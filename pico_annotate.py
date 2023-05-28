from utils import *

k_counts_re = re.compile(r"^-- T:\d+ C:\d+( minC:\d+)?$")
k_min_source_str = "-- minified source:"

# finds where the annotation previously added before node starts, so that it can be replaced instead of stacked.
# the block is a suffix of node's comments, as it's always added directly before node - any comments above it are the user's.
def find_annotation(source, node):
    comments = [cmt for cmt in node.first_token().children if cmt.source is source]
    texts = [source.text[cmt.idx:cmt.endidx].rstrip() for cmt in comments] # comment spans include their newline

    start = None
    for i, text in enumerate(texts):
        # the counts are the last line of a block only when the minified source was omitted
        if k_counts_re.match(text) and (i + 1 == len(texts) or texts[i + 1] == k_min_source_str):
            start = comments[i].idx
    return start

def annotate_code(ctxt, source, root, annotate_opts):
    fail = annotate_opts.get("fail", True)

    funcs = []
    def visit(node):
        if node.type == NodeType.function and node.source is source:
            funcs.append(node)
    root.traverse_nodes(pre=visit, extra=True)

    # an annotation spans from its first comment up to the node it describes
    func_starts = [(node, find_annotation(source, node)) for node in funcs]
    old_annotations = sorted((start, node.idx) for node, start in func_starts if start != None)

    # a node's own annotation is outside of it, but the annotations of any nodes nested in it are not,
    # and counting those would make each run over an already-annotated source report larger numbers.
    def text_without_annotations(idx, endidx):
        parts, pos = [], idx
        for start, end in old_annotations:
            if start >= idx and end <= endidx:
                parts.append(source.text[pos:start])
                pos = end
        parts.append(source.text[pos:endidx])
        return "".join(parts)

    # measure everything before modifying source.text, as that invalidates the nodes' indices
    annotations = []
    for node, start in func_starts:
        text = text_without_annotations(node.idx, node.endidx)
        token_count = count_tokens(node.get_tokens())
        min_text, errors = minify_source(ctxt, text, for_expr=not node.target)
        if errors:
            if fail:
                throw("\n".join(map(str, errors)))
            min_text = None
        annotations.append((node.idx if start == None else start, node.idx, text, token_count, min_text))

    # apply in reverse order, so that each replacement leaves the earlier indices valid
    for idx, endidx, text, token_count, min_text in sorted(annotations, reverse=True, key=lambda ann: ann[0]):
        comment = f"-- T:{token_count} C:{len(text)}"
        if min_text != None:
            comment += f" minC:{len(min_text)}\n{k_min_source_str}\n{comment_out(min_text)}"
        # no newline is added before the comment, so that the annotation is exactly the text removed above
        source.text = f"{source.text[:idx]}{comment}\n{source.text[endidx:]}"

# comments out every line, including blank ones, so that the result is a single unbroken run of comments
def comment_out(text):
    return "\n".join(f"-- {line}" if line.strip() else "--" for line in text.splitlines())

# minifies a standalone snippet of code, in isolation from the rest of the cart
def minify_source(ctxt, text, for_expr=False):
    sub_source = Source("annotate", text)
    tokens, errors = tokenize(sub_source, ctxt, inner=True)
    if not errors:
        sub_root, errors = parse(sub_source, tokens, ctxt, for_expr=for_expr)
    if errors:
        return None, errors

    rename_tokens(ctxt, sub_root, {})
    minify_code(ctxt, sub_root, {})
    return output_code(ctxt, sub_root, {}), ()

from pico_tokenize import tokenize, count_tokens
from pico_parse import parse, NodeType
from pico_process import Source
from pico_minify import minify_code
from pico_output import output_code
from pico_rename import rename_tokens
