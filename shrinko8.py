#!/usr/bin/env python3
from utils import *
from pico_process import PicoContext, process_code, CartSource, CustomPreprocessor
from pico_cart import read_cart, write_cart_to_source, write_cart_to_image, from_pico_chars, write_code_sizes
import argparse, importlib.util

def CommaSep(val):
    return val.split(",")

extend_arg = "extend" if sys.version_info >= (3,8) else None

parser = argparse.ArgumentParser()
# input/output
parser.add_argument("input", help="input file, can be in p8/png/lua/code format")
parser.add_argument("output", help="output file", nargs='?')
parser.add_argument("-f", "--format", choices=["p8", "png", "lua", "code"], help="output format")
# lint
parser.add_argument("-l", "--lint", action="store_true", help="enable erroring on lint errors")
parser.add_argument("--no-lint-unused", action="store_true", help="don't print lint errors on unused variables")
parser.add_argument("--no-lint-duplicate", action="store_true", help="don't print lint errors on duplicate variables")
parser.add_argument("--no-lint-undefined", action="store_true", help="don't print lint errors on undefined variables")
parser.add_argument("--no-lint-fail", action="store_true", help="don't fail immediately on lint errors")
# minify
parser.add_argument("-m", "--minify", action="store_true", help="enable minification")
parser.add_argument("-p", "--preserve", type=CommaSep, action=extend_arg, help="preserve specific identifiers in minification, e.g. 'global1,global2,*.member2,table3.*'")
parser.add_argument("--no-preserve", type=CommaSep, action=extend_arg, help="do not preserve specific built-in identifiers in minification, e.g. 'circfill,rectfill'")
parser.add_argument("--no-minify-rename", action="store_true", help="disable variable renaming in minification")
parser.add_argument("--no-minify-spaces", action="store_true", help="disable space removal in minification")
parser.add_argument("--no-minify-lines", action="store_true", help="disable line removal in minification")
parser.add_argument("--no-minify-tokens", action="store_true", help="disable token removal in minification")
# count
parser.add_argument("-c", "--count", action="store_true", help="enable printing token count, character count & compressed size")
parser.add_argument("--input-count", action="store_true", help="enable printing input character count & compressed size, for now just for png format")
# script
parser.add_argument("-s", "--script", help="manipulate the cart via a custom python script - see README for api details")
parser.add_argument("--script-args", nargs=argparse.REMAINDER, help="send arguments directly to --script", default=())
# misc (semi-undocumented)
parser.add_argument("--rename-map", help="log renaming of identifiers (from minify step) to this file")
parser.add_argument("--force-compression", action="store_true", help="force code compression even if code fits (when creating pngs)")
parser.add_argument("--custom-preprocessor", action="store_true", help="enable a custom preprocessor (#define X 123, #ifdef X, #[X], #[X[[print('X enabled')]]])")
args = parser.parse_args()

res_path = path_dirname(path_resolve(__file__))

def fail(msg):
    print(msg)
    sys.exit(1)

if not args.lint and not args.count and not args.output and not args.input_count:
    fail("No operation (--lint/--count) or output file specified")
if args.format and not args.output:
    fail("Output should be specified under --format")
if args.minify and not args.output and not args.count:
    fail("Output (or --count) should be specified under --minify")
    
if not args.format and args.output:
    args.format = path_extension(args.output)[1:].lower()
    if args.format not in ("p8", "png", "lua"):
        args.format = "p8"

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
        "tokens": not args.no_minify_tokens,
    }

args.obfuscate = bool(args.minify) and not args.no_minify_rename
if args.obfuscate and (args.preserve or args.no_preserve):
    args.obfuscate = {}
    if args.preserve:
        args.obfuscate.update({k: False for k in args.preserve})
    if args.no_preserve:
        args.obfuscate.update({k: True for k in args.no_preserve})

preproc_cb, postproc_cb = None, None
if args.script:
    script_spec = importlib.util.spec_from_file_location(path_basename_no_extension(args.script), args.script)
    script_mod = importlib.util.module_from_spec(script_spec)
    script_spec.loader.exec_module(script_mod)
    preproc_cb = getattr(script_mod, "preprocess_main", None)
    postproc_cb = getattr(script_mod, "postprocess_main", None)

preprocessor = CustomPreprocessor() if args.custom_preprocessor else None
cart = read_cart(args.input, print_sizes=args.input_count, preprocessor=preprocessor)
src = CartSource(cart)
    
ctxt = PicoContext(srcmap=args.rename_map)
if preproc_cb:
    preproc_cb(cart=cart, src=src, ctxt=ctxt, args=args, res_path=res_path)

ok, errors = process_code(ctxt, src, count=args.count, lint=args.lint, minify=args.minify, obfuscate=args.obfuscate, fail=False)
if errors:
    print("Lint errors:" if ok else "Compilation errors:")
    for error in errors:
        print(error)
    if not ok or not args.no_lint_fail:
        sys.exit(1)

if args.rename_map:
    file_write_text(args.rename_map, "\n".join(ctxt.srcmap))
    
if postproc_cb:
    postproc_cb(cart=cart, args=args, res_path=res_path)

if args.output:
    if args.format == "p8":
        file_write_text(args.output, write_cart_to_source(cart))
    elif args.format == "png":
        file_write(args.output, write_cart_to_image(cart, res_path,
            print_sizes=args.count, force_compress=args.count or args.force_compression))
        args.count = False # done above
    else:
        prefix = "__lua__\n" if args.format == "code" else ""
        file_write_text(args.output, prefix + from_pico_chars(cart.code))

if args.count:
    write_code_sizes(cart.code)

if errors:
    sys.exit(2)
