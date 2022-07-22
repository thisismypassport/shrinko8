from utils import *
from pico_process import read_code, PicoContext, process_code, PicoSource
from pico_cart import read_cart, write_cart_to_source, from_pico_chars
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("input", help="input file, can be in p8/png/code format")
parser.add_argument("output", help="output file", nargs='?')
parser.add_argument("-f", "--format", choices=["p8", "code"], default="p8", help="output format")
parser.add_argument("--map", help="log renaming of identifiers to this file")
parser.add_argument("-l", "--lint", action="store_true", help="enable erroring on lint errors")
parser.add_argument("-c", "--count", action="store_true", help="enable printing token count")
parser.add_argument("-m", "--minify", action="store_true", help="enable minification")
parser.add_argument("-p", "--preserve", help="preserve identifiers in minification, e.g. 'global1,global2,*.member2,table3.*'")
parser.add_argument("--no-lint-unused", action="store_true", help="don't print lint errors on unused variables")
parser.add_argument("--no-lint-duplicate", action="store_true", help="don't print lint errors on duplicate variables")
parser.add_argument("--no-lint-undefined", action="store_true", help="don't print lint errors on undefined variables")
parser.add_argument("--no-minify-rename", action="store_true", help="disable variable renaming in minification")
parser.add_argument("--no-minify-spaces", action="store_true", help="disable space removal in minification")
parser.add_argument("--no-minify-lines", action="store_true", help="disable line removal in minification")
args = parser.parse_args()

def fail(msg):
    print(msg)
    sys.exit(1)

if not args.lint and not args.count and not args.minify:
    fail("No operation (--lint/--count/--minify) specified")
if args.minify and not args.output:
    fail("Output should be specified under --minify")

if args.lint:
    args.lint = {
        "unused": not args.no_lint_unused,
        "duplicate": not args.no_lint_duplicate,
        "undefined": not args.no_lint_undefined,
    }

if args.minify:
    args.minify = {
        "lines": not args.no_minify_lines,
        "wspace": not args.no_minify_spaces,
    }

args.obfuscate = bool(args.minify) and not args.no_minify_rename
if args.preserve:
    args.obfuscate = {k: False for k in args.preserve.split(",")}

cart = read_cart(args.input)
try:
    src = read_code(args.input, pp_inline=False) # supports #include (and other stuff), which read_cart currently does not
except UnicodeDecodeError: # hacky png detection
    src = PicoSource(path_basename(args.input), cart.code)

ctxt = PicoContext(srcmap=args.map)
process_code(ctxt, src, count=args.count, lint=args.lint, minify=args.minify, obfuscate=args.obfuscate)

if args.map:
    file_write_text(args.map, "\n".join(ctxt.srcmap))

if args.minify:
    cart.code = src.new_text
    if args.format == "p8":
        file_write_text(args.output, write_cart_to_source(cart))
    else:
        file_write_text(args.output, "__lua__\n" + from_pico_chars(cart.code))
