#!/usr/bin/env python3
from test_utils import *
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--measure", action="store_true", help="print the input/output counts for successful tests")
parser.add_argument("--stdout", action="store_true", help="print the stdout of shrinko8 while running the tests")
parser.add_argument("-t", "--test", action="append", help="specify a specific test to run")
parser.add_argument("--no-private", action="store_true", help="do not run private tests, if they exist")
parser.add_argument("-q", "--quiet", action="store_true", help="do not print test successes")
parser.add_argument("-x", "--exe", action="store_true", help="test a packaged exe instead of the python script")
parser.add_argument("--pico8", action="append", help="specify a pico8 exe to test the results with")
g_opts = parser.parse_args()

# for test consistency:
os.environ["PICO8_PLATFORM_CHAR"] = 'w'
os.environ["PICO8_VERSION_ID"] = '38'

def measure(kind, path, input=False):
    print("Measuring %s..." % kind)
    if path_exists(path):
        _, stdout = run_code(path, "--input-count" if input else "--count")
        print(stdout, end="")
    else:
        print("MISSING!")

def run_test(name, input, output, *args, private=False, from_temp=False, to_temp=False, 
             read_stdout=False, exit_code=None, extra_outputs=None, pico8_printh=None):
    if g_opts.test and name not in g_opts.test:
        return None

    prefix = "private_" if private else ""
    inpath = path_join(prefix + ("test_temp" if from_temp else "test_input"), input)
    outpath = path_join(prefix + ("test_temp" if to_temp else "test_output"), output)
    cmppath = path_join(prefix + "test_compare", output)

    if read_stdout:
        args = (inpath,) + args
    else:
        args = (inpath, outpath) + args

    run_success, run_stdout = run_code(*args, exit_code=exit_code)
    success = run_success
    stdouts = [run_stdout]

    if read_stdout:
        file_write_text(outpath, run_stdout)

    if run_success and not to_temp:
        if try_file_read(outpath) != try_file_read(cmppath):
            stdouts.append("ERROR: File difference: %s, %s" % (outpath, cmppath))
            success = False

    if run_success and extra_outputs:
        for extra_output in extra_outputs:
            extra_outpath = path_join(prefix + "test_output", extra_output)
            extra_cmppath = path_join(prefix + "test_compare", extra_output)
            if try_file_read(extra_outpath) != try_file_read(extra_cmppath):
                stdouts.append("ERROR: Extra file difference: %s, %s" % (outpath, cmppath))
                success = False

    if run_success and g_opts.pico8 and pico8_printh != None:
        if pico8_printh == True:
            pico8_printh = file_read_text(path_join(prefix + "test_compare", output + ".printh"))
        for pico8_exe in g_opts.pico8:
            p8_success, p8_stdout = run_pico8(pico8_exe, outpath, expected_printh=pico8_printh)
            if not p8_success:
                stdouts.append("ERROR: Pico8 run failure with %s" % pico8_exe)
                stdouts.append(p8_stdout)
                success = False

    stdout = "\n".join(stdouts)

    if not success:
        print("\nERROR - test %s failed" % name)
        print(stdout)
        measure("new", outpath)
        measure("old", cmppath)
        fail_test()
        return False
    elif g_opts.measure:
        print("\nMeasuring %s" % name)
        measure("in", inpath, input=True)
        measure("out", outpath)
    elif not g_opts.quiet:
        print("\nTest %s succeeded" % name)
    if g_opts.stdout:
        print(stdout)
    return True

def run_stdout_test(name, input, *args, output=None, **kwargs):
    run_test(name, input, output, *args, **kwargs, read_stdout=True)

def run():
    run_test("minify", "input.p8", "output.p8", "--minify",
             "--preserve", "*.preserved_key,preserved_glob,preserving_obj.*",
             "--no-preserve", "circfill,rectfill", pico8_printh=True)
    run_test("semiobfuscate", "input.p8", "output_semiob.p8", "--minify", "--format", "code", 
             "--preserve", "*.*,preserved_glob",
             "--no-minify-spaces", "--no-minify-lines")
    run_test("minrename", "input.p8", "output_minrename.p8", "--minify", "--format", "code", 
             "--preserve", "*,*.*")
    run_test("auto_minrename", "input.p8", "output_minrename.p8", "--minify", "--format", "code",
             "--minify-safe-only")
    run_test("minifytokens", "input.p8", "output_tokens.p8", "--minify", "--format", "code",
             "--no-minify-spaces", "--no-minify-lines", "--no-minify-comments", "--no-minify-rename")
    run_test("test", "test.p8", "test.p8", "--minify", "--rename-members-as-globals", pico8_printh="DONE")
    run_test("p82png", "testcvt.p8", "testcvt.png")
    run_test("test_png", "test.png", "test.png", "--minify")
    run_test("png2p8", "test.png", "testcvt.p8")
    if run_test("compress", "testcvt.p8", "testtmp.png", "--force-compression", to_temp=True):
        run_test("compress_check", "testtmp.png", "test_post_compress.p8", from_temp=True)
    if run_test("old_compress", "testcvt.p8", "testtmp_old.png", "--force-compression", "--old-compression", to_temp=True):
        run_test("old_compress_check", "testtmp_old.png", "test_post_compress_old.p8", from_temp=True)
        run_test("old_compress_keep", "testtmp_old.png", "testtmp_old.png", "--keep-compression", from_temp=True)
    run_test("lua2p8", "included.lua", "testlua.p8")
    run_test("rom2p8", "test.rom", "test.rom.p8")
    run_test("p82rom", "testcvt.p8", "test.p8.rom")
    run_test("clip2p8", "test.clip", "test.clip.p8")
    run_test("p82clip", "testcvt.p8", "testcvt.clip")
    run_test("url2p8", "test.url", "test.url.p8")
    run_test("p82url", "bad.p8", "bad.url")
    run_test("genend", "genend.p8.png", "genend.p8")
    run_stdout_test("lint", "bad.p8", "--lint", output="bad.txt", exit_code=1)
    run_stdout_test("count", "bad.p8", "--count", output="badcount.txt")
    run_test("script", "script.p8", "script.p8", "--script", path_join("test_input", "my_script.py"),
             "--script-args", "my-script-arg", "--my-script-opt", "123")
    run_stdout_test("sublang.lint", "sublang.p8", "--lint",
             "--script", path_join("test_input", "sublang.py"), output="sublang.txt", exit_code=1)
    run_test("sublang", "sublang.p8", "sublang.p8", "--minify",
             "--script", path_join("test_input", "sublang.py"))
    run_test("unkform1", "unkform1", "unkform1")
    run_test("unkform2", "unkform2.png", "unkform2", "--format", "png", "--input-format", "auto")
    run_test("mini", "mini.p8", "mini.p8", "--minify", "--no-minify-lines",
             "--builtin", "a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z")
    run_test("tinyrom", "tiny.rom", "tiny.lua")
    run_test("title", "title.p8", "title.p8.png")
    run_test("repl", "repl.p8", "repl.p8", "--minify", "--preserve", "env.*,g_ENV.*,*._ENV,*._env,*._", 
             "--rename-map", "test_output/repl.map", extra_outputs=["repl.map"], pico8_printh="finished")

if __name__ == "__main__":
    init_tests(g_opts.exe)
    
    os.makedirs("test_output", exist_ok=True)
    os.makedirs("test_temp", exist_ok=True)
    run()

    if not g_opts.no_private:
        try:
            from private_run_tests import run as private_run
        except ImportError:
            pass
        else:
            private_run(run_test, run_stdout_test)
    
    exit_tests()
