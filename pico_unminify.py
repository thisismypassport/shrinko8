from utils import *
from pico_defs import Language
from pico_tokenize import TokenType, Token
from pico_output import format_num, format_string_literal
from pico_parse import NodeType, Node, VarKind, is_function_stmt, is_short_block_stmt

k_unary_to_func = {
    "@": ("peek", None),
    "%": ("peek2", None),
    "$": ("peek4", None),
    "*": ("peek8", None),
    "~": {Language.pico8: ("bnot", None)},
}

k_binary_to_func = {
    "&": {Language.pico8: ("band", None)},
    "|": {Language.pico8: ("bor", None)},
    "^^": {Language.pico8: ("bxor", None), Language.picotron: (None, "~")},
    "~": {Language.pico8: ("bxor", None)},
    "<<": {Language.pico8: ("shl", None)},
    ">>": {Language.pico8: ("shr", None)},
    ">>>": {Language.pico8: ("lshr", None)},
    "<<>": {Language.pico8: ("rotl", None)},
    ">><": {Language.pico8: ("rotr", None)},
    "\\": {Language.pico8: ("flr", "/"), Language.picotron: (None, "//")},
    "!=": (None, "~="),
}

def unminify_code(ctxt, root, unminify_opts):
    indent_str = unminify_opts.get("indent", 2)
    plain_lua = unminify_opts.get("lua")

    output = []
    prev_token = Token.none
    prev_tight = False
    indent = 0
    curr_stmt = None
    stmt_stack = []
    used_locals = set() # HACK - really should have a way to get scope from any node...

    k_tight_prefix_tokens = ("(", "[", "{", "?", ".", ":", "::")
    k_tight_suffix_tokens = (")", "]", "}", ",", ";", ".", ":", "::")

    def visit_token(token):
        nonlocal prev_token, prev_tight
        value = token.value

        for comment in token.children:
            comment_value = comment.value

            # (lua) c-style comments -> lua comments
            if plain_lua and comment_value.startswith("//"):
                comment_value = "--" + comment_value[2:]

            # check if spaces or linebreaks/indents would be good
            if "\n" in comment_value:
                if prev_tight:
                    output.append("\n")
                    output.append(indent_str * indent)
                output.append(comment_value)
                if not comment_value.endswith("\n"):
                    output.append("\n")
                output.append(indent_str * indent)
            else:
                if prev_tight and prev_token.value not in k_tight_prefix_tokens:
                    output.append(" ")
                output.append(comment_value)
            prev_tight = False

        if token.value is None:
            return

        # ignore shorthand parens, to avoid increasing token count as we convert shorthands to longhand
        gparent = token.parent.parent
        if gparent and is_short_block_stmt(gparent) and token.parent == gparent.cond and token.value in ("(", ")"):
            return
        
        # ignore semicolons inside blocks - our formatting makes them unneeded
        if token.parent.type == NodeType.block and token.value == ";":
            return
        
        # undo ugly token replacements
        if token.value == "do" and token.parent.type in (NodeType.if_, NodeType.elseif):
            value = "then"

        # check if a space is needed
        if prev_tight and prev_token.value not in k_tight_prefix_tokens and \
                token.value not in k_tight_suffix_tokens and \
                not (token.value in ("(", "[") and (prev_token.type == TokenType.ident or 
                                                    prev_token.value in ("function", ")", "]", "}"))) and \
                not (prev_token.type == TokenType.punct and prev_token.parent.type == NodeType.unary_op):
            output.append(" ")

        output.append(value)
        prev_token = token
        prev_tight = True

    def replace_op_with_call(node, op_map, left_i, right_i):
        op_info = op_map.get(node.op)
        if op_info and isinstance(op_info, dict):
            op_info = op_info.get(ctxt.lang)
        if op_info:
            func, op = op_info

            new_children = []
            if func:
                if func in used_locals:
                    new_children.append(Token.synthetic(TokenType.ident, "_ENV", node, prepend=True))
                    new_children.append(Token.synthetic(TokenType.punct, ".", node, prepend=True))
                new_children.append(Token.synthetic(TokenType.ident, func, node, prepend=True))
                new_children.append(Token.synthetic(TokenType.punct, "(", node, prepend=True))
            if left_i != None:
                new_children.append(node.children[left_i])
            if op:
                new_children.append(Token.synthetic(TokenType.punct, op, node, prepend=True))
            elif left_i != None:
                new_children.append(Token.synthetic(TokenType.punct, ",", node, prepend=True))
            if right_i != None:
                new_children.append(node.children[right_i])
            if func:
                new_children.append(Token.synthetic(TokenType.punct, ")", node, prepend=True))
            
            node.replace_with(Node(NodeType.custom, new_children))

    def visit_node(node):
        nonlocal indent, curr_stmt, prev_tight

        if node.type == NodeType.block:
            if node.parent:
                indent += 1
                # shorthand -> longhand
                if is_short_block_stmt(node.parent) and node.parent.type != NodeType.else_:
                    output.append(" then" if node.parent.type == NodeType.if_ else " do")

            stmt_stack.append(curr_stmt)
            curr_stmt = None
            output.append("\n")
            prev_tight = False

        elif curr_stmt is None:
            if is_function_stmt(node):
                child_i = node.parent.children.index(node)
                if child_i > 0 and not is_function_stmt(node.parent.children[child_i - 1]):
                    output.append("\n")

            curr_stmt = node
            output.append(indent_str * indent)
            prev_tight = False
        
        if plain_lua:
            if node.type == NodeType.var and node.kind == VarKind.local:
                used_locals.add(node.name)

            if node.type == NodeType.unary_op:
                replace_op_with_call(node, k_unary_to_func, None, 1)

            elif node.type == NodeType.binary_op:
                replace_op_with_call(node, k_binary_to_func, 0, 2)
            
            elif node.type == NodeType.op_assign:
                target = node.target
                node.type = NodeType.binary_op
                node.children[1] = Token.synthetic(TokenType.punct, node.op, node, prepend=True)
                replace_op_with_call(node, k_binary_to_func, 0, 2)
                node.replace_with(Node(NodeType.custom, [target, Token.synthetic(TokenType.punct, "=", node, prepend=True), node.move()]))
            
            elif node.type == NodeType.call and node.short:
                new_children = [Token.synthetic(TokenType.ident, "print", node, prepend=True),
                                Token.synthetic(TokenType.punct, "(", node, prepend=True),
                                *node.children[1:],
                                Token.synthetic(TokenType.punct, ")", node, prepend=True)]
                node.replace_with(Node(NodeType.custom, new_children))
            
            elif node.type == NodeType.const and node.token.type == TokenType.number and node.token.value.lower().startswith("0b"):
                node.token.modify(format_num(ctxt.lang, node.token.parsed_value, sign='', base=16))

            elif node.type == NodeType.const and node.token.type == TokenType.string:
                quote = node.token.value[0]
                node.token.modify(format_string_literal(node.token.parsed_value, long=quote=='[', quote=quote,
                                                        use_ctrl_chars=False, plain_lua=True))

    def end_visit_node(node):
        nonlocal indent, curr_stmt, prev_tight

        if node.type == NodeType.block:
            if node.parent:
                indent -= 1

            curr_stmt = stmt_stack.pop()
            output.append(indent_str * indent)
            prev_tight = False
            
            # shorthand -> longhand
            if node.parent and is_short_block_stmt(node.parent) and not (node.parent.type == NodeType.if_ and node.parent.else_):
                output.append("end")

        elif node is curr_stmt:
            curr_stmt = None
            output.append("\n")
            prev_tight = False
                
            if is_function_stmt(node):
                output.append("\n")

    root.traverse_nodes(visit_node, end_visit_node, tokens=visit_token)

    return "".join(output)
