from utils import *
from pico_tokenize import TokenType, Token
from pico_parse import NodeType

def unminify_code(source, tokens, root, unminify):
    
    indent_delta = 2
    if isinstance(unminify, dict):
        indent_delta = unminify.get("indent", indent_delta)

    output = []
    prev_token = Token.dummy(None)
    prev_tight = False
    indent = 0
    short_count = 0
    curr_stmt = None
    stmt_stack = []

    def visit_token(token):
        nonlocal prev_token, prev_tight
        if token.fake or token.value is None:
            return
        
        # TODO: preserve comments

        if prev_tight and prev_token.value not in ("(", "[", "{", ".", ":") and token.value not in (")", "]", "}", ",", ".", ":") and \
                not (token.value in ("(", "[") and prev_token.type == TokenType.ident):
            output.append(" ")

        output.append(token.value)
        prev_token = token
        prev_tight = True

    def visit_node(node):
        nonlocal indent, curr_stmt, short_count, prev_tight

        if node.type == NodeType.block:
            if node.parent:
                indent += indent_delta
                if getattr(node.parent, "short", False):
                    short_count += 1

            stmt_stack.append(curr_stmt)
            curr_stmt = None
            output.append(" " if short_count else "\n")
            prev_tight = False

        elif curr_stmt is None:
            curr_stmt = node
            if not short_count:
                output.append(" " * indent)
                prev_tight = False

    def end_visit_node(node):
        nonlocal indent, curr_stmt, short_count, prev_tight

        if node.type == NodeType.block:
            if node.parent:
                indent -= indent_delta
                if getattr(node.parent, "short", False):
                    short_count -= 1

            next_is_short_else = node.parent and node.parent.type == NodeType.if_ and node.parent.short and node.parent.then is node and node.parent.else_

            curr_stmt = stmt_stack.pop()
            if not short_count and not next_is_short_else:
                output.append(" " * indent)
                prev_tight = False

        elif node is curr_stmt:
            curr_stmt = None
            output.append("; " if short_count else "\n")
            prev_tight = False

    root.traverse_nodes(visit_node, end_visit_node, tokens=visit_token)

    return "".join(output)
