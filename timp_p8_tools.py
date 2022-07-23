from utils import *
from pico_process import read_code, PicoContext, process_code, PicoSource
from pico_cart import read_cart, write_cart_to_source, write_cart_to_image, from_pico_chars, write_code_sizes
import argparse

def CommaSep(val):
    return val.split(",")

parser = argparse.ArgumentParser()
parser.add_argument("input", help="input file, can be in p8/png/code format")
parser.add_argument("output", help="output file", nargs='?')
parser.add_argument("-f", "--format", choices=["p8", "code"], help="output format")
parser.add_argument("--map", help="log renaming of identifiers to this file")
parser.add_argument("-l", "--lint", action="store_true", help="enable erroring on lint errors")
parser.add_argument("-c", "--count", action="store_true", help="enable printing token count, character count & compressed size")
parser.add_argument("-m", "--minify", action="store_true", help="enable minification")
parser.add_argument("-p", "--preserve", type=CommaSep, action="extend", help="preserve specific identifiers in minification, e.g. 'global1,global2,*.member2,table3.*'")
parser.add_argument("--no-preserve", type=CommaSep, action="extend", help="do not preserve specific built-in identifiers in minification, e.g. 'circfill,rectfill'")
parser.add_argument("--input-count", action="store_true", help="enable printing input character count & compressed size, for now just for png format")
parser.add_argument("--no-lint-unused", action="store_true", help="don't print lint errors on unused variables")
parser.add_argument("--no-lint-duplicate", action="store_true", help="don't print lint errors on duplicate variables")
parser.add_argument("--no-lint-undefined", action="store_true", help="don't print lint errors on undefined variables")
parser.add_argument("--no-lint-fail", action="store_true", help="don't fail immediately on lint errors")
parser.add_argument("--no-minify-rename", action="store_true", help="disable variable renaming in minification")
parser.add_argument("--no-minify-spaces", action="store_true", help="disable space removal in minification")
parser.add_argument("--no-minify-lines", action="store_true", help="disable line removal in minification")
args = parser.parse_args()

def fail(msg):
    print(msg)
    sys.exit(1)

if not args.lint and not args.count and not args.minify and not args.format and not args.input_count:
    fail("No operation (--lint/--count/--minify/--format) specified")
if args.format and not args.output:
    fail("Output should be specified under --format")
if args.minify and not args.output and not args.count:
    fail("Output (or --count) should be specified under --minify")
args.format = args.format or "p8"

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
if args.obfuscate:
    args.obfuscate = {}
    if args.preserve:
        args.obfuscate.update({k: False for k in args.preserve})
    if args.no_preserve:
        args.obfuscate.update({k: True for k in args.no_preserve})

cart = read_cart(args.input, print_sizes=args.input_count)
try:
    src = read_code(args.input, pp_inline=False, fail=False) # supports #include (and other stuff), which read_cart currently does not
except UnicodeDecodeError: # hacky png detection
    src = PicoSource(path_basename(args.input), cart.code)

if src.errors:
    print("Preprocessor errors:")
    for error in src.errors:
        print(error)
    sys.exit(1)

ctxt = PicoContext(srcmap=args.map)
ok, errors = process_code(ctxt, src, count=args.count, lint=args.lint, minify=args.minify, obfuscate=args.obfuscate, fail=False)
if errors:
    print("Lint errors:" if ok else "Compilation errors:")
    for error in errors:
        print(error)
    if not ok or not args.no_lint_fail:
        sys.exit(1)

if args.map:
    file_write_text(args.map, "\n".join(ctxt.srcmap))
    
cart.code = src.new_text if args.minify else src.text

if args.output:
    if args.format == "p8":
        file_write_text(args.output, write_cart_to_source(cart))
    #elif args.format == "png":
    #    with file_create(args.output) as f:
    #        write_cart_to_image(f, cart, path_dirname(path_resolve(__file__)), print_sizes=args.count, force_compress=args.count)
    #        args.count = False # done above
    else:
        file_write_text(args.output, "__lua__\n" + from_pico_chars(cart.code))

#if args.count:
#    write_code_sizes(cart.code)

if errors:
    sys.exit(2)
