from utils import *
from pico_defs import from_pico_chars
from pico_tokenize import TokenType, is_identifier, tokenize, Token, keywords, k_char_escapes
from pico_tokenize import parse_string_literal, parse_fixnum
from pico_parse import VarKind, NodeType, Local
from pico_parse import k_unary_ops_prec, k_binary_op_precs, k_right_binary_ops

global_callbacks = {
    "_init", "_draw", "_update", "_update60",
}

member_strings = {
    "n",
    "__index", "__newindex", "__len", "__eq", "__lt", "__le",
    "__add", "__sub", "__mul", "__div", "__idiv", "__mod",
    "__pow", "__and", "__or", "__xor", "__shl", "__shr",
    "__lshr", "__rotl", "__rotr", "__concat", "__unm", "__not",
    "__peek", "__peek2", "__peek4", "__call", "__tostring",
    "__pairs", "__ipairs", "__metatable", "__gc", "__mode",
}

def obfuscate_tokens(ctxt, root, obfuscate):
    all_globals = ctxt.globals.copy()
    global_knowns = global_callbacks.copy()
    member_knowns = member_strings.copy()
    known_tables = set()
    preserve_members = False
    members_as_globals = False

    if isinstance(obfuscate, dict):
        members_as_globals = obfuscate.get("members=globals", False)
        rules_input = obfuscate.get("rules")
        if rules_input:
            for key, value in rules_input.items():
                if value == False:
                    if key == "*.*":
                        preserve_members = True
                    elif key.endswith(".*"):
                        known_tables.add(key[:-2])
                    elif key.startswith("*."):
                        member_knowns.add(key[2:])
                    else:
                        global_knowns.add(key)
                elif value == True:
                    if key == "*.*":
                        preserve_members = False
                    elif key.endswith(".*"):
                        known_tables.discard(key[:-2])
                    elif key.startswith("*."):
                        member_knowns.discard(key[2:])
                    else:
                        all_globals.discard(key)
                        global_knowns.discard(key)
                else:
                    fail(value)

    # collect char histogram

    char_uses = CounterDictionary()
    def collect_chars(token):
        if token.type != TokenType.ident and not token.fake:
            sublang = getattr(token, "sublang", None)
            if sublang and sublang.get_unminified_chars:
                for ch in sublang.get_unminified_chars():
                    char_uses[ch] += 1
            else:
                for ch in token.value:
                    char_uses[ch] += 1

    root.traverse_tokens(collect_chars)

    k_identifier_chars = string.ascii_letters + string.digits + "_"
    
    ident_chars = []
    for ch in sorted(char_uses, key=lambda k: char_uses[k], reverse=True):
        if ch in k_identifier_chars:
            ident_chars.append(ch)
    
    for ch in k_identifier_chars:
        if ch not in ident_chars:
            ident_chars.append(ch)

    ident_char_order_map = {ch1: ch2 for ch1, ch2 in zip(ident_chars, ident_chars[1:])}

    # collect ident uses

    global_uses = CounterDictionary()
    member_uses = CounterDictionary()
    local_uses = CounterDictionary()
    scopes = []

    def compute_effective_kind(node, kind, explicit):
        if kind == VarKind.member:
            table_name = None
            
            if node.parent.type == NodeType.member and node.parent.key == node and node.parent.child.type == NodeType.var:
                var_node = node.parent.child
                table_name = var_node.name

                if not explicit and var_node.var and var_node.var.keys_kind != None:
                    return compute_effective_kind(node, var_node.var.keys_kind, explicit=True)

            elif not explicit and node.parent.type == NodeType.table_member and node.parent.key == node:
                table_node = node.parent.parent
                if table_node.keys_kind != None:
                    return compute_effective_kind(node, table_node.keys_kind, explicit=True)

                if table_node.parent.type in (NodeType.assign, NodeType.local) and table_node in table_node.parent.sources:
                    assign_i = table_node.parent.sources.index(table_node)
                    target_node = list_get(table_node.parent.targets, assign_i)
                    if target_node and target_node.type == NodeType.var and target_node.var and target_node.var.keys_kind != None:
                        return compute_effective_kind(node, target_node.var.keys_kind, explicit=True)
            
            if preserve_members:
                return None
            elif node.name in member_knowns:
                return None
            elif table_name in known_tables:
                return None
            elif table_name == "_ENV":
                return compute_effective_kind(node, VarKind.global_, explicit=True)
            
            if members_as_globals:
                kind = VarKind.global_

        elif kind == VarKind.global_:
            if not explicit:
                env_var = node.parent_scope.find("_ENV")
                if env_var and env_var.keys_kind != None:
                    return compute_effective_kind(node, env_var.keys_kind, explicit=True)

            if node.name in global_knowns:
                return None
            elif node.name in all_globals:
                global_knowns.add(node.name)
                return None

        elif kind == VarKind.local:
            if node.var.implicit:
                return None
            elif node.name == "_ENV": # e.g. new locals named it
                return None

        return kind

    def collect_idents_pre(node):
        scope = node.start_scope
        if e(scope):
            scope.used_globals = set()
            scope.used_locals = set()
            scopes.append(scope)
            
        if node.type == NodeType.var:
            node.effective_kind = compute_effective_kind(node, default(node.var_kind, node.kind), explicit=e(node.var_kind))
            
            if node.effective_kind == VarKind.member:
                member_uses[node.name] += 1

            elif node.effective_kind == VarKind.global_:
                global_uses[node.name] += 1

            elif node.effective_kind == VarKind.local:
                # should in theory help, but doesn't...
                #if node.new:
                #    local_uses[node.var] += 0
                #else:
                local_uses[node.var] += 1
                    
            # add to the scope based on real kind, to avoid conflicts (e.g. between builtins and globals)
            if node.kind == VarKind.global_:
                for scope in scopes:
                    scope.used_globals.add(node.name)

            elif node.kind == VarKind.local:
                if node.var.scope in scopes:
                    i = scopes.index(node.var.scope)
                    for scope in scopes[i:]:
                        scope.used_locals.add(node.var)
                        
        elif node.type == NodeType.sublang:
            # slight dup of compute_effective_kind logic

            for name, count in node.lang.get_global_usages().items():
                if name not in global_knowns and is_identifier(name):
                    if name in all_globals:
                        global_knowns.add(name)
                    else:
                        global_uses[name] += count

            for name, count in node.lang.get_member_usages().items():
                if name not in member_knowns and is_identifier(name):
                    member_uses[name] += count

            for var, count in node.lang.get_local_usages().items():
                if not var.implicit:
                    local_uses[var] += count

    def collect_idents_post(node):
        for scope in node.end_scopes:
            assert scopes.pop() == scope

    root.traverse_nodes(collect_idents_pre, collect_idents_post, extra=True)

    # assign idents

    def get_next_ident_char(ch, first):
        nextch = ident_char_order_map.get(ch) if ch else ident_chars[0]
        while first and nextch and (nextch.isdigit() or nextch == '_'): # note: we avoid leading underscores too
            nextch = ident_char_order_map.get(nextch)
        if nextch:
            return nextch, True
        else:
            return ident_chars[0], False

    def create_ident_stream():
        next_ident = ""

        def get_next_ident():
            nonlocal next_ident
            for i in range(len(next_ident)-1, -1, -1):
                next_ch, found = get_next_ident_char(next_ident[i], i==0)
                next_ident = str_replace_at(next_ident, i, 1, next_ch)
                if found:
                    break
            else:
                next_ident = str_insert(next_ident, 0, get_next_ident_char(None, True)[0])
            return next_ident

        return get_next_ident

    def assign_idents(uses, excludes, skip=0):
        ident_stream = create_ident_stream()
        rename_map = {}

        for i in range(skip):
            ident_stream()

        for value in sorted(uses, key=lambda k: uses[k], reverse=True):
            while True:
                ident = ident_stream()
                if ident not in excludes and ident not in keywords:
                    break

            rename_map[value] = ident

        return rename_map

    member_renames = assign_idents(member_uses, member_knowns)
    global_renames = assign_idents(global_uses, global_knowns)
    rev_global_renames = {v: k for k, v in global_renames.items()}
    
    local_ident_stream = create_ident_stream()
    local_renames = {}

    remaining_local_uses = list(sorted(local_uses, key=lambda k: local_uses[k], reverse=True))
    while remaining_local_uses:
        ident = local_ident_stream()
        ident_global = rev_global_renames.get(ident)
        if not ident_global and ident in global_knowns:
            ident_global = ident
        ident_locals = []
        
        for i, var in enumerate(remaining_local_uses):
            if ident_global in var.scope.used_globals:
                continue
            
            for _, ident_local in ident_locals:
                if ident_local in var.scope.used_locals:
                    break
                if var in ident_local.scope.used_locals:
                    break

            else:
                local_renames[var] = ident
                ident_locals.append((i, var))

        for i, ident_local in reversed(ident_locals):
            assert remaining_local_uses.pop(i) == ident_local

    # output

    def update_srcmap(mapping, kind):
        for old, new in mapping.items():
            old_name = old.name if isinstance(old, Local) else old

            ctxt.srcmap.append("%s %s <- %s" % (kind, from_pico_chars(new), old_name))

    if e(ctxt.srcmap):
        update_srcmap(member_renames, "member")
        update_srcmap(global_renames, "global")
        update_srcmap(local_renames, "local")

    def update_idents(node):
        if node.type == NodeType.var:
            orig_name = node.name

            if node.effective_kind == VarKind.member:
                node.name = member_renames[node.name]
            elif node.effective_kind == VarKind.global_:
                node.name = global_renames[node.name]
            elif node.effective_kind == VarKind.local:
                node.name = local_renames[node.var]
            else:
                return

            if node.parent.type == NodeType.const: # const string interpreted as identifier case
                assert len(node.parent.children) == 1 and node.parent.extra_names[node.extra_i] == orig_name
                node.parent.extra_names[node.extra_i] = node.name
                node.parent.children[0].value = '"%s"' % ",".join(node.parent.extra_names)
            else:
                assert len(node.children) == 1 and node.children[0].value == orig_name
                node.children[0].value = node.name
                node.children[0].modified = True
                
        elif node.type == NodeType.sublang:
            node.lang.rename(globals=global_renames, members=member_renames, locals=local_renames)
            
    root.traverse_nodes(update_idents, extra=True)

def from_fixnum(value):
    neg = value & 0x80000000
    if neg:
        value = (-value) & 0xffffffff
    if value & 0xffff:
        value /= (1 << 16)
    else:
        value >>= 16
    return -value if neg else value

# essentially only returns decvalue right now, given mostly non-fract. inputs
# TODO: test with fract-ish inputs to see what's best to do.
def format_fixnum(value, allow_minus=False):
    intvalue = value >> 16
    dotvalue = value & 0xffff

    hexvalue = "0x%x" % intvalue
    if dotvalue:
        hexvalue = "0x" if hexvalue == "0x0" else hexvalue
        hexvalue += (".%04x" % dotvalue).rstrip('0')
        
    def str_add_1(str):
        if not str:
            return "1"
        elif str[-1] == ".":
            return str_add_1(str[:-1]) + "."
        elif str[-1] == "9":
            return str_add_1(str[:-1]) + "0"
        else:
            return str[:-1] + chr(ord(str[-1]) + 1)
    
    numvalue = value / (1 << 16)
    decvalue = "%.10f" % numvalue
    while "." in decvalue:
        nextvalue = decvalue[:-1]
        nextupvalue = str_add_1(nextvalue)
        if parse_fixnum(nextvalue) == value:
            decvalue = nextvalue
        elif parse_fixnum(nextupvalue) == value:
            decvalue = nextupvalue
        else:
            break
    if decvalue.startswith("0."):
        decvalue = decvalue[1:]

    minvalue = hexvalue if len(hexvalue) < len(decvalue) else decvalue

    if allow_minus and value & 0x80000000 and value != 0x80000000:
        negvalue = "-" + format_fixnum(-value & 0xffffffff)
        if len(negvalue) < len(minvalue):
            minvalue = negvalue

    return minvalue

k_char_escapes_rev = {v: k for k, v in k_char_escapes.items() if k != '\n'}
k_char_escapes_rev.update({"\0": "0", "\x0e": "14", "\x0f": "15"})

k_char_escapes_rev_min = {k: v for k, v in k_char_escapes_rev.items() if k in "\0\n\r\"'\\"}

def format_string_literal(value, use_ctrl_chars=True, long=False):
    # currently, I'm unable to find a better-than-nothing heuristic for long strings's compression size
    # if len(strlit) > len(value) + len(long_prefix) + 4 and ...
    if long and "\0" not in value and "\r" not in value and "]]" not in value:
        long_prefix = "\n" if value.startswith("\n") else ""
        # note: we never generate [=[]=] and the like, as pico doesn't like it much
        return "[[%s%s]]" % (long_prefix, value)

    char_escapes_rev = k_char_escapes_rev_min if use_ctrl_chars else k_char_escapes_rev
    if value.count('"') <= value.count("'"):
        opener = closer = '"'
        exclude_esc = "'"
    else:
        opener = closer = "'"
        exclude_esc = '"'

    litparts = []
    for i, ch in enumerate(value):
        if ch in char_escapes_rev and ch != exclude_esc:
            esc = char_escapes_rev[ch]
            if esc.isdigit() and i + 1 < len(value) and value[i + 1].isdigit():
                esc = esc.rjust(3, '0')
            litparts.append("\\" + esc)
        else:
            litparts.append(ch)

    return '%s%s%s' % (opener, "".join(litparts), closer)

def get_precedence(node):
    if node.type == NodeType.binary_op:
        return k_binary_op_precs[node.op]
    elif node.type == NodeType.unary_op:
        return k_unary_ops_prec

def is_right_assoc(node):
    if node.type == NodeType.binary_op:
        return node.op in k_right_binary_ops
    else:
        return False

def is_vararg_expr(node):
    return node.type in (NodeType.call, NodeType.varargs)
    
def minify_code(source, tokens, root, minify):

    minify_lines = minify_wspace = minify_tokens = minify_comments = True
    if isinstance(minify, dict):
        minify_lines = minify.get("lines", True)
        minify_wspace = minify.get("wspace", True)
        minify_tokens = minify.get("tokens", True)
        minify_comments = minify.get("comments", True)

    vlines = defaultdict(set)

    def remove_parens(token):
        token.value = None
        end_token = token.parent.children[-1]
        assert end_token.value == ")"
        end_token.value = None

    def fixup_tokens(token):
        # update vline data

        if token.value in ("if", "then", "while", "do", "?"):
            vlines[token.vline].add(token.value)
    
        sublang = getattr(token, "sublang", None)
        if sublang and sublang.minify:
            token.value = format_string_literal(sublang.minify(), long=token.value.startswith('['))

        if minify_tokens:
            
            # remove unneeded tokens

            if token.value == ";" and token.parent.type == NodeType.block and token.next_token().value != "(":
                if not (getattr(token.parent.parent, "short", False) and not token.parent.stmts):
                    token.value = None
                    return

            if token.value in (",", ";") and token.parent.type == NodeType.table and token.next_sibling().value == "}":
                token.value = None
                return

            if token.value == "(" and token.parent.type == NodeType.call and len(token.parent.args) == 1:
                arg = token.parent.args[0]
                if arg.type == NodeType.table or (arg.type == NodeType.const and arg.token.type == TokenType.string):
                    return remove_parens(token)

            if token.value == "(" and token.parent.type == NodeType.group:
                inner, outer = token.parent.child, token.parent.parent
                inner_prec, outer_prec = get_precedence(inner), get_precedence(outer)
                if e(inner_prec) and e(outer_prec) and (inner_prec > outer_prec or (inner_prec == outer_prec and
                        (outer_prec == k_unary_ops_prec or is_right_assoc(outer) == (outer.right == token.parent)))):
                    return remove_parens(token)
                if outer.type in (NodeType.group, NodeType.table_member, NodeType.table_index, NodeType.op_assign):
                    return remove_parens(token)
                if outer.type in (NodeType.call, NodeType.print) and (token.parent in outer.args[:-1] or 
                        (outer.args and token.parent == outer.args[-1] and not is_vararg_expr(inner))):
                    return remove_parens(token)
                if outer.type in (NodeType.assign, NodeType.local) and (token.parent in outer.sources[:-1] or 
                        (outer.sources and token.parent == outer.sources[-1] and (not is_vararg_expr(inner) or len(outer.targets) <= len(outer.sources)))):
                    return remove_parens(token)
                if outer.type in (NodeType.return_, NodeType.table) and (token.parent in outer.items[:-1] or
                        (outer.items and token.parent == outer.items[-1] and not is_vararg_expr(inner))):
                    return remove_parens(token)
                if outer.type in (NodeType.if_, NodeType.elseif, NodeType.while_, NodeType.until) and not getattr(outer, "short", False):
                    return remove_parens(token)

            # replace tokens for higher consistency

            if token.value == ";" and token.parent.type == NodeType.table:
                token.value = ","

            if token.value == "!=":
                token.value = "~="
             
            #TODO: enable this in a few weeks.
            #if token.value == "^^":
            #    token.value = "~"

            if token.type == TokenType.string:
                token.value = format_string_literal(parse_string_literal(token.value), long=token.value.startswith('['))

            if token.type == TokenType.number:
                outer_prec = get_precedence(token.parent.parent) if token.parent.type == NodeType.const else None
                allow_minus = outer_prec is None or outer_prec < k_unary_ops_prec
                token.value = format_fixnum(parse_fixnum(token.value), allow_minus=allow_minus)
                if token.value.startswith("-"):
                    # insert synthetic minus token, so that output_tokens's tokenize won't get confused
                    token.value = token.value[1:]
                    minus_token = Token.synthetic(TokenType.punct, "-", token, prepend=True)
                    token.parent.children.insert(0, minus_token)
                    tokens.insert(tokens.index(token), minus_token)

    root.traverse_tokens(fixup_tokens)

    output = []

    if minify_wspace:
        # add keep: comments (for simplicity, at start)
        for token in tokens:
            if token.type == TokenType.comment:
                output.append("--%s\n" % token.value)

        def has_shorthands(vline):
            data = vlines[vline]
            return ("if" in data and "then" not in data) or ("while" in data and "do" not in data) or ("?" in data)

        prev_token = Token.dummy(None)
        def output_tokens(token):
            nonlocal prev_token
            if token.value is None:
                return

            # (modified tokens may require whitespace not previously required - e.g. 0b/0x)
            if (prev_token.endidx < token.idx or prev_token.modified or token.modified) and prev_token.value:

                # note: always adding \n before if/while wins a few bytes on my code (though similar tactics for other keywords and spaces don't work?)
                if prev_token.vline != token.vline and (not minify_lines or has_shorthands(prev_token.vline) or has_shorthands(token.vline)):
                    output.append("\n")
                    
                else:
                    combined = prev_token.value + token.value
                    ct, ce = tokenize(PicoSource(None, combined))
                    if ce or len(ct) != 2 or (ct[0].type, ct[0].value, ct[1].type, ct[1].value) != (prev_token.type, prev_token.value, token.type, token.value):
                        output.append(" ")

            output.append(token.value)
            prev_token = token

        root.traverse_tokens(output_tokens)

    else:
        # just remove the comments (if needed), with minimal impact on visible whitespace
        prev_token = Token.dummy(None)

        def output_wspace(wspace):
            if minify_comments:
                i = 0
                pre_i, post_i = 0, 0
                while True:
                    next_i = wspace.find("--", i) # in theory should support //
                    if next_i < 0:
                        post_i = i
                        break
                    
                    if pre_i == 0:
                        pre_i = next_i

                    # TODO: --[[]]/etc comments...
                    i = wspace.find("\n", next_i)
                    i = i if i >= 0 else len(wspace)

                result = wspace[:pre_i] + wspace[post_i:]
                if post_i > 0 and not result:
                    result = " "
                output.append(result)
            else:
                output.append(wspace)

        for token in tokens:
            if token.type == TokenType.lint:
                continue

            output_wspace(source.text[prev_token.endidx:token.idx])

            if token.type == TokenType.comment:
                output.append("--%s\n" % token.value)
            elif token.value != None:
                output.append(token.value)
                
            prev_token = token

        output_wspace(source.text[prev_token.endidx:])

    return "".join(output), tokens

from pico_process import PicoSource
