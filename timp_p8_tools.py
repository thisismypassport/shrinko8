from utils import *
from pico_process import read_code, PicoContext, process_code
from pico_cart import Cart, read_cart, write_cart_to_source
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("input")
parser.add_argument("output")
parser.add_argument("-f", "--format", choices=["p8", "code"], default="p8")
parser.add_argument("--map")
parser.add_argument("-l", "--lint", action="store_true")
parser.add_argument("-c", "--count", action="store_true")
parser.add_argument("-m", "--minify", action="store_true")
parser.add_argument("-p", "--preserve")
args = parser.parse_args()

if not args.lint and not args.count and not args.minify:
    print("No operation (--lint/--count/--minify) specified")
    sys.exit(1)

args.obfuscate = bool(args.minify)
if args.preserve:
    args.obfuscate = {k: False for k in args.preserve.split(",")}

cart = read_cart(args.input)
src = read_code(args.input) # supports #include (and other stuff), which read_cart currently does not
ctxt = PicoContext(srcmap=args.map)
process_code(ctxt, src, count=args.count, lint=args.lint, minify=args.minify, obfuscate=args.obfuscate)

if args.map:
    file_write_text(args.map, "\n".join(ctxt.srcmap))

if args.minify:
    cart.code = src.new_text
    if args.format == "p8":
        file_write_text(args.output, write_cart_to_source(cart))
    else:
        file_write_text(args.output, "__lua__\n" + cart.code)
