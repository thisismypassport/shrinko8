#!/usr/bin/env python3
from test_utils import *
import argparse, fnmatch

parser = argparse.ArgumentParser()
parser.add_argument("--measure", action="store_true", help="print the input/output counts for successful tests")
parser.add_argument("--no-measure", action="store_true", help="don't print the input/output counts for failed tests")
parser.add_argument("--stdout", action="store_true", help="print the stdout of shrinko8 while running the tests")
parser.add_argument("-t", "--test", action="append", help="specify a specific test to run, optionally with wildcards")
parser.add_argument("--test-from", help="specify a specific test to start running from")
parser.add_argument("--no-private", action="store_true", help="do not run private tests, if they exist")
parser.add_argument("-v", "--verbose", action="store_true", help="print test successes")
parser.add_argument("-x", "--exe", action="store_true", help="test a packaged exe instead of the python script")
parser.add_argument("-p", "--pico8", action="append", help="specify a pico8 exe to test the results with")
parser.add_argument("-P", "--no-pico8", action="store_true", help="disable running pico8 even if exe is supplied (for convenience)")
parser.add_argument("--profile", action="store_true", help="enable profiling")

# for test consistency:
os.environ["PICO8_EXPORT_REPRO_TIME"] = '1577934245'
os.environ["PICO8_PLATFORM_CHAR"] = 'w'

def norm_paths(output):
    return output.replace("\\", "/")

def measure(kind, path, input=False):
    print(f"Measuring {kind}...")
    if path_exists(path):
        _, stdout = run_code(path, "--input-count" if input else "--count")
        print(stdout, end="")
    else:
        print("MISSING!")

def try_read_dir_contents(dir):
    results = []
    for name in sorted(try_dir_names(dir, ())):
        child = path_join(dir, name)
        if path_is_dir(child):
            results.append((name, try_read_dir_contents(child)))
        else:
            results.append((name, try_file_read(child)))
    return results

def run_test(name, input, output, *args, private=False, check_output=True, from_output=False,
             stdout_output=None, norm_stdout=nop, exit_code=0, extra_outputs=None, output_reader=try_file_read,
             pico8_output_val=None, pico8_output=None, pico8_run=None, copy_in_to_out=False, update_version=True):
    if g_opts.test:
        for wanted_test in g_opts.test:
            if fnmatch.fnmatch(name, wanted_test):
                break
        else:
            return None
    if g_opts.test_from:
        if name == g_opts.test_from:
            g_opts.test_from = None
        else:
            return None

    start_test()
    prefix = "private_" if private else ""
    inpath = path_join(prefix + ("test_output" if from_output else "test_input"), input)
    if output:
        outpath = path_join(prefix + "test_output", output)
        cmppath = path_join(prefix + "test_compare", output)

    if copy_in_to_out:
        file_write(outpath, file_read(path_join(path_dirname(inpath), output)))

    if update_version:
        args += ("--update-version",)

    if not input:
        args = (outpath,) + args
    elif not output:
        args = (inpath,) + args
    else:
        args = (inpath, outpath) + args

    run_success, run_stdout = run_code(*args, exit_code=exit_code)
    success = run_success
    stdouts = [run_stdout]

    if run_success and output and check_output:
        if output_reader(outpath) != output_reader(cmppath):
            stdouts.append(f"ERROR: Output difference: {outpath}, {cmppath}")
            success = False

    if run_success and stdout_output:
        stdout_outpath = path_join(prefix + "test_output", stdout_output)
        stdout_cmppath = path_join(prefix + "test_compare", stdout_output)
        run_stdout = norm_stdout(run_stdout)
        file_write_text(stdout_outpath, run_stdout)
        if run_stdout != try_file_read_text(stdout_cmppath):
            stdouts.append(f"ERROR: Stdout difference: {stdout_outpath}, {stdout_cmppath}")
            success = False

    if run_success and extra_outputs:
        for extra_output in extra_outputs:
            extra_outpath = path_join(prefix + "test_output", extra_output)
            extra_cmppath = path_join(prefix + "test_compare", extra_output)
            if try_file_read(extra_outpath) != try_file_read(extra_cmppath):
                stdouts.append(f"ERROR: Extra output difference: {extra_outpath}, {extra_cmppath}")
                success = False

    if run_success and g_opts.pico8 and not g_opts.no_pico8 and (pico8_output != None or pico8_output_val != None or pico8_run):
        if pico8_output_val is None and pico8_output != None:
            pico8_output_val = file_read_text(path_join(prefix + "test_compare", pico8_output))
        for pico8_exe in g_opts.pico8:
            p8_success, p8_stdout = run_pico8(pico8_exe, outpath, expected_printh=pico8_output_val)
            if not p8_success:
                stdouts.append(f"ERROR: Pico8 run failure with {pico8_exe}")
                stdouts.append(p8_stdout)
                success = False

    stdout = "\n".join(stdouts)

    if not success:
        print(f"\nERROR - test {name} failed")
        print(f"Args: {args}")
        print(stdout)
        if output and not g_opts.no_measure:
            measure("new", outpath)
            measure("old", cmppath)
        fail_test()
        return False
    elif g_opts.measure:
        print(f"\nMeasuring {name}")
        measure("in", inpath, input=True)
        measure("out", outpath)
    elif g_opts.verbose:
        print(f"\nTest {name} succeeded")
    if g_opts.stdout:
        print(stdout)
    return True

def run():
    if run_test("minify", "input.p8", "output.p8", "--minify", "--no-minify-consts",
                "--preserve", "*.preserved_key,preserved_glob,preserving_obj.*", pico8_output="output.p8.printh"):
        run_test("unminify", "output.p8", "input-un.p8", "--unminify",
                 from_output=True, pico8_output="output.p8.printh")
    run_test("minifysimp", "input.p8", "output-simp.p8", "--minify",
             "--preserve", "*.preserved_key,preserved_glob,preserving_obj.*", pico8_output="output.p8.printh")
    run_test("semiobfuscate", "input.p8", "output_semiob.p8", "--minify", "--no-minify-consts",
             "--preserve", "*.*,preserved_glob",
             "--no-minify-spaces", "--no-minify-lines", pico8_output="output.p8.printh")
    run_test("minrename", "input.p8", "output_minrename.p8", "--minify", "--no-minify-consts",
             "--preserve", "*,*.*", pico8_output="output.p8.printh")
    run_test("auto_minrename", "input.p8", "output_minrename-ih.p8", "--minify", "--no-minify-consts", "--rename-safe-only",
             "--ignore-hints", pico8_output="output.p8.printh")
    run_test("auto_minrename-oc", "input.p8", "output_minrename-oc.p8", "--minify", "--no-minify-consts", "--rename-safe-only",
             "--ignore-hints", "--focus-chars", pico8_output="output.p8.printh")
    run_test("auto_minrename-ob", "input.p8", "output_minrename-ob.p8", "--minify", "--no-minify-consts", "--rename-safe-only",
             "--ignore-hints", "--focus-compressed", pico8_output="output.p8.printh")
    run_test("minminify", "input.p8", "output_min.p8", "--minify-safe-only", "--no-minify-consts", "--focus-tokens",
             "--ignore-hints", "--no-minify-rename", "--no-minify-lines", pico8_output="output.p8.printh")
    run_test("minifytokens", "input.p8", "output_tokens.p8", "--minify", "--no-minify-consts", "--focus-tokens",
             "--no-minify-spaces", "--no-minify-lines", "--no-minify-comments", "--no-minify-rename",
             pico8_output="output.p8.printh")
    run_test("nominify", "input.p8", "output-nomin.p8", check_output=False, pico8_output="output.p8.printh")
    run_test("reformat", "input.p8", "input-reformat.p8", "--unminify", "--unminify-indent", "4")

    run_test("nopreserve", "nopreserve.p8", "nopreserve.p8", "--minify",
             "--no-preserve", "circfill,rectfill", pico8_output_val="yep")
    run_test("safeonly", "safeonly.p8", "safeonly.p8", "--minify-safe-only")

    run_test("const-baseline", "const.p8", "const-baseline.p8", check_output=False, pico8_output="const.p8.printh")
    run_test("const", "const.p8", "const.p8", "--minify",
             "--no-minify-spaces", "--no-minify-lines", "--no-minify-comments", "--no-minify-rename", "--no-minify-tokens",
             pico8_output="const.p8.printh")
    run_test("const2", "const2.p8", "const2.p8", "--minify",
             "--no-minify-spaces", "--no-minify-lines", "--no-minify-comments", "--no-minify-rename", "--no-minify-tokens",
             stdout_output="const2.txt", norm_stdout=norm_paths)
    run_test("constcl", "constcl.p8", "constcl.p8", "--minify")
    run_test("constcl-1", "constcl.p8", "constcl-1.p8", "--minify", "--const", "DEBUG", "true", "--const", "SPEED", "2.5", "--str-const", "VERSION", "v1.2")
    run_test("constcl-2", "constcl.p8", "constcl-2.p8", "--minify", "--const", "DEBUG", "true", "--const", "SPEED", "-2.6", "--const", "hero", "~1")
    run_test("constmin", "const.p8", "constmin.p8", "--minify", pico8_output="const.p8.printh")

    if run_test("test", "test.p8", "test.p8", "--minify", "--no-minify-consts", pico8_output_val="DONE"):
        run_test("unmintest", "test.p8", "test-un.p8", "--unminify", from_output=True, pico8_output_val="DONE")
    run_test("test-ob", "test.p8", "test-ob.p8", "--focus-compressed", "--minify", "--no-minify-consts", pico8_output_val="DONE")
    run_test("test-oc", "test.p8", "test-oc.p8", "--focus-chars", "--minify", "--no-minify-consts", pico8_output_val="DONE")
    run_test("test-simp", "test.p8", "test-simp.p8", "--minify", pico8_output_val="DONE")
    run_test("test-none", "test.p8", "test-none.p8", check_output=False, pico8_output_val="DONE")
    run_test("globasmemb", "globasmemb.p8", "globasmemb.p8", "--minify", pico8_output_val="OK")
    if run_test("p82png", "testcvt.p8", "testcvt.png",
                "--extra-output", "test_output/testcvt.sprites.png", "spritesheet",
                "--extra-output", "test_output/testcvt.label.png", "label", 
                extra_outputs=["testcvt.sprites.png", "testcvt.label.png"]):
        run_test("merge", "default.p8", "merged.p8",
                 "--label", "test_output/testcvt.label.png", "--title", "a fine title", "--title", "by you",
                 "--merge", "test_output/testcvt.sprites.png", "gfx", "spritesheet",
                 "--merge", "test_input/default2.p8", "map,sfx,music,gff")
    run_test("test_png", "test.png", "test.png", "--minify", "--no-minify-consts")
    run_test("png2p8", "test.png", "testcvt.p8")
    if run_test("compress", "testcvt.p8", "testtmp.png", "--force-compression", check_output=False):
        run_test("compress_check", "testtmp.png", "test_post_compress.p8", from_output=True)
    if run_test("old_compress", "testcvt.p8", "testtmp_old.png", "--force-compression", "--old-compression", check_output=False):
        run_test("old_compress_check", "testtmp_old.png", "test_post_compress_old.p8", from_output=True)
        run_test("old_compress_keep", "testtmp_old.png", "testtmp_old.png", "--keep-compression", from_output=True)
    run_test("lua2p8", "included space.lua", "testlua.p8")
    run_test("rom2p8", "test.rom", "test.rom.p8")
    run_test("p82rom", "testcvt.p8", "test.p8.rom")
    run_test("clip2p8", "test.clip", "test.clip.p8")
    run_test("p82clip", "testcvt.p8", "testcvt.clip")
    if run_test("url2p8", "test.url", "test.url.p8"):
        run_test("p82url", "test.url.p8", "test.url", from_output=True)

    run_test("default", "default.p8", "default.rom")
    run_test("default2", "default2.p8", "default2.rom")
    run_test("genend", "genend.p8.png", "genend.p8", update_version=False)
    run_test("lint", "bad.p8", None, "--lint", stdout_output="bad.txt", norm_stdout=norm_paths, exit_code=2)
    run_test("linttab", "bad.p8", None, "--lint", "--error-format", "tabbed",
             stdout_output="bad-tab.txt", norm_stdout=norm_paths, exit_code=2)
    run_test("count", "bad.p8", None, "--count", stdout_output="badcount.txt")
    run_test("countminus", "minus.p8", None, "--count", stdout_output="minuscount.txt")
    run_test("error", "worse.p8", None, "--lint", stdout_output="worse.txt", norm_stdout=norm_paths, exit_code=1)
    run_test("script", "script.p8", "script.p8", "--script", path_join("test_input", "my_script.py"),
             "--update-version", "--script-args", "my-script-arg", "--my-script-opt", "123", update_version=False)
    run_test("sublang.lint", "sublang.p8", None, "--lint",
             "--script", path_join("test_input", "sublang.py"), stdout_output="sublang.txt", norm_stdout=norm_paths, exit_code=2)
    run_test("sublang", "sublang.p8", "sublang.p8", "--minify",
             "--script", path_join("test_input", "sublang.py"))
    run_test("unkform1", "unkform1", "unkform1", update_version=False)
    run_test("unkform2", "unkform2.png", "unkform2", "--format", "png", "--input-format", "auto", update_version=False)
    run_test("mini", "mini.p8", "mini.p8", "--minify", "--no-minify-lines", "--no-minify-consts",
             "--builtin", "a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z",
             "--local-builtin", "a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z")
    run_test("tinyrom", "tiny.rom", "tiny.lua")
    run_test("title", "title.p8", "title.p8.png", update_version=False)

    if run_test("repl", "repl.p8", "repl.p8", "--minify",
                "--rename-map", "test_output/repl.map", extra_outputs=["repl.map"], pico8_output_val="finished"):
        run_test("unminrepl", "repl.p8", "repl-un.p8", "--unminify", from_output=True, pico8_output_val="finished")
        run_test("repl-com", "repl.p8", "repl-com.png", "--force-compression", from_output=True, pico8_output_val="finished")
    run_test("repl-oc", "repl.p8", "repl-oc.p8", "--minify", "--focus-chars", pico8_output_val="finished")
    run_test("repl-ob", "repl.p8", "repl-ob.p8", "--minify", "--focus-compressed", pico8_output_val="finished")

    run_test("notnil", "notnil.p8", "notnil.p8", "--minify", pico8_output_val="passed")
    run_test("wildcards", "wildcards.p8", "wildcards.p8", "--minify", "--no-minify-consts")

    run_test("reorder", "reorder.p8", "reorder.p8", "-m", "--focus-tokens", "--no-minify-lines", "--no-minify-consts",
             pico8_output="reorder.p8.printh")
    run_test("reorder_simp", "reorder.p8", "reorder_simp.p8", "-m", "--focus-tokens", "--no-minify-lines", 
             pico8_output="reorder.p8.printh")
    run_test("reorder_safe", "reorder.p8", "reorder_safe.p8", "-M", "--focus-tokens", "--no-minify-lines", "--no-minify-consts", 
             "--ignore-hints", pico8_output="reorder.p8.printh")
    run_test("reorder_safe_2", "reorder.p8", "reorder_safe_2.p8", "-m", "--focus-tokens", "--no-minify-lines", "--no-minify-consts", 
             "--reorder-safe-only", pico8_output="reorder.p8.printh")
    
    run_test("short", "short.p8", "short.p8", "-m", "--no-minify-consts", "--focus-chars", pico8_output_val="K\nK")
    run_test("short-lines", "short.p8", "short-lines.p8", "-m", "--no-minify-consts", "--no-minify-lines", "--focus-chars", pico8_output_val="K\nK")
    run_test("short-spaces", "short.p8", "short-spaces.p8", "-m", "--no-minify-consts", "--no-minify-spaces", "--focus-chars", pico8_output_val="K\nK")
    run_test("short2", "short2.p8", "short2.p8", "-m", "--no-minify-consts", "--focus-compressed", "--no-minify-spaces")

    run_test("version-latest", "versioned.p8", "versioned-latest.p8", "-m", "-oc", pico8_output="versioned.p8.printh")
    run_test("version-orig", "versioned.p8", "versioned-orig.p8", "-m", "-oc", update_version=False, pico8_output="versioned.p8.printh")

def main(raw_args):
    global g_opts
    g_opts = parser.parse_args(raw_args)
    init_tests(g_opts)
    
    dir_ensure_exists("test_output")
    run()

    if not g_opts.no_private:
        try:
            from private_run_tests import run as private_run
        except ImportError:
            pass
        else:
            private_run(g_opts, sys.modules[__name__])
    
    return end_tests()

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
