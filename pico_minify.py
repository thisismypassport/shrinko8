from utils import *
from pico_defs import fixnum_is_negative
from pico_tokenize import TokenType
from pico_tokenize import StopTraverse, k_skip_children
from pico_parse import Node, NodeType, VarKind
from pico_parse import k_unary_ops_prec, get_precedence, is_right_assoc, can_replace_with_unary
from pico_parse import is_vararg_expr, is_short_block_stmt, is_global_or_builtin_local
from pico_output import format_fixnum, format_string_literal
from pico_output import output_min_wspace, output_original_wspace

class Focus(Bitmask):
    chars = compressed = tokens = ...
    none = 0

def minify_string_literal(ctxt, token, focus, value=None):
    if value is None:
        value = token.string_value
    
    if focus.chars:
        return format_string_literal(value, use_complex_long=ctxt.version >= 40)
    else:
        # haven't found a good balanced heuristic for 'long' yet
        return format_string_literal(value, long=token.value.startswith('['))

def minify_needs_comments(minify):
    # returns whether minify_code makes use of the tokens' comments
    return not minify.get("wspace", True)
    
def get_node_bodies(node):
    if node.type in (NodeType.if_, NodeType.elseif):
        yield node.then
        if node.else_:
            yield from get_node_bodies(node.else_)
    else:
        yield node.body

def analyze_code_for_minify(root, focus):
    shorts = CounterDictionary()
    longs = CounterDictionary()
    shortenables = set()

    def analyze_node_post(node):

        if node.type in (NodeType.if_, NodeType.while_):
            is_short = node.short

            weight = 1
            if node.type == NodeType.if_:
                else_ = node.else_
                while else_ and else_.type == NodeType.elseif:
                    weight += 1
                    else_ = else_.else_
            has_elseif = weight > 1

            # can the node be converted to shorthand?
            if not is_short and not has_elseif:
                has_shorthand, has_empties, starts_with_do = False, False, False

                def check_shorthand(node):
                    nonlocal has_shorthand
                    # ideally, could allow last node in an 'if' to be a print...
                    if node.short or node in shortenables:
                        has_shorthand = True
                    
                # first check the parents
                node.traverse_parents(check_shorthand)
                
                # now check the children
                for i, body in enumerate(get_node_bodies(node)):
                    body.traverse_nodes(post=check_shorthand)
                    if not body.children:
                        has_empties = True
                    
                    if i == 0:
                        # beware of do block ambiguity
                        starts_with_do = body.first_token().value == "do"
                
                # empty bodies require extra ';'s to shorten, which worsens compression
                is_short = not has_shorthand and not (has_empties and not focus.chars) and not starts_with_do
                if is_short:
                    shortenables.add(node)
            
            if is_short:
                shorts[node.type] += weight
            else:
                longs[node.type] += weight

    root.traverse_nodes(post=analyze_node_post)

    new_shorts = {}
    for type in (NodeType.if_, NodeType.while_):
        # if everything can be made short, that's always best.
        # else, consistency is better for compression while more shorts are better for chars
        if focus.chars or not longs[type] or (not focus.compressed and longs[type] * 1.5 <= shorts[type]):
            new_shorts[type] = True
        elif focus.compressed:
            new_shorts[type] = False
        else:
            new_shorts[type] = None # leave alone

    return Dynamic(new_shorts=new_shorts, shortenables=shortenables)

def minify_change_shorthand(node, new_short):
    if new_short:
        node.short = True
        node.remove_token(2, ("then", "do"))
        if node.type == NodeType.if_ and node.else_:
            node.else_.short = True
            node.else_.remove_token(-1, "end")
        else:
            node.remove_token(-1, "end")
        
        # we can assume node.cond is not wrapped in parens, since we're in a post-visit
        # wrap it in parens ourselves (TODO: eww...)
        node.cond.replace_with(Node(NodeType.group, [], child=node.cond.move()))
        node.cond.children.append(node.cond.child)
        node.cond.insert_token(0, TokenType.punct, "(", near_next=True)
        node.cond.append_token(TokenType.punct, ")")

        # fixup empty bodies
        for body in get_node_bodies(node):
            if not body.children:
                body.append_token(TokenType.punct, ";")
        
        # remove line breaks originally in the source
        vline = node.first_token().vline
        def fix_vlines(token):
            token.vline = vline
        node.traverse_tokens(fix_vlines)

    else:
        node.short = False
        node.insert_token(2, TokenType.keyword, "then" if node.type == NodeType.if_ else "do")
        if node.type == NodeType.if_ and node.else_:
            node.else_.short = False
            node.else_.append_token(TokenType.keyword, "end", near_next=True)
        else:
            node.append_token(TokenType.keyword, "end", near_next=True)

def node_contains_vars(root, vars):
    def visitor(node):
        if node.type == NodeType.var and node.var in vars:
            raise StopTraverse()

    try:
        root.traverse_nodes(visitor, extra=True)
        return False
    except StopTraverse:
        return True

def expr_is_trivial(root, ctxt, safe_only, allow_member=True, allow_index=True, allow_call=True):
    def visitor(expr):
        # nodes that cannot call user-defined code in any case
        if expr.type in (NodeType.const, NodeType.varargs, NodeType.group,
                         NodeType.table, NodeType.table_member, NodeType.table_index): # (since new tables have no metatable)
            pass
        elif expr.type == NodeType.var and expr.kind != VarKind.global_:
            pass
        elif expr.type == NodeType.unary_op and expr.op == "not":
            pass
        elif expr.type == NodeType.binary_op and expr.op in ("and", "or"):
            pass
        elif expr.type == NodeType.function:
            assert not expr.target # we only traverse expressions!
            return k_skip_children
        # nodes that may call user-defined code
        elif expr.type == NodeType.call:
            func = expr.func
            if safe_only or not allow_call or \
                    not (func.type == NodeType.var and is_global_or_builtin_local(func) and not func.var.reassigned and func.name not in ctxt.callback_builtins):
                raise StopTraverse()
        elif expr.type == NodeType.member and not allow_member:
            raise StopTraverse()
        elif expr.type == NodeType.index and not allow_index:
            raise StopTraverse()
        # nodes that may call user-defined code via metatables (E.g. member access, operators)
        elif safe_only:
            raise StopTraverse()
    
    try:
        root.traverse_nodes(visitor)
        return True
    except StopTraverse:
        return False

def minify_merge_assignments(prev, next, ctxt, safe_only):
    if len(prev.targets) < len(prev.sources):
        return
    if len(prev.targets) > len(prev.sources) and \
            ((prev.sources and is_vararg_expr(prev.sources[-1])) or (next.sources and is_vararg_expr(next.sources[-1])) or len(next.targets) < len(next.sources)):
        return
    
    merge_prev = getattr(next.first_token(), "merge_prev", None)
    if merge_prev is False:
        return
    
    # check if prev's targets are used in next's sources or targets

    require_trivial = False # True when prev.targets may be accessed indirectly from functions that may be called by next.soources
    allow_index = allow_member = True
    target_vars = []
    for target in prev.targets:
        if target.type == NodeType.var:
            target_vars.append(target.var)
            # is it possible for 'next' to access 'target' without refering to it directly? (via function call)
            if target.kind == VarKind.global_ or (prev.type == NodeType.assign and target.var.captured):
                require_trivial = True
        elif target.type == NodeType.member:
            target_vars.append(target.key.var)
            require_trivial = True
            allow_index = False # TODO: could rely on rename's preserve logic
        elif target.type == NodeType.index:
            require_trivial = True
            allow_member = False # TODO: could rely on rename's preserve logic
            allow_index = False
        else: # just in case...
            return
    
    for node in next.sources:
        if target_vars and node_contains_vars(node, target_vars):
            return
        if require_trivial and not expr_is_trivial(node, ctxt, safe_only, allow_member, allow_index):
            return
        
    for node in next.targets:
        if target_vars and node_contains_vars(node, target_vars):
            return
        if require_trivial and not expr_is_trivial(node, ctxt, safe_only, allow_member, allow_index, allow_call=False):
            return
    
    # when reordering local declarations, ensure we don't change which local wins out among identically-named locals
    # (this relies on rename being done already!)
        
    if len(prev.targets) > len(prev.sources) and prev.type == NodeType.local:
        for target in prev.targets[len(prev.sources):]:
            for next_target in next.targets:
                if target.name == next_target.name:
                    return
    
    # do the merge: (TODO: eww...)

    def insert_array_items(dst_node, dst_arr, dst_arr_i, src_arr, src_arr_i, count):
        count = default(count, len(src_arr) - src_arr_i)        
        if not count:
            return

        need_end_comma = False
        if dst_arr_i < len(dst_arr):
            dst_i = dst_node.children.index(dst_arr[dst_arr_i])
            need_end_comma = True
        elif len(dst_arr):
            dst_i = dst_node.children.index(dst_arr[dst_arr_i - 1]) + 1
            dst_node.insert_token(dst_i, TokenType.punct, ",")
            dst_i += 1
        else:
            assert dst_arr is dst_node.sources
            dst_node.append_token(TokenType.punct, "=")
            dst_i = len(dst_node.children)

        for i in range(count):
            src_elem = src_arr[src_arr_i + i]
            dst_arr.insert(dst_arr_i + i, src_elem)

            dst_node.insert_existing(dst_i, src_elem)
            dst_i += 1
            
            if i < count - 1 or need_end_comma:
                dst_node.insert_token(dst_i, TokenType.punct, ",")
                dst_i += 1

    insert_array_items(prev, prev.targets, len(prev.sources), next.targets, 0, None)
    insert_array_items(prev, prev.sources, len(prev.sources), next.sources, 0, None)

    next.erase()

def minify_code(ctxt, root, minify_opts):
    safe_reorder = minify_opts.get("safe-reorder", False)
    minify_lines = minify_opts.get("lines", True)
    minify_wspace = minify_opts.get("wspace", True)
    minify_tokens = minify_opts.get("tokens", True)
    minify_comments = minify_opts.get("comments", True)
    minify_reorder = minify_opts.get("reorder", True)
    focus = Focus(minify_opts.get("focus"))

    if not focus.tokens:
        safe_reorder = True # nothing gained with False here, so set it to True just in case.

    analysis = analyze_code_for_minify(root, focus)

    def fixup_nodes_pre(node):
        if minify_tokens:
            # remove shorthands

            if node.type in (NodeType.if_, NodeType.while_) and node.short and (analysis.new_shorts[node.type] == False):
                minify_change_shorthand(node, False)
                
            # remove unneeded groups

            while node.type == NodeType.group:
                inner, outer = node.child, node.parent
                inner_prec, outer_prec = get_precedence(inner), get_precedence(outer)
                needed = True
                if e(inner_prec) and e(outer_prec) and (inner_prec > outer_prec or (inner_prec == outer_prec and
                        (outer_prec == k_unary_ops_prec or is_right_assoc(outer) == (outer.right == node)))):
                    needed = False
                elif e(outer_prec) and inner.type in (NodeType.var, NodeType.index, NodeType.member, NodeType.call, NodeType.varargs):
                    needed = False
                elif e(outer_prec) and inner.type == NodeType.const and (focus.tokens or can_replace_with_unary(node) or
                        not (inner.token.type == TokenType.number and fixnum_is_negative(inner.token.fixnum_value))):
                    needed = False
                elif outer.type in (NodeType.group, NodeType.table_member, NodeType.table_index, NodeType.op_assign):
                    needed = False
                elif outer.type == NodeType.call and (node in outer.args[:-1] or 
                        (outer.args and node == outer.args[-1] and not is_vararg_expr(inner))):
                    needed = False
                elif outer.type in (NodeType.assign, NodeType.local) and (node in outer.sources[:-1] or 
                        (outer.sources and node == outer.sources[-1] and (not is_vararg_expr(inner) or len(outer.targets) <= len(outer.sources)))):
                    needed = False
                elif outer.type in (NodeType.return_, NodeType.table) and (node in outer.items[:-1] or
                        (outer.items and node == outer.items[-1] and not is_vararg_expr(inner))):
                    needed = False
                elif outer.type in (NodeType.if_, NodeType.elseif, NodeType.while_, NodeType.until) and not outer.short:
                    needed = False
                
                if needed:
                    break
                else:
                    node.replace_with(node.child.move())
                    # node may now be another group, so loop
        
    def fixup_nodes_post(node):
        if minify_tokens:
            # create shorthands
            
            if node.type in (NodeType.if_, NodeType.while_) and not node.short and \
               (analysis.new_shorts[node.type] == True) and node in analysis.shortenables:
                minify_change_shorthand(node, True)

        if minify_reorder:
            # merge assignments

            if node.type == NodeType.local or (focus.tokens and node.type == NodeType.assign):
                prev = node.prev_sibling()
                while prev and prev.type == None: # skip erased
                    prev = prev.prev_sibling()
                if prev and prev.type == node.type:
                    minify_merge_assignments(prev, node, ctxt, safe_reorder)

    def fixup_tokens(token):

        # minify sublangs

        sublang = getattr(token, "sublang", None)
        if sublang and sublang.minify:
            token.modify(minify_string_literal(ctxt, token, focus, value=sublang.minify()))

        if minify_tokens:
            
            # remove unneeded tokens

            if token.value == ";" and token.parent.type == NodeType.block and token.next_token().value != "(":
                gparent = token.parent.parent
                if not (gparent and is_short_block_stmt(gparent) and not token.parent.stmts):
                    token.erase()
                    return

            if token.value in (",", ";") and token.parent.type == NodeType.table and token.next_sibling().value == "}":
                token.erase()
                return

            if token.value == "(" and token.parent.type == NodeType.call and len(token.parent.args) == 1:
                arg = token.parent.args[0]
                if arg.type == NodeType.table or (arg.type == NodeType.const and arg.token.type == TokenType.string):
                    token.erase("(")
                    token.parent.erase_token(-1, ")")
                    return

            # replace tokens for higher consistency

            if token.value == ";" and token.parent.type == NodeType.table:
                token.modify(",")

            if token.value == "!=":
                token.modify("~=")
             
            if token.value == "^^" and ctxt.version >= 37:
                token.modify("~")

            if token.type == TokenType.string:
                token.modify(minify_string_literal(ctxt, token, focus))

            if token.type == TokenType.number:
                allow_unary = can_replace_with_unary(token.parent)
                token.modify(format_fixnum(token.fixnum_value, sign=None if allow_unary else ''))
        
        if token.type == TokenType.number:
            if token.value.startswith("-") or token.value.startswith("~"): # either due to format_fixnum above, or due to ConstToken.value
                # insert synthetic unary token, so that output_tokens's tokenize and root.get_tokens() won't get confused
                token.parent.insert_token(0, TokenType.punct, token.value[0], near_next=True)
                token.modify(token.value[1:])

    root.traverse_nodes(fixup_nodes_pre, fixup_nodes_post, tokens=fixup_tokens)

    if minify_wspace:
        return output_min_wspace(root, minify_lines)
    else:
        return output_original_wspace(root, minify_comments)
