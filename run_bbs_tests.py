#!/usr/bin/env python3
from test_utils import *
from pico_cart import get_bbs_cart_url
import argparse, threading
import multiprocessing as mp
import multiprocessing.dummy as mt

def CommaSep(val):
    return val.split(",")

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--carts", type=CommaSep, help="specify a specific cart or carts to run on (overrides -f)")
parser.add_argument("-f", "--carts-file", help="specify which carts to run on via a file", default="private_bbs_tests.lst")
parser.add_argument("-n", "--new-only", action="store_true", help="only test new carts")
parser.add_argument("--input-redownload", action="store_true", help="download the carts again")
parser.add_argument("--input-reprocess", action="store_true", help="process the downloaded carts again (count sizes and convert to p8)")
parser.add_argument("--only-compress", action="store_true", help="only test compression")
parser.add_argument("--only-safe-minify", action="store_true", help="only test safe minification")
parser.add_argument("--only-unsafe-minify", action="store_true", help="only test unsafe minification")
parser.add_argument("--none", action="store_true", help="do not test anything (allows running pico8 against input)")
parser.add_argument("-oc", "--focus-chars", action="store_true", help="focus on char count")
parser.add_argument("-ob", "--focus-compressed", action="store_true", help="focus on compressed size")
parser.add_argument("-oa", "--focus-all", action="store_true", help="test all focuses")
parser.add_argument("-i", "--compare-input", action="store_true", help="compare results vs the inputs too")
parser.add_argument("-u", "--compare-unfocused", action="store_true", help="compare results vs the unfocused results too")
parser.add_argument("-v", "--verbose", action="store_true", help="print changes in individual carts")
parser.add_argument("-x", "--exe", action="store_true", help="use a packaged exe instead of the python script")
parser.add_argument("-p", "--pico8", action="append", help="specify a pico8 exe to test the results with")
parser.add_argument("--pico8-time", type=float, help="how long to run pico8 carts for", default=2.0)
parser.add_argument("-P", "--no-pico8", action="store_true", help="disable running pico8 even if exe is supplied (for convenience)")
parser.add_argument("-j", "--parallel-jobs", type=int, help="how many processes to run in parallel")
g_opts = parser.parse_args()

if g_opts.carts_file and not g_opts.carts:
    g_opts.carts = file_read_text(g_opts.carts_file).splitlines()

if not g_opts.carts:
    raise Exception("no carts specified!")

if g_opts.input_redownload:
    g_opts.input_reprocess = True

if not g_opts.parallel_jobs:
    g_opts.parallel_jobs = mp.cpu_count()

g_opts.all = not g_opts.only_compress and not g_opts.only_safe_minify and not g_opts.only_unsafe_minify and not g_opts.none

class DeltaInfoDictionary(defaultdict): # keeps sum, min, max
    class Info:
        __slots__ = ('sum', 'min', 'max', 'count')
        def __init__(m):
            m.sum = m.min = m.max = m.count = 0
        def apply(m, value):
            m.sum += value
            m.count += 1
            m.min = min(m.min, value)
            m.max = max(m.max, value)
        def apply_info(m, info):
            m.sum += info.sum
            m.count += info.count
            m.min = min(m.min, info.min)
            m.max = max(m.max, info.max)

        @property
        def average(m):
            return m.sum / m.count

    def __missing__(m, key):
        info = m.Info()
        m[key] = info
        return info

    def apply(m, key, value):
        m[key].apply(value)
    
    def apply_dictionary(m, other):
        for key, info in other.items():
            m[key].apply_info(info)

def check_run(name, result, parse_meta=False):
    success, stdout = result
    if not success:
        print("Run %s failed. Stdout:\n%s" % (name, stdout))
        fail_test()
        return None
    
    if parse_meta:
        meta = {}
        for line in stdout.splitlines():
            if line.startswith("count:"):
                split = line.split(":")
                meta[split[2]] = int(split[3])
            if line.startswith("version:"):
                meta["version"] = str_after_first(line, ":").strip()
        return meta

def init_for_process(opts):
    global g_opts
    g_opts = opts
    init_tests(opts.exe)

def run_for_cart(args):
    (cart, cart_input, cart_output, cart_compare, cart_unfocused, focus) = args
    
    short_prefix = "c" if focus == "chars" else "b" if focus == "compressed" else ""

    basepath = path_join("test_bbs", cart)
    download_path = basepath + ".dl.png"
    uncompress_path = basepath + ".dp.p8"
    compress_path = basepath + ".c.png"
    safe_minify_path = basepath + ".%ssm.png" % short_prefix
    unsafe_minify_path = basepath + ".%sum.png" % short_prefix

    if g_opts.input_redownload or not path_exists(download_path):
        file_write(download_path, file_read(URLPath(get_bbs_cart_url("#" + cart))))
    elif g_opts.new_only:
        return None

    new_cart_input = None
    if g_opts.input_reprocess or not cart_input:
        process_results = run_code(download_path, uncompress_path, "--input-count", "--parsable-count", "--version")
        new_cart_input = cart_input = check_run("%s.process" % cart, process_results, parse_meta=True)
    
    if not cart_output:
        cart_output = {}
    deltas = DeltaInfoDictionary()

    def process_compare(kind, output, compare, ignore_partial=False):
        for key in compare.keys() | output.keys():
            outval, cmpval = output.get(key), compare.get(key)
            if outval is None:
                if not ignore_partial:
                    print("Missing key %s in output of %s:%s" % (key, cart, kind))
                    fail_test()
            elif cmpval is None:
                if not ignore_partial:
                    print("New key %s in output of %s:%s" % (key, cart, kind))
            elif outval != cmpval:
                if g_opts.verbose:
                    if outval < cmpval:
                        print("Improvement of %d in %s:%s:%s" % (cmpval - outval, cart, kind, key))
                    else:
                        print("Regression of %d in %s:%s:%s" % (outval - cmpval, cart, kind, key))
                deltas.apply("%s.%s" % (kind, key), outval - cmpval)

    def process_output(kind, output):
        cart_output[kind] = output
        if cart_compare and kind in cart_compare:
            process_compare(kind, output, cart_compare[kind])
        else:
            print("No comparison info of %s.%s" % (cart, kind))
            fail_test()
        
        if g_opts.compare_input:
            process_compare(kind + "-vs-input", output, cart_input, ignore_partial=True)

        if g_opts.compare_unfocused:
            process_compare(kind + "-vs-unfocused", output, cart_unfocused[kind])

    best_path_for_pico8 = download_path
    
    if g_opts.all or g_opts.only_compress:
        compress_results = run_code(uncompress_path, compress_path, "--count", "--parsable-count", "--no-count-tokenize")
        process_output("compress", check_run("%s:compress" % cart, compress_results, parse_meta=True))
        best_path_for_pico8 = compress_path

    minify_opts = ["--focus-%s" % focus] if focus else []
    
    if g_opts.all or g_opts.only_safe_minify:
        safe_minify_results = run_code(uncompress_path, safe_minify_path, "--minify-safe-only", "--count", "--parsable-count", *minify_opts)
        process_output("safe_minify", check_run("%s:safe_minify" % cart, safe_minify_results, parse_meta=True))
        best_path_for_pico8 = safe_minify_path
    
    if g_opts.all or g_opts.only_unsafe_minify:
        unsafe_minify_results = run_code(uncompress_path, unsafe_minify_path, "--minify", "--count", "--parsable-count", *minify_opts)
        process_output("unsafe_minify", check_run("%s:unsafe_minify" % cart, unsafe_minify_results, parse_meta=True))

    return (cart, is_fail_test(), new_cart_input, cart_output, deltas, best_path_for_pico8)

def run(focus):
    prefix = "%s_" % focus if focus else ""

    input_json = path_join("test_bbs", "input.json")
    output_json = path_join("test_bbs", prefix + "output.json")
    compare_json = path_join("test_bbs", prefix + "compare.json")
    unfocused_json = path_join("test_bbs", "compare.json") if g_opts.compare_unfocused else None
    inputs = try_file_read_json(input_json, {})
    outputs = try_file_read_json(output_json, {})
    compares = try_file_read_json(compare_json, {})
    unfocuseds = try_file_read_json(unfocused_json, {}) if unfocused_json else {}
    deltas = DeltaInfoDictionary()

    with mp.Pool(g_opts.parallel_jobs, init_for_process, (g_opts,)) as mp_pool, \
         mt.Pool(g_opts.parallel_jobs) as mt_pool:
        
        p8_results = []
        mp_inputs = [(cart, inputs.get(cart), outputs.get(cart), compares.get(cart), unfocuseds.get(cart), focus) for cart in g_opts.carts]
        for mp_result in mp_pool.imap_unordered(run_for_cart, mp_inputs):
            if not mp_result:
                continue

            (cart, is_fail, new_cart_input, cart_output, cart_deltas, cart_pico8_path) = mp_result
            if is_fail:
                fail_test()
            if new_cart_input:
                inputs[cart] = new_cart_input
            outputs[cart] = cart_output
            deltas.apply_dictionary(cart_deltas)
            
            if cart_pico8_path and g_opts.pico8 and not g_opts.no_pico8:
                for pico8 in g_opts.pico8:
                    p8_results.append(mt_pool.apply_async(lambda: run_pico8(pico8, cart_pico8_path, timeout=g_opts.pico8_time, allow_timeout=True)))

        for p8_result in p8_results:
            check_run("%s:p8-run" % cart, p8_result.get())

    file_write_json(input_json, inputs, sort_keys=True, indent=4)
    file_write_json(output_json, outputs, sort_keys=True, indent=4)

    for key, info in sorted(deltas.items()):
        extra_print = []
        if info.min:
            extra_print.append("%d max improvement" % -info.min)
        if info.max:
            extra_print.append("WARNING: %d max regression" % info.max)
        
        if info.sum <= 0:
            print("%s improved by %d in total (%f average, %s)" % (key, -info.sum, -info.average, ", ".join(extra_print)))
        else:
            print("WARNING: %s regressed by %d in total (%f average, %s)" % (key, info.sum, info.average, ", ".join(extra_print)))

def run_all():
    if g_opts.focus_all:
        for focus in [None, "chars", "compressed"]:
            print("Focus %s:" % focus)
            run(focus)
    else:
        focus = "chars" if g_opts.focus_chars else "compressed" if g_opts.focus_compressed else None
        run(focus)

if __name__ == "__main__":
    init_tests(g_opts.exe)
    os.makedirs("test_bbs", exist_ok=True)
    run_all()
    exit_tests()
