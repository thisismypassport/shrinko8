#!/usr/bin/env python3
from utils import *
from pico_process import PicoContext, process_code, CartSource, CustomPreprocessor
from pico_cart import CartFormat, read_cart, write_cart, write_code_sizes, download_cart_from_bbs
import argparse, importlib.util

def CommaSep(val):
    return val.split(",")

extend_arg = "extend" if sys.version_info >= (3,8) else None

parser = argparse.ArgumentParser()
parser.add_argument("input", help="input file, can be in any format. ('-' for stdin)")
parser.add_argument("output", help="output file. ('-' for stdout)", nargs='?')

parser.add_argument("-f", "--format", type=CartFormat, help="output format {%s}" % ",".join(CartFormat._output_values))
parser.add_argument("-F", "--input-format", type=CartFormat, help="input format {%s}" % ",".join(CartFormat._values))
parser.add_argument("-u", "--unicode-caps", action="store_true", help="write capitals as italicized unicode characters (better for copy/paste)")

pgroup = parser.add_argument_group("minify options")
pgroup.add_argument("-m", "--minify", action="store_true", help="enable minification")
pgroup.add_argument("-p", "--preserve", type=CommaSep, action=extend_arg, help="preserve specific identifiers in minification, e.g. 'global1,global2,*.member2,table3.*'")
pgroup.add_argument("--no-preserve", type=CommaSep, action=extend_arg, help="do not preserve specific built-in identifiers in minification, e.g. 'circfill,rectfill'")
pgroup.add_argument("--no-minify-rename", action="store_true", help="disable variable renaming in minification")
pgroup.add_argument("--no-minify-spaces", action="store_true", help="disable space removal in minification")
pgroup.add_argument("--no-minify-lines", action="store_true", help="disable line removal in minification")
pgroup.add_argument("--no-minify-comments", action="store_true", help="disable comment removal in minification (requires --no-minify-spaces)")
pgroup.add_argument("--no-minify-tokens", action="store_true", help="disable token removal in minification")
pgroup.add_argument("--rename-map", help="log renaming of identifiers (from minify step) to this file")

pgroup = parser.add_argument_group("lint options")
pgroup.add_argument("-l", "--lint", action="store_true", help="enable erroring on lint errors")
pgroup.add_argument("--no-lint-unused", action="store_true", help="don't print lint errors on unused variables")
pgroup.add_argument("--no-lint-duplicate", action="store_true", help="don't print lint errors on duplicate variables")
pgroup.add_argument("--no-lint-undefined", action="store_true", help="don't print lint errors on undefined variables")
pgroup.add_argument("--no-lint-fail", action="store_true", help="don't fail immediately on lint errors")

pgroup = parser.add_argument_group("count options")
pgroup.add_argument("-c", "--count", action="store_true", help="enable printing token count, character count & compressed size")
pgroup.add_argument("--input-count", action="store_true", help="enable printing input character count & compressed size, for now just for png format")

pgroup = parser.add_argument_group("script options")
pgroup.add_argument("-s", "--script", help="manipulate the cart via a custom python script - see README for api details")
pgroup.add_argument("--script-args", nargs=argparse.REMAINDER, help="send arguments directly to --script", default=())

pgroup = parser.add_argument_group("misc. options (semi-undocumented)")
pgroup.add_argument("--version", action="store_true", help="print version of cart")
pgroup.add_argument("--bbs", action="store_true", help="interpret input file as a bbs cart id, e.g. '#...'")
pgroup.add_argument("--fast-compression", action="store_true", help="force fast but poor compression (when creating pngs)")
pgroup.add_argument("--force-compression", action="store_true", help="force code compression even if code fits (when creating pngs)")
pgroup.add_argument("--custom-preprocessor", action="store_true", help="enable a custom preprocessor (#define X 123, #ifdef X, #[X], #[X[[print('X enabled')]]])")

args = parser.parse_args()

if args.input == "-":
    args.input = StdPath("-")
if args.output == "-":
    args.output = StdPath("-")

if args.bbs:
    args.input = DataPath(args.input, download_cart_from_bbs(args.input))
    args.input_format = CartFormat.png

def fail(msg):
    print(msg)
    sys.exit(1)

if not args.lint and not args.count and not args.output and not args.input_count and not args.version:
    fail("No operation (--lint/--count) or output file specified")
if args.format and not args.output:
    fail("Output should be specified under --format")
if args.minify and not args.output and not args.count:
    fail("Output (or --count) should be specified under --minify")
    
if not args.format and args.output:
    ext = path_extension(args.output)[1:].lower()
    if ext in CartFormat._ext_values:
        args.format = CartFormat(ext)
    else:
        args.format = CartFormat.p8

if not args.input_format and args.input:
    ext = path_extension(args.input)[1:].lower()
    if ext in CartFormat._ext_values:
        args.input_format = CartFormat(ext)

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
        "comments": not args.no_minify_comments,
        "tokens": not args.no_minify_tokens,
    }

args.obfuscate = bool(args.minify) and not args.no_minify_rename
if args.obfuscate and (args.preserve or args.no_preserve):
    args.obfuscate = {}
    if args.preserve:
        args.obfuscate.update({k: False for k in args.preserve})
    if args.no_preserve:
        args.obfuscate.update({k: True for k in args.no_preserve})

preproc_cb, postproc_cb, sublang_cb = None, None, None
if args.script:
    script_spec = importlib.util.spec_from_file_location(path_basename_no_extension(args.script), args.script)
    script_mod = importlib.util.module_from_spec(script_spec)
    script_spec.loader.exec_module(script_mod)
    preproc_cb = getattr(script_mod, "preprocess_main", None)
    postproc_cb = getattr(script_mod, "postprocess_main", None)
    sublang_cb = getattr(script_mod, "sublanguage_main", None)

preprocessor = CustomPreprocessor() if args.custom_preprocessor else None
cart = read_cart(args.input, args.input_format, print_sizes=args.input_count, preprocessor=preprocessor)
src = CartSource(cart)
    
ctxt = PicoContext(srcmap=args.rename_map, sublang_getter=sublang_cb)
if preproc_cb:
    preproc_cb(cart=cart, src=src, ctxt=ctxt, args=args, res_path=None) # (res_path is obsolete)

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
    postproc_cb(cart=cart, args=args, res_path=None) # (res_path is obsolete)

if args.output:
    write_cart(args.output, cart, args.format, print_sizes=args.count, 
               unicode_caps=args.unicode_caps,
               force_compress=args.count or args.force_compression,
               fast_compress=args.fast_compression)
    if args.format not in CartFormat._src_values:
        args.count = False # handled above

if args.count:
    write_code_sizes(cart.code, fast_compress=args.fast_compression)
if args.version:
    hex = cart.version_hex
    print("version: %d, %d.%d.%d, %c" % (cart.version_id, hex>>16, (hex>>8)&0xff, hex&0xff, cart.platform))

if errors:
    sys.exit(2)
