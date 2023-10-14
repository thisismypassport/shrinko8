#!/usr/bin/env python3
from test_utils import *
from pico_cart import get_bbs_cart_url
from threading import Thread
import argparse
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
parser.add_argument("--unminify", action="store_true", help="test unminify instead of minify")
parser.add_argument("-ot", "--focus-tokens", action="store_true", help="focus on token count")
parser.add_argument("-oc", "--focus-chars", action="store_true", help="focus on char count")
parser.add_argument("-ob", "--focus-compressed", action="store_true", help="focus on compressed size")
parser.add_argument("-oa", "--focus-all", action="store_true", help="test all focuses")
parser.add_argument("-i", "--compare-input", action="store_true", help="compare results vs the inputs too")
parser.add_argument("-u", "--compare-unfocused", action="store_true", help="compare results vs the unfocused results too")
parser.add_argument("-v", "--verbose", action="store_true", help="print changes in individual carts")
parser.add_argument("-x", "--exe", action="store_true", help="use a packaged exe instead of the python script")
parser.add_argument("-p", "--pico8", action="append", help="specify a pico8 exe to test the results with")
parser.add_argument("-P", "--no-pico8", action="store_true", help="disable running pico8 even if exe is supplied (for convenience)")
parser.add_argument("-t", "--pico8-time", type=float, help="how long to run pico8 carts for")
parser.add_argument("-T", "--pico8-interact", action="store_true", help="show real pico8 windows and randomly interact with them (windows-only!)")
parser.add_argument("-j", "--parallel-jobs", type=int, help="how many processes to run in parallel")
parser.add_argument("--profile", action="store_true", help="enable profiling")
g_opts = parser.parse_args()

if not g_opts.pico8_time:
    g_opts.pico8_time = 8.0 if g_opts.pico8_interact else 2.0

if g_opts.carts_file and not g_opts.carts:
    g_opts.carts = file_read_text(g_opts.carts_file).splitlines()

if not g_opts.carts:
    raise Exception("no carts specified!")

if g_opts.input_redownload:
    g_opts.input_reprocess = True

if not g_opts.parallel_jobs:
    g_opts.parallel_jobs = mp.cpu_count()

g_opts.all = not g_opts.only_compress and not g_opts.only_safe_minify and not g_opts.only_unsafe_minify and not g_opts.none

class DeltaInfoDictionary(defaultdict):
    class Info(Struct):
        sum = min = max = count = 0
        pos_sum = neg_sum = 0
        min_ref = max_ref = None
        
        def apply(m, value, ref):
            m.sum += value
            m.count += 1
            m.min = min(m.min, value)
            m.max = max(m.max, value)
            if m.min == value:
                m.min_ref = ref
            if m.max == value:
                m.max_ref = ref
            if value >= 0:
                m.pos_sum += value
            else:
                m.neg_sum += value

        def apply_info(m, info):
            m.sum += info.sum
            m.count += info.count
            m.min = min(m.min, info.min)
            m.max = max(m.max, info.max)
            if m.min == info.min:
                m.min_ref = info.min_ref
            if m.max == info.max:
                m.max_ref = info.max_ref
            m.pos_sum += info.pos_sum
            m.neg_sum += info.neg_sum

        @property
        def average(m):
            return m.sum / m.count
        
        @property
        def pos_average(m):
            return m.pos_sum / m.count
        
        @property
        def neg_average(m):
            return m.neg_sum / m.count

    def __missing__(m, key):
        info = m.Info()
        m[key] = info
        return info

    def apply(m, key, value, ref):
        m[key].apply(value, ref)
    
    def apply_dictionary(m, other):
        for key, info in other.items():
            m[key].apply_info(info)

def check_run(name, result, parse_meta=False):
    success, stdout = result
    if "SHORT" in stdout:
        print(name, stdout)
    if not success:
        print(f"Run {name} failed. Stdout:\n{stdout}")
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
    init_tests(opts)

def run_for_cart(args):
    (cart, cart_input, cart_output, cart_compare, cart_unfocused, focus) = args
    
    short_prefix = "c" if focus == "chars" else "b" if focus == "compressed" else "t" if focus == "tokens" else ""

    basepath = path_join("test_bbs", cart)
    download_path = basepath + ".dl.png"
    uncompress_path = basepath + ".dp.p8"
    compress_path = basepath + ".c.png"
    safe_minify_path = basepath + f".{short_prefix}sm.png" 
    unsafe_minify_path = basepath + f".{short_prefix}um.png"
    unminify_path = basepath + ".un.p8"

    if g_opts.input_redownload or not path_exists(download_path):
        file_write(download_path, file_read(URLPath(get_bbs_cart_url("#" + cart))))
    elif g_opts.new_only:
        return None

    new_cart_input = None
    if g_opts.input_reprocess or not cart_input:
        process_results = run_code(download_path, uncompress_path, "--input-count", "--parsable-count", "--version")
        new_cart_input = cart_input = check_run(f"{cart}.process", process_results, parse_meta=True)
    
    if not cart_output:
        cart_output = {}
    deltas = DeltaInfoDictionary()

    def process_compare(kind, output, compare, ignore_partial=False):
        for key in compare.keys() | output.keys():
            outval, cmpval = output.get(key), compare.get(key)
            if outval is None:
                if not ignore_partial:
                    print(f"Missing key {key} in output of {cart}:{kind}")
                    fail_test()
            elif cmpval is None:
                if not ignore_partial:
                    print(f"New key {key} in output of {cart}:{kind}")
            else:
                if g_opts.verbose and outval != cmpval:
                    if outval < cmpval:
                        print(f"Improvement of {cmpval - outval} in {cart}:{kind}:{key}")
                    else:
                        print(f"Regression of {outval - cmpval} in {cart}:{kind}:{key}")
                deltas.apply(f"{kind}.{key}", outval - cmpval, cart)

    def process_output(kind, output):
        if output is None:
            return # already printed about this

        cart_output[kind] = output
        if cart_compare and kind in cart_compare:
            process_compare(kind, output, cart_compare[kind])
        else:
            print(f"No comparison info of {cart}.{kind}")
            fail_test()
        
        if g_opts.compare_input:
            process_compare(kind + "-vs-input", output, cart_input, ignore_partial=True)

        if g_opts.compare_unfocused:
            process_compare(kind + "-vs-unfocused", output, cart_unfocused[kind])

    best_path_for_pico8 = download_path
    start_test()

    if g_opts.unminify:
        unminify_results = run_code(uncompress_path, unminify_path, "--unminify")
        check_run(f"{cart}:unminify", unminify_results)
        best_path_for_pico8 = unminify_path
    
    else:
        if g_opts.all or g_opts.only_compress:
            compress_results = run_code(uncompress_path, compress_path, "--count", "--parsable-count", "--no-count-tokenize")
            process_output("compress", check_run(f"{cart}:compress", compress_results, parse_meta=True))
            best_path_for_pico8 = compress_path

        minify_opts = [f"--focus-{focus}"] if focus else []
        
        if g_opts.all or g_opts.only_safe_minify:
            safe_minify_results = run_code(uncompress_path, safe_minify_path, "--minify-safe-only", "--count", "--parsable-count", *minify_opts)
            process_output("safe_minify", check_run(f"{cart}:safe_minify", safe_minify_results, parse_meta=True))
            best_path_for_pico8 = safe_minify_path
        
        if g_opts.all or g_opts.only_unsafe_minify:
            unsafe_minify_results = run_code(uncompress_path, unsafe_minify_path, "--minify", "--count", "--parsable-count", *minify_opts)
            process_output("unsafe_minify", check_run(f"{cart}:unsafe_minify", unsafe_minify_results, parse_meta=True))

    return (cart, get_test_results(), new_cart_input, cart_output, deltas, best_path_for_pico8)

def interact_with_pico8s():
    import win32api, win32gui, win32process, win32con as wc, pywintypes # type: ignore

    pico8_paths = set(path_normalize(pico8) for pico8 in g_opts.pico8)

    pico8_keys = [wc.VK_LEFT, wc.VK_RIGHT, wc.VK_UP, wc.VK_DOWN, ord('X'), ord('Z')]
    pico8_key_counts = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 3, 3, 4]
    prev_hwnd_data = defaultdict(lambda: Dynamic(keys=[], pid=None))

    wc_MAPVK_VK_TO_VSC_EX = 4 # missing...

    def send_key(key, state):
        scode = win32api.MapVirtualKey(key, wc_MAPVK_VK_TO_VSC_EX)
        flags = 0 if state else wc.KEYEVENTF_KEYUP
        if scode >= 0x100:
            flags |= wc.KEYEVENTF_EXTENDEDKEY
            scope >>= 8
        win32api.keybd_event(key, scode, flags, 0)

    while True:
        # activate a random pico8 window
        pico8_windows = []

        def on_window(hwnd, _):
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc = win32api.OpenProcess(wc.PROCESS_QUERY_INFORMATION | wc.PROCESS_VM_READ, False, pid)
                if proc:
                    try:
                        ppath = win32process.GetModuleFileNameEx(proc, None)
                    finally:
                        proc.close()

                    if ppath and path_normalize(ppath) in pico8_paths:

                        if prev_hwnd_data[hwnd].pid != pid: # just in case?
                            prev_hwnd_data[hwnd].keys.clear()
                            prev_hwnd_data[hwnd].pid = pid

                        pico8_windows.append(hwnd)
            except pywintypes.error:
                pass # e.g. can't access hwnd, or hwnd/process died

        win32gui.EnumWindows(on_window, None)

        if pico8_windows:
            hwnd = random.choice(pico8_windows)
            try:
                win32gui.SetForegroundWindow(hwnd)
            except pywintypes.error:
                pass # e.g. hwnd died
            else:
                key_count = random.choice(pico8_key_counts)
                keys = random.sample(pico8_keys, k=key_count)
                prev_keys = prev_hwnd_data[hwnd].keys

                for key in prev_keys:
                    if key not in keys:
                        send_key(key, False)
                for key in keys:
                    if key not in prev_keys:
                        send_key(key, True)

        time.sleep(0.05)

def run(focus):
    prefix = f"{focus}_" if focus else ""

    input_json = path_join("test_bbs", "input.json")
    output_json = path_join("test_bbs", prefix + "output.json")
    compare_json = path_join("test_bbs", prefix + "compare.json")
    unfocused_json = path_join("test_bbs", "compare.json") if g_opts.compare_unfocused else None
    inputs = try_file_read_json(input_json, {})
    outputs = try_file_read_json(output_json, {})
    compares = try_file_read_json(compare_json, {})
    unfocuseds = try_file_read_json(unfocused_json, {}) if unfocused_json else {}
    deltas = DeltaInfoDictionary()

    if g_opts.pico8_interact:
        Thread(target=interact_with_pico8s, daemon=True).start()

    with mp.Pool(g_opts.parallel_jobs, init_for_process, (g_opts,)) as mp_pool, \
         mt.Pool(g_opts.parallel_jobs) as mt_pool:
        
        p8_results = []
        mp_inputs = [(cart, inputs.get(cart), outputs.get(cart), compares.get(cart), unfocuseds.get(cart), focus) for cart in g_opts.carts]
        for mp_result in mp_pool.imap_unordered(run_for_cart, mp_inputs):
            if not mp_result:
                continue

            (cart, test_results, new_cart_input, cart_output, cart_deltas, cart_pico8_path) = mp_result
            add_test_results(test_results)
            if new_cart_input:
                inputs[cart] = new_cart_input
            outputs[cart] = cart_output
            deltas.apply_dictionary(cart_deltas)
            
            if cart_pico8_path and g_opts.pico8 and not g_opts.no_pico8:
                for pico8 in g_opts.pico8:
                    def run(pico8=pico8, path=cart_pico8_path):
                        return run_pico8(pico8, path, allow_timeout=True, timeout=g_opts.pico8_time, with_window=g_opts.pico8_interact)

                    p8_results.append(mt_pool.apply_async(run))

        for p8_result in p8_results:
            check_run(f"{cart}:p8-run", p8_result.get())

    file_write_json(input_json, inputs, sort_keys=True, indent=4)
    file_write_json(output_json, outputs, sort_keys=True, indent=4)

    for key, info in sorted(deltas.items()):
        if not info.min and not info.max:
            continue
        
        if info.sum <= 0:
            print(f"{key} improved by {-info.sum} in total ({-info.average:.2f} average)")
        else:
            print(f"WARNING: {key} regressed by {info.sum} in total ({info.average:.2f} average)")

        if info.min:
            print(f"    {-info.min} max improvement [@{info.min_ref}], {-info.neg_average:.2f} improvement average")
        if info.max:
            print(f"    WARNING: {info.max} max regression [@{info.max_ref}], {info.pos_average:.2f} regression average")

def run_all():
    if g_opts.focus_all:
        for focus in [None, "tokens", "chars", "compressed"]:
            print(f"Focus {focus}:")
            run(focus)
    else:
        focus = "chars" if g_opts.focus_chars else "compressed" if g_opts.focus_compressed else "tokens" if g_opts.focus_tokens else None
        run(focus)

if __name__ == "__main__":
    init_tests(g_opts)
    dir_ensure_exists("test_bbs")
    run_all()
    sys.exit(end_tests())
