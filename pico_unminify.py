from utils import *
from pico_tokenize import TokenType, Token
from pico_parse import NodeType, is_function_stmt, is_short_block_stmt

def unminify_code(root, unminify_opts):    
    indent_delta = unminify_opts.get("indent", 2)

    output = []
    prev_token = Token.none
    prev_tight = False
    indent = 0
    curr_stmt = None
    stmt_stack = []

    k_tight_prefix_tokens = ("(", "[", "{", "?", ".", ":", "::")
    k_tight_suffix_tokens = (")", "]", "}", ",", ";", ".", ":", "::")

    def visit_token(token):
        nonlocal prev_token, prev_tight

        for comment in token.children:
            comment_value = comment.value
            if "\n" in comment_value:
                if prev_tight:
                    output.append("\n")
                    output.append(" " * indent)
                output.append(comment_value)
                if not comment_value.endswith("\n"):
                    output.append("\n")
                output.append(" " * indent)
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

        if prev_tight and prev_token.value not in k_tight_prefix_tokens and \
                token.value not in k_tight_suffix_tokens and \
                not (token.value in ("(", "[") and (prev_token.type == TokenType.ident or 
                                                    prev_token.value in ("function", ")", "]", "}"))) and \
                not (prev_token.type == TokenType.punct and prev_token.parent.type == NodeType.unary_op):
            output.append(" ")

        output.append(token.value)
        prev_token = token
        prev_tight = True

    def visit_node(node):
        nonlocal indent, curr_stmt, prev_tight

        if node.type == NodeType.block:
            if node.parent:
                indent += indent_delta
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
            output.append(" " * indent)
            prev_tight = False

    def end_visit_node(node):
        nonlocal indent, curr_stmt, prev_tight

        if node.type == NodeType.block:
            if node.parent:
                indent -= indent_delta

            curr_stmt = stmt_stack.pop()
            output.append(" " * indent)
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
