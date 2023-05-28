from textwrap import indent

# Calls function for the descendants of node, then for node
def apply_node_tree(node, func):
    if hasattr(node, "extra_children"):
        for child in reversed(node.extra_children):
            apply_node_tree(child, func)
    for child in reversed(node.children):
        apply_node_tree(child, func)
    func(node)

def annotate_code(ctxt, source, root, fail=True):
    def comment_before_function(node, source=source):
        if node.type==NodeType.function:
            tokens, errors = tokenize(PicoSource("temp", source.text[node.idx:node.endidx]), ctxt)
            if fail and errors:
                raise Exception("\n".join(map(str, errors)))
            token_count = count_tokens(tokens)
            char_count = len(source.text[node.idx:node.endidx])
            print("SOURCE:")
            print(source.text[node.idx:node.endidx])
            rename_tokens(ctxt, node, True)
            minified_source = minify_code(source.text[node.idx:node.endidx], ctxt, node, minify=True)
            min_char_count = len(minified_source)
            prefix_newline = "\n" if node.idx > 0 and source.text[node.idx-1] != "\n" else ""
            source.text = f'{source.text[:node.idx]}{prefix_newline}-- T:{token_count} C:{char_count} minC:{min_char_count}\n-- minified source:\n{indent(minified_source,"-- ")}\n{source.text[node.idx:]}'
    apply_node_tree(root, comment_before_function)

from pico_tokenize import tokenize, count_tokens
from pico_parse import NodeType
from pico_process import PicoSource
from pico_minify import minify_code
from pico_rename import rename_tokens
