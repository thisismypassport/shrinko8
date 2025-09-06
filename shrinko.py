from utils import *
from pico_process import PicoContext, process_code, CartSource, ErrorFormat
from pico_compress import write_code_size, write_compressed_size, CompressionTracer
from pico_cart import CartFormat, read_cart, write_cart, get_bbs_cart_url, merge_cart, write_cart_version
from pico_export import read_cart_export, read_pod_file, ListOp
from pico_tokenize import k_hint_split_re
from pico_constfold import parse_constant
from pico_defs import Language, get_default_pico8_version
from picotron_defs import PicotronContext, Cart64Source, get_default_picotron_version
from picotron_cart import Cart64Format, read_cart64, write_cart64, merge_cart64, filter_cart64, preproc_cart64
from picotron_cart import write_cart64_compressed_size, write_cart64_version
from picotron_export import read_cart64_export, read_sysrom_file
import argparse

k_version = 'v1.2.6'

def SplitBySeps(val):
    return k_hint_split_re.split(val)

def Indent(val):
    return "\t" if val == "tabs" else " " * int(val)

def EnumFromStr(enum_type):
    def cvt(name):
        return enum_type(name.replace("-", "_").replace(" ", "_"))
    cvt.__name__ = enum_type.__name__
    return cvt

def EnumList(enum_type, pred=None):
    list = enum_type._values
    if pred:
        list = filter(lambda name: pred(enum_type(name)), list)
    return ", ".join(str.replace("_", "-") for str in list)

def ParsableCountHandler(prefix, name, size, limit):
    print(f"count:{prefix}:{name}:{size}:{limit}")

def lang_not_supported():
    throw("operation not supported for this language")
def lang_do_nothing(*_, **__):
    pass

def find_in_builtin_script(name, func_name):
    import importlib
    try:
        module = importlib.import_module("scripts." + str_before_first(name, "."))
    except ModuleNotFoundError:
        return None
    func = getattr(module, func_name, None)
    if func:
        return func(name)

def create_main(lang):
    is_pico8 = lang == Language.pico8
    is_picotron = lang == Language.picotron

    if is_pico8:
        CartFormatCls = CartFormat
        CartSourceCls = CartSource
        ContextCls = PicoContext

        read_cart_func = read_cart
        read_cart_export_func = read_cart_export
        read_pico_dat_func = read_pod_file
        merge_cart_func = merge_cart
        filter_cart_func = lang_not_supported
        preproc_cart_func = lang_not_supported
        write_cart_func = write_cart
        write_code_size_func = write_code_size
        write_compressed_size_func = write_compressed_size
        write_cart_version_func = write_cart_version
        get_default_version_func = get_default_pico8_version

        pico_name = "pico8"
        label_section = "label"

    elif is_picotron:
        CartFormatCls = Cart64Format
        CartSourceCls = Cart64Source
        ContextCls = PicotronContext
        
        read_cart_func = read_cart64
        read_cart_export_func = read_cart64_export
        read_pico_dat_func = read_sysrom_file
        merge_cart_func = merge_cart64
        filter_cart_func = filter_cart64
        preproc_cart_func = preproc_cart64
        write_cart_func = write_cart64
        write_code_size_func = lang_do_nothing
        write_compressed_size_func = write_cart64_compressed_size
        write_cart_version_func = write_cart64_version
        get_default_version_func = get_default_picotron_version
        
        pico_name = "picotron"
        label_section = "label.png"
    
    else:
        fail("unknown language")

    def create_parser():
        src_ext = CartFormatCls.default_src

        if is_pico8:
            sections_str = "sections"
            sections_desc = "comma separated list of sections out of {%s}" % ",".join(("lua", "gfx", "map", "gff", "sfx", "music", "label", "meta:*"))
        else:
            sections_str = "files"
            sections_desc = "comma separated list of files (can use wildcards and ! for exclude)"
        sections_meta = sections_str.upper()

        parser = argparse.ArgumentParser()
        parser.add_argument("input", help="input file, can be in any format. ('-' for stdin)", nargs='?')
        parser.add_argument("additional_inputs", help="extra input files. (for use when creating exports)", nargs='*')
        parser.add_argument("output", help="output file. ('-' for stdout)", nargs='?')
        parser.add_argument("-f", "--format", type=EnumFromStr(CartFormatCls),
                            help="output cart format {%s}" % EnumList(CartFormatCls, lambda e: e.is_output and e.is_exposed))
        parser.add_argument("-F", "--input-format", type=EnumFromStr(CartFormatCls),
                            help="input cart format {%s}" % EnumList(CartFormatCls, lambda e: e.is_input and e.is_exposed))
        parser.add_argument("-i", "--in-place", action="store_true", help="modify the input file in-place")
        if is_pico8:
            parser.add_argument("-u", "--unicode-caps", action="store_true", help="write capitals as italicized unicode characters (better for copy/paste)")
        else:
            parser.set_defaults(unicode_caps=False)

        pgroup = parser.add_argument_group("minify options")
        pgroup.add_argument("-m", "--minify", action="store_true", help="enable minification of the cart")
        pgroup.add_argument("-M", "--minify-safe-only", action="store_true", help="only do minification that's always safe to do")
        pgroup.add_argument("--minify-consts-only", action="store_true", help="only do constant folding - no other minification")
        if is_pico8:
            pgroup.add_argument("-ot", "--focus-tokens", action="store_true", help="when minifying, focus on reducing the amount of tokens")
            pgroup.add_argument("-oc", "--focus-chars", action="store_true", help="when minifying, focus on reducing the amount of characters")
            pgroup.add_argument("-ob", "--focus-compressed", action="store_true", help="when minifying, focus on reducing the code's compressed size")
        else:
            pgroup.set_defaults(focus_tokens=False, focus_chars=False, focus_compressed=True)
        pgroup.add_argument("--no-minify-rename", action="store_true", help="disable variable renaming in minification")
        pgroup.add_argument("--no-minify-consts", action="store_true", help="disable constant folding in minification")
        pgroup.add_argument("--no-minify-spaces", action="store_true", help="disable space removal in minification")
        pgroup.add_argument("--no-minify-lines", action="store_true", help="disable line removal in minification")
        pgroup.add_argument("--no-minify-comments", action="store_true", help="disable comment removal in minification (requires --no-minify-spaces)")
        pgroup.add_argument("--no-minify-tokens", action="store_true", help="disable token removal/changes in minification")
        pgroup.add_argument("--no-minify-reorder", action="store_true", help="disable statement reordering in minification")
        pgroup.add_argument("-p", "--preserve", type=SplitBySeps, action="extend", help='preserve specific identifiers in minification, e.g. "global1, global2, *.member2, table3.*"')
        pgroup.add_argument("--no-preserve", type=SplitBySeps, action="extend", help='do not preserve specific built-in identifiers in minification, e.g. "circfill, rectfill"')
        pgroup.add_argument("--rename-members-as-globals", action="store_true", help='rename globals and members the same way (same as --preserve "*=*.*")')
        pgroup.add_argument("--rename-safe-only", action="store_true", help="only do renaming that's always safe to do (subset of --minify-safe-only)")
        pgroup.add_argument("--reorder-safe-only", action="store_true", help="only do statement reordering that's always safe to do (subset of --minify-safe-only)")
        pgroup.add_argument("--builtins-safe-only", action="store_true", help="only assume a function is builtin when it's always safe to do (subset of --minify-safe-only)")
        pgroup.add_argument("--rename-map", help="log renaming of identifiers (from minify step) to this file")
        pgroup.add_argument("--const", nargs=2, action="append", metavar=("NAME", "VALUE"), help="define a constant that will be replaced with the VALUE across the entire file")
        pgroup.add_argument("--str-const", nargs=2, action="append", metavar=("NAME", "VALUE"), help="same as --const, but the value is interpreted as a string")

        pgroup = parser.add_argument_group("lint options")
        pgroup.add_argument("-l", "--lint", action="store_true", help="enable checking the cart for common issues")
        pgroup.add_argument("--no-lint-unused", action="store_true", help="don't print lint warnings on unused variables")
        pgroup.add_argument("--no-lint-unused-global", action="store_true", help="don't print lint warnings on unused global variables")
        pgroup.add_argument("--no-lint-duplicate", action="store_true", help="don't print lint warnings on duplicate variables")
        pgroup.add_argument("--no-lint-duplicate-global", action="store_true", help="don't print lint warnings on duplicate variables between a local and a global")
        pgroup.add_argument("--no-lint-undefined", action="store_true", help="don't print lint warnings on undefined variables")
        pgroup.add_argument("--no-lint-fail", action="store_true", help="create output cart even if there were lint warnings")
        pgroup.add_argument("--lint-global", type=SplitBySeps, action="extend", help="don't print lint warnings for these globals (same as '--lint:' comment)")
        pgroup.add_argument("--error-format", type=EnumFromStr(ErrorFormat), help="how to format lint warnings & compilation errors {%s}" % EnumList(ErrorFormat))

        pgroup = parser.add_argument_group("count options")
        pgroup.add_argument("-c", "--count", action="store_true", help="enable printing token count, character count & compressed size")
        pgroup.add_argument("--input-count", action="store_true", help="enable printing input token count, character count & compressed size")
        pgroup.add_argument("--parsable-count", action="store_true", help="output counts in a stable, parsable format")
        pgroup.add_argument("--no-count-compress", action="store_true", help="do not compress the cart just to print the compressed size")
        pgroup.add_argument("--no-count-tokenize", action="store_true",
                            help="do not tokenize the cart just to print the token count" if is_pico8 else argparse.SUPPRESS)

        pgroup = parser.add_argument_group("unminify options")
        pgroup.add_argument("-U", "--unminify", action="store_true", help="enable unminification of the cart")
        pgroup.add_argument("--unminify-indent", type=Indent, help="indentation when unminifying - either 'tabs' or a number of spaces (default: 2)", default="2")

        pgroup = parser.add_argument_group("misc. options")
        pgroup.add_argument("-s", "--script", action="append", help="manipulate the cart via a custom python script - see README for api details")
        pgroup.add_argument("--script-args", nargs=argparse.REMAINDER, help="send arguments directly to --script", default=())
        pgroup.add_argument("--label", help=f"image to use as the label (default: taken from __label__ like {lang} does)")
        pgroup.add_argument("--title", action="append", 
                            help=f"text to use as the title (default: taken from first two comments like {lang} does). Use twice for a second line")
        pgroup.add_argument("--extra-output", nargs='+', action="append", metavar=("OUTPUT [FORMAT]", ""),
                            help="additional output file to produce (and optionally, the format to use)")

        if is_picotron:
            pgroup = parser.add_argument_group("picotron filesystem options")
            pgroup.add_argument("--code-files", dest="code_sections", type=SplitBySeps, action="extend",
                                help=f"specify a {sections_desc} that contain lua code to process (default: *.lua)")
            pgroup.add_argument("--delete-meta", type=SplitBySeps, action="extend",
                                help=f"specify a {sections_desc} to delete metadata of (default: * if minifying unsafely, else none)")
            pgroup.add_argument("--delete-label", action="store_true", default=None, help="always delete the label")
            pgroup.add_argument("--keep-label", action="store_false", dest="delete_label", help="always keep the label")
            pgroup.add_argument("--keep-pod-compression", action="store_true", help="keep compression of all pod files as-is")
            pgroup.add_argument("-u", "--uncompress-pods", action="store_true", help="uncompress all pod files to plain text")
            pgroup.add_argument("--base64-pods", action="store_true", help="base64 all pod files")
            pgroup.add_argument("--list", action="store_true", help="list all files inside the cart")
            pgroup.add_argument("--filter", type=SplitBySeps, action="extend", help=f"specify a {sections_desc} to keep in the output")
            pgroup.add_argument("--insert", nargs='+', action="append", metavar=(f"INPUT [FSPATH [FILTER]]", ""),
                                help=f"insert the specified file or directory INPUT into FSPATH. (FILTER can be a {sections_desc} to insert - relative to cart root)")
            pgroup.add_argument("--extract", nargs='+', action="append", metavar=(f"FSPATH [OUTPUT]", ""),
                                help=f"extract the specified file or directory from FSPATH to OUTPUT ")
        else:
            pgroup.set_defaults(code_sections=None, delete_meta=None, keep_label=None, uncompress_pods=None, keep_pod_compression=None, base64_pods=None,
                                filter=None, insert=None, extract=None)
        
        pgroup.add_argument("--merge", nargs='+', action="append", metavar=(f"INPUT {sections_meta} [FORMAT]", ""),
                            help=f"merge {sections_str} from the specified INPUT file, where {sections_meta} is a {sections_desc}")

        if is_pico8:
            pgroup = parser.add_argument_group("cart export options (for use with the formats: %s)" % EnumList(CartFormatCls, lambda e: e.is_export and e.is_exposed))
            pgroup.add_argument("--list", action="store_true", help="list all cart names inside the export")
            pgroup.add_argument("--dump", help="dump all carts inside the export to the specified folder. -f can be used to specify the output format")
            pgroup.add_argument("--cart", help="name of cart to extract from the export")
            pgroup.add_argument("--pico8-dat", dest="pico_dat", help="path to the pico8.dat file in the pico8 directory. needed to create new exports")
            pgroup.add_argument("--output-cart", help="override name to use for the main cart in the export")
            pgroup.add_argument("--extra-input", nargs='+', action="append", metavar=("INPUT [FORMAT [NAME]]", ""),
                                help="additional input file to place in export (and optionally, the format of the file & the name to use for it in the export)")
        else:
            pgroup.add_argument("--picotron-dat", dest="pico_dat", help="path to the picotron.dat file in the picotron directory. needed to create exports")
            pgroup.add_argument("--dump-misc", dest="dump", help="dump the cart, sysrom, etc. inside a sysrom.dat to the specified folder. -f can be used to specify the output format")
            pgroup.set_defaults(cart=None, output_cart=None, extra_input=())

        pgroup = parser.add_argument_group("other interesting options (semi-undocumented)")
        pgroup.add_argument("--template-image", help=f"template image to use for png carts, instead of the default {lang} template")
        pgroup.add_argument("--template-only", action="store_true", help="when creating the png cart, ignore the label & title, using just the template")
        pgroup.add_argument("--version", action="store_true", help="print version of cart. (if no cart is provided - print shrinko8 version and exit)")
        pgroup.add_argument("--output-version", type=int, help=f"the version to convert the cart to. (Same as 'version' field of {src_ext} files)")
        pgroup.add_argument("--update-version", action="store_true", help="convert the cart to the highest supported version")
        pgroup.add_argument("--bbs", action="store_true", help="interpret input as a bbs cart id, e.g. '#...' and download it from the bbs")
        pgroup.add_argument("--url", action="store_true", help="interpret input as a URL, and download it from the internet")
        if is_pico8:
            pgroup.add_argument("--dump-misc-too", action="store_true", help="causes --dump to also dump misc. files inside the export")
            pgroup.set_defaults(avoid_base64=False)
        else:
            pgroup.add_argument("--avoid-base64", action="store_true", help=f"avoid using base64 in p64 files whenever possible")
            pgroup.set_defaults(dump_misc_too=True)

        if is_pico8:
            pgroup = parser.add_argument_group("export editing options (semi-undocumented)")
            pgroup.add_argument("--insert-cart", nargs="*", metavar=("NAME", "BEFORE"), help="add the cart to an existing export. (The default name is the input cart's name)")
            pgroup.add_argument("--replace-cart", nargs="*", metavar=("NAME"), help="replace the cart with the given name (Default: main cart) in the export")
            pgroup.add_argument("--delete-cart", nargs=1, help="delete the cart with the given name from the export")
            pgroup.add_argument("--rename-cart", nargs=2, metavar=("OLD", "NEW"), help="rename the cart with the given name in the export")
        else:
            pgroup.set_defaults(insert_cart=None, replace_cart=None, delete_cart=None, rename_cart=None)

        pgroup = parser.add_argument_group("compression options (semi-undocumented)")
        if is_pico8:
            pgroup.add_argument("--keep-compression", action="store_true", help="keep existing compression, instead of re-compressing")
            pgroup.add_argument("--force-compression", action="store_true", help="force code compression even if code fits (when creating png carts)")
            pgroup.add_argument("--old-compression", action="store_true", help="compress with the old pre-v0.2.0 compression scheme")
        else:
            pgroup.set_defaults(keep_compression=False, force_compression=False, old_compression=False)
        pgroup.add_argument("--fast-compression", action="store_true", help="force fast but poor compression (when creating png carts)")
        pgroup.add_argument("--trace-compression", help="trace the compressed symbols and their cost into this file")
        pgroup.add_argument("--trace-input-compression", help="trace the input's compressed symbols and their cost into this file")

        pgroup = parser.add_argument_group("other uninteresting options (semi-undocumented)")
        pgroup.add_argument("--ignore-hints", action="store_true", help="ignore shrinko8 hint comments")
        pgroup.add_argument("--builtin", type=SplitBySeps, action="extend", help=f"treat identifier(s) as a {pico_name} builtin (for minify, lint, etc.)")
        pgroup.add_argument("--not-builtin", type=SplitBySeps, action="extend", help=f"do not treat identifier(s) as a {pico_name} builtin (for minify, lint, etc.)")
        pgroup.add_argument("--export-name", help="name to use for the export (by default, taken from output name)")
        if is_pico8:
            pgroup.add_argument("--global-builtins-only", action="store_true", help="assume all builtins are global, corresponds to pico8's -global_api option")
            pgroup.add_argument("--local-builtin", type=SplitBySeps, action="extend", help="treat identifier(s) as a local builtin (probably no use outside of testing)")
            pgroup.add_argument("--output-sections", type=SplitBySeps, action="extend", help=f"specifies a {sections_desc} to write to the p8")
        else:
            pgroup.set_defaults(global_builtins_only=False, local_builtin=None, output_sections=None)
        
        return parser

    def default_format(input, for_output=False):
        ext = path_extension(input)[1:].lower()
        if ext in CartFormatCls._values and CartFormatCls(ext).is_ext:
            return CartFormatCls(ext)
        elif CartFormatCls.default_dir and path_is_native(input) and (path_is_dir(input) or not path_basename(input)):
            return CartFormatCls.default_dir
        elif for_output:
            return CartFormatCls.default_src
        else:
            return None

    def main_inner(args):
        if args.version and not args.input:
            print(k_version)
            return

        if args.additional_inputs and not args.output:
            args.output = args.additional_inputs[-1] # argparse doesn't support nargs=* followed by nargs=?
            del args.additional_inputs[-1]
        
        if args.in_place:
            if args.output:
                throw("Cannot specify output cart with --in-place")
            args.output = args.input
            if args.input_format and not args.format:
                args.format = args.input_format
            
        if not args.input:
            throw("No input file specified")
        
        if args.delete_cart or args.rename_cart:
            if args.output:
                throw("Only need to specify a single cart when using --delete-cart or --rename-cart")
            args.input, args.output = None, args.input

        if args.input == "-":
            args.input = StdPath("-")
        if args.output == "-":
            args.output = StdPath("-")

        if args.url:
            args.input = URLPath(args.input)
        elif args.bbs:
            args.input = URLPath(get_bbs_cart_url(args.input, lang))
            args.input_format = CartFormatCls.png

        if (not args.lint and not args.count and not args.output and not args.input_count and not args.version and
            not args.list and not args.dump and not args.script and not args.extract):
            throw("No operation (--lint/--count/--script) or output file specified")
        if args.format and not args.output and not args.dump:
            throw("Output should be specified under --format")
        if args.minify and not args.output and not args.count:
            throw("Output (or --count) should be specified under --minify")
        if args.minify and args.keep_compression:
            throw("Can't modify code and keep compression")
        if (args.list or args.dump) and (args.output or args.lint or args.count):
            throw("--list & --dump can't be combined with most other options")
        if (e(args.delete_cart) + e(args.rename_cart) + e(args.insert_cart) + e(args.replace_cart)) > 1:
            throw("Can only specify one of --insert/replace/delete/rename-cart")
            
        if not args.input_format and args.input:
            args.input_format = default_format(args.input)
            if args.in_place and not args.format:
                args.format = args.input_format

        if not args.format and args.output:
            args.format = default_format(args.output, for_output=True)

        if args.lint:
            args.lint = {
                "unused": not args.no_lint_unused,
                "unused-global": not args.no_lint_unused_global,
                "duplicate": not args.no_lint_duplicate,
                "duplicate-global": not args.no_lint_duplicate_global,
                "undefined": not args.no_lint_undefined,
                "globals": args.lint_global or (),
            }
        
        args.focus = []
        if args.focus_chars:
            args.focus.append("chars")
        if args.focus_compressed:
            args.focus.append("compressed")
        if args.focus_tokens:
            args.focus.append("tokens")

        if args.minify or args.minify_safe_only or args.minify_consts_only:
            minify_default = not args.minify_consts_only
            args.minify = {
                "safe-reorder": args.minify_safe_only or args.reorder_safe_only,
                "safe-builtins": args.minify_safe_only or args.builtins_safe_only,
                "lines": minify_default and not args.no_minify_lines,
                "wspace": minify_default and not args.no_minify_spaces,
                "comments": minify_default and not args.no_minify_comments,
                "tokens": minify_default and not args.no_minify_tokens,
                "reorder": minify_default and not args.no_minify_reorder,
                "consts": not args.no_minify_consts,
                "focus": args.focus,
            }

        args.rename = bool(args.minify) and not args.no_minify_rename
        if args.rename:
            if args.no_preserve:
                args.preserve = (args.preserve or []) + [f"!{item}" for item in args.no_preserve]
            if args.rename_members_as_globals:
                args.preserve = (args.preserve or []) + ["*=*.*"]
            args.rename = {
                "safe-only": args.minify_safe_only or args.rename_safe_only,
                "focus": args.focus,
                "rules": args.preserve or (),
            }

        if args.unminify:
            args.unminify = {
                "indent": args.unminify_indent
            }
        
        if args.const or args.str_const:
            if args.const:
                args.const = {name: parse_constant(val, lang) or throw(f"cannot parse const <{val}>. If it's meant to be a string, try using --str-const instead") 
                            for name, val in args.const}
            if args.str_const:
                args.const = args.const or {}
                args.const.update({name: parse_constant(val, lang, as_str=True) for name, val in args.str_const})

        if is_picotron and not args.delete_meta and args.minify and not args.minify_safe_only:
            args.delete_meta = ["*"]

        args.preproc_cb, args.postproc_cb, args.preproc_syntax_cb = None, None, None
        args.sublang_cb = lambda name: find_in_builtin_script(name, "sublanguage_main")
        if args.script:
            for script in args.script:
                preproc_main, postproc_main, preproc_syntax_main, sublang_main = import_from_script_by_path(script,
                    "preprocess_main", "postprocess_main", "preprocess_syntax_main", "sublanguage_main")
                args.preproc_cb = func_union(args.preproc_cb, preproc_main)
                args.postproc_cb = func_union(postproc_main, args.postproc_cb) # (reverse order)
                args.preproc_syntax_cb = func_union(args.preproc_syntax_cb, preproc_syntax_main)
                args.sublang_cb = func_union(sublang_main, args.sublang_cb, return_early=e) # (reverse order)

        base_count_handler = ParsableCountHandler if args.parsable_count else True
        if args.input_count:
            args.input_count = base_count_handler
        if args.count:
            args.count = base_count_handler

        if args.trace_input_compression:
            args.trace_input_compression = CompressionTracer(args.trace_input_compression, lang)
        if args.trace_compression:
            args.trace_compression = CompressionTracer(args.trace_compression, lang)

        if args.input:
            cart, extra_carts = handle_input(args)
            if cart is None: # e.g. list/dump case
                return 0
            
            passed, ok = handle_processing(args, cart, extra_carts)
            if not passed:
                return 2 if ok else 1
            
        else: # output-only operations
            cart, extra_carts = None, ()

        handle_output(args, cart, extra_carts)
    
    class InputDef(Tuple):
        input = format = name = sections = fspath = None

    def handle_input(args):
        allow_extra_input = is_pico8 and args.format and args.format.is_export

        # read the main cart
        extra_carts = []
        try:
            if (is_pico8 and args.list) or args.dump:
                export = read_cart_export_func(args.input, args.input_format)
                if args.list:
                    for entry in export.list_carts():
                        print(entry)
                else:
                    dir_ensure_exists(args.dump)
                    export.dump_contents(args.dump, default(args.format, CartFormatCls.default_src), misc=args.dump_misc_too)
                return None, None

            main_cart = read_cart_func(args.input, args.input_format, size_handler=args.input_count, 
                                       debug_handler=args.trace_input_compression, cart_name=args.cart,
                                       keep_compression=args.keep_compression,
                                       extra_carts=extra_carts if allow_extra_input and not args.cart else None)
        except OSError as err:
            throw(f"cannot read cart: {err}")
        
        # collect additional carts to read
        if args.additional_inputs:
            if not args.extra_input:
                args.extra_input = []
            for input in args.additional_inputs:
                args.extra_input.append((input,))

        extra_inputs = []
        if args.extra_input:
            if not allow_extra_input:
                throw("--extra-input can only be used when creating exports")
            
            for extra in args.extra_input:
                if len(extra) == 1:
                    extra_inputs.append(InputDef(extra[0], default_format(extra[0], for_output=True)))
                elif 3 >= len(extra) >= 2:
                    extra_inputs.append(InputDef(extra[0], CartFormatCls(extra[1]), name=list_get(extra, 2)))
                else:
                    throw("too many arguments to --extra-output")
        
        if args.insert:
            for insert in args.insert:
                if len(insert) == 1:
                    extra_inputs.append(InputDef(insert[0], CartFormatCls.fs, fspath=path_basename(insert[0])))
                elif len(insert) == 2:
                    extra_inputs.append(InputDef(insert[0], CartFormatCls.fs, fspath=insert[1]))
                elif len(insert) == 3:
                    extra_inputs.append(InputDef(insert[0], CartFormatCls.fs, fspath=insert[1], sections=SplitBySeps(insert[2])))
                else:
                    throw("too many arguments to --insert (must be 1 through 3)")

        if args.merge:
            for merge in args.merge:
                if len(merge) == 2:
                    extra_inputs.append(InputDef(merge[0], default_format(merge[0]), sections=SplitBySeps(merge[1])))
                elif len(merge) == 3:
                    extra_inputs.append(InputDef(merge[0], CartFormatCls(merge[2]), sections=SplitBySeps(merge[1])))
                else:
                    throw("too many or few arguments to --merge (must be 2 or 3)")
        
        if args.label:
            extra_inputs.append(InputDef(args.label, CartFormatCls.label, sections=(label_section,)))
        if args.title:
            main_cart.set_raw_title(args.title)

        # read additional carts
        for input, input_format, input_name, merge_sections, fspath in extra_inputs:
            cart = read_cart_func(input, input_format, fspath=fspath, sections=merge_sections,
                                  keep_compression=args.keep_compression)
            
            if input_name:
                cart.name = input_name
            
            if e(merge_sections) or e(fspath):
                merge_cart_func(main_cart, cart, merge_sections)
            else:
                extra_carts.append(cart)
        
        if is_picotron and args.list:
            for path in main_cart.files:
                print(path)
            return None, None

        return main_cart, extra_carts

    def handle_processing(args, main_cart, extra_carts):
        had_warns = False

        for cart in itertools.chain((main_cart,), extra_carts):
            if args.update_version:
                cart.set_version(get_default_version_func())
            elif e(args.output_version):
                cart.set_version(args.output_version)
        
            if args.filter:
                filter_cart_func(cart, args.filter)

            if is_picotron:
                preproc_cart_func(cart, delete_meta=args.delete_meta,
                                  delete_label=default(args.delete_label, args.format == CartFormatCls.png),
                                  keep_pod_compression=args.keep_pod_compression,
                                  uncompress_pods=args.uncompress_pods, base64_pods=args.base64_pods,
                                  # binary formats are already compressed, so pod compression just hurts
                                  need_pod_compression=args.format and args.format.is_src)

            src = CartSourceCls(cart, args.code_sections)
            
            if args.input_count:
                write_code_size_func(cart, handler=args.input_count, input=True)
                
            ctxt = ContextCls(extra_builtins=args.builtin, not_builtins=args.not_builtin, 
                              use_local_builtins=not args.global_builtins_only,
                              extra_local_builtins=args.local_builtin,
                              srcmap=args.rename_map, sublang_getter=args.sublang_cb, version=cart.version_id,
                              hint_comments=not args.ignore_hints, consts=args.const)
            if args.preproc_cb:
                args.preproc_cb(cart=cart, src=src, ctxt=ctxt, args=args)

            def preproc_syntax_call(root, on_error):
                args.preproc_syntax_cb(cart=cart, src=src, root=root, on_error=on_error, ctxt=ctxt, args=args)

            ok, errors = process_code(ctxt, src,
                                      input_count=is_pico8 and args.input_count,
                                      count=is_pico8 and args.count,
                                      lint=args.lint, minify=args.minify, rename=args.rename,
                                      unminify=args.unminify, stop_on_lint=not args.no_lint_fail,
                                      count_is_optional=args.no_count_tokenize,
                                      preproc=preproc_syntax_call if args.preproc_syntax_cb else None)
            if errors:
                had_warns = True

                if not ok:
                    print("Compilation errors:")
                elif args.lint:
                    print("Lint warnings:")
                else:
                    print("Hint usage warnings:")
                
                for error in sorted(errors):
                    print(error.format(args.error_format))
                
                if not ok or (args.lint and not args.no_lint_fail):
                    return False, ok

            if args.rename_map:
                file_write_maybe_text(args.rename_map, "\n".join(ctxt.srcmap))
                
            if args.postproc_cb:
                args.postproc_cb(cart=cart, args=args)
            
            if args.count:
                write_code_size_func(cart, handler=args.count)
                if not (args.output and not args.format.is_src) and not args.no_count_compress: # else, will be done in write_cart
                    write_compressed_size_func(cart, handler=args.count, fast_compress=args.fast_compression, debug_handler=args.trace_compression)
            
            if args.version:
                write_cart_version_func(cart)
        
        return True, not had_warns

    class OutputDef(Tuple):
        output = format = fspath = None

    def handle_output(args, cart, extra_carts):
        if e(args.insert_cart):
            output_cart_op = ListOp.insert
            output_cart_name, output_cart_target = list_unpack(args.insert_cart, 2)
        elif e(args.replace_cart):
            output_cart_op = ListOp.replace
            output_cart_name, output_cart_target = list_unpack(args.replace_cart, 2)
        elif e(args.delete_cart):
            output_cart_op = ListOp.delete
            output_cart_name, output_cart_target = list_unpack(args.delete_cart, 2)
        elif e(args.rename_cart):
            output_cart_op = ListOp.rename
            output_cart_name, output_cart_target = list_unpack(args.rename_cart, 2)
        else:
            output_cart_op = output_cart_target = None
            output_cart_name = args.output_cart

        all_outputs = []
        if args.output:
            all_outputs.append(OutputDef(args.output, args.format))
        
        if args.extra_output:
            for extra in args.extra_output:
                if len(extra) == 1:
                    all_outputs.append(OutputDef(extra[0], default_format(extra[0], for_output=True)))
                elif len(extra) == 2:
                    all_outputs.append(OutputDef(extra[0], CartFormatCls(extra[1])))
                else:
                    throw("too many arguments to --extra-output (must be 1 or 2)")
        
        if args.extract:
            for extract in args.extract:
                if len(extract) == 1:
                    all_outputs.append(OutputDef(path_basename(extract[0]), CartFormatCls.fs, extract[0]))
                elif len(extract) == 2:
                    all_outputs.append(OutputDef(extract[1], CartFormatCls.fs, extract[0]))
                else:
                    throw("too many arguments to --extract (must be 1 or 2)")

        for output, format, fspath in all_outputs:
            target_export, pico_dat = None, None
            if format.is_export:
                if e(output_cart_op):
                    try:
                        target_export = read_cart_export_func(output, format)
                    except OSError as err:
                        throw(f"cannot read export for editing: {err}")
                else:
                    if not args.pico_dat:
                        throw(f"Creating a new export requires passing --{pico_name}-dat <path to {pico_name}.dat>")
                    try:
                        pico_dat = read_pico_dat_func(args.pico_dat)
                    except OSError as err:
                        throw(f"cannot read {pico_name} dat: {err}")

            try:
                write_cart_func(output, cart, format, extra_carts=extra_carts, fspath=fspath,
                                size_handler=args.count, debug_handler=args.trace_compression,
                                unicode_caps=args.unicode_caps, old_compress=args.old_compression,
                                force_compress=args.count or args.force_compression,
                                fast_compress=args.fast_compression, keep_compression=args.keep_compression,
                                template_image=args.template_image, template_only=args.template_only,
                                sections=args.output_sections, avoid_base64=args.avoid_base64,
                                cart_op=output_cart_op, cart_name=output_cart_name, target_name=output_cart_target,
                                target_export=target_export, export_name=args.export_name, pico_dat=pico_dat)
            except OSError as err:
                throw(f"cannot write cart: {err}")

    parser = create_parser()

    def main(raw_args=None):
        try:
            raw_args = default(raw_args, sys.argv[1:])

            if not raw_args: # help is better than usage
                parser.print_help(sys.stderr)
                return 1

            args = parser.parse_intermixed_args(raw_args)
            return main_inner(args)
        except CheckError as err:
            sys.stdout.flush()
            eprint("ERROR: " + str(err))
            return 1
    return main

if __name__ == "__main__":
    eprint("The correct script to run is shrinko8.py (or shrinkotron.py)")
