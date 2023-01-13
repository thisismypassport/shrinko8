from utils import *
from unittest.mock import patch
import argparse, subprocess

status = 0

parser = argparse.ArgumentParser()
parser.add_argument("--measure", action="store_true")
parser.add_argument("--stdout", action="store_true")
parser.add_argument("-t", "--test", action="append")
parser.add_argument("--no-private", action="store_true")
parser.add_argument("-q", "--quiet", action="store_true")
parser.add_argument("-x", "--exe", action="store_true")
opts = parser.parse_args()

# for test consistency:
os.environ["PICO8_PLATFORM_CHAR"] = 'w'
os.environ["PICO8_VERSION_ID"] = '36'

if opts.exe:
    g_exe_path = "dist/shrinko8/shrinko8.exe"
else:
    g_code_file = "shrinko8.py"
    g_code = file_read_text(g_code_file)

def fail_test():
    global status
    status = 1

def run_code(*args, exit_code=None):
    actual_code = None
    stdout = None

    try:
        if opts.exe:
            try:
                stdout = subprocess.check_output([g_exe_path, *args], encoding="utf8")
            except subprocess.CalledProcessError as e:
                actual_code = e.returncode
                stdout = e.stdout
        else:
            stdout_io = StringIO()
            try:
                with patch.object(sys, "argv", ["dontcare", *args]):
                    with patch.object(sys, "stdout", stdout_io):
                        exec(g_code, {"__file__": g_code_file, "__name__": "__main__"})
            except SystemExit as e:
                actual_code = e.code
            
            stdout = stdout_io.getvalue()

    except Exception:
        traceback.print_exc()
        return False, stdout
            
    if exit_code == actual_code:
        return True, stdout
    else:
        print("Exit with unexpected code %s" % actual_code)
        return False, stdout

def measure(kind, path, input=False):
    print("Measuring %s..." % kind)
    if path_exists(path):
        _, stdout = run_code(path, "--input-count" if input else "--count")
        print(stdout, end="")
    else:
        print("MISSING!")

def run_test(name, input, output, *args, private=False, from_temp=False, to_temp=False):
    if opts.test and name not in opts.test:
        return None

    prefix = "private_" if private else ""
    inpath = path_join(prefix + ("test_temp" if from_temp else "test_input"), input)
    outpath = path_join(prefix + ("test_temp" if to_temp else "test_output"), output)
    cmppath = path_join(prefix + "test_compare", output)

    success, stdout = run_code(inpath, outpath, *args)
    if success and not to_temp:
        success = try_file_read(outpath) == try_file_read(cmppath)

    if not success:
        print("\nERROR - test %s failed" % name)
        print(stdout)
        measure("new", outpath)
        measure("old", cmppath)
        fail_test()
        return False
    elif opts.measure:
        print("\nMeasuring %s" % name)
        measure("in", inpath, input=True)
        measure("out", outpath)
    elif not opts.quiet:
        print("\nTest %s succeeded" % name)
    if opts.stdout:
        print(stdout)
    return True

def run_stdout_test(name, input, *args, private=False, output=None, exit_code=None):
    if opts.test and name not in opts.test:
        return None

    prefix = "private_" if private else ""
    inpath = path_join(prefix + "test_input", input)
    outpath = path_join(prefix + "test_output", output)
    cmppath = path_join(prefix + "test_compare", output)

    success, stdout = run_code(inpath, *args, exit_code=exit_code)
    file_write_text(outpath, stdout)
    if success:
        success = stdout == try_file_read_text(cmppath)

    if not success:
        print("\nERROR - test %s failed" % name)
        print(stdout)
        fail_test()
        return False
    elif not opts.quiet:
        print("\nTest %s succeeded" % name)
    return True

def run():
    run_test("minify", "input.p8", "output.p8", "--minify", "--format", "code", 
             "--preserve", "*.preserved_key,preserved_glob,preserving_obj.*",
             "--no-preserve", "circfill,rectfill")
    run_test("semiobfuscate", "input.p8", "output_semiob.p8", "--minify", "--format", "code", 
             "--preserve", "*.*,preserved_glob",
             "--no-minify-spaces", "--no-minify-lines")
    run_test("minrename", "input.p8", "output_minrename.p8", "--minify", "--format", "code", 
             "--preserve", "*,*.*")
    run_test("minifytokens", "input.p8", "output_tokens.p8", "--minify", "--format", "code",
             "--no-minify-spaces", "--no-minify-lines", "--no-minify-comments", "--no-minify-rename")
    run_test("test", "test.p8", "test.p8", "--minify")
    run_test("p82png", "testcvt.p8", "testcvt.png")
    run_test("test_png", "test.png", "test.png", "--minify")
    run_test("png2p8", "test.png", "testcvt.p8")
    if run_test("compress", "testcvt.p8", "testtmp.png", "--force-compression", to_temp=True):
        run_test("compress_check", "testtmp.png", "test_post_compress.p8", from_temp=True)
    run_test("lua2p8", "included.lua", "testlua.p8")
    run_test("rom2p8", "test.rom", "test.rom.p8")
    run_test("p82rom", "testcvt.p8", "test.p8.rom")
    run_test("clip2p8", "test.clip", "test.clip.p8")
    run_test("p82clip", "testcvt.p8", "testcvt.clip")
    run_test("url2p8", "test.url", "test.url.p8")
    run_test("p82url", "testcvt.p8", "testcvt.url")
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

if __name__ == "__main__":
    os.makedirs("test_output", exist_ok=True)
    os.makedirs("test_temp", exist_ok=True)
    run()

    if not opts.no_private:
        try:
            from private_run_tests import run as private_run
        except ImportError:
            pass
        else:
            private_run()
    
    print("\nAll passed" if status == 0 else "\nSome FAILED!")
    sys.exit(status)
