from utils import *
from unittest.mock import patch

code_file = "timp_p8_tools.py"
code = file_read_text(code_file)
measure_all = "--measure" in sys.argv[1:]

def run_code(*args):
    try:
        with patch.object(sys, "argv", ["dontcare", *args]):
            exec(code, {"__file__": code_file})
        return True
    except SystemExit:
        print("EXIT!")
        return False
    except Exception:
        traceback.print_exc()
        return False

def measure(kind, path, input=False):
    print("\nMeasuring %s..." % kind)
    if path_exists(path):
        run_code(path, "--input-count" if input else "--count")
    else:
        print("MISSING!")

def run_test(name, input, output, *args, private=False):
    prefix = "private_" if private else ""
    inpath = path_join(prefix + "test_input", input)
    outpath = path_join(prefix + "test_output", output)
    cmppath = path_join(prefix + "test_compare", output)

    if not run_code(inpath, outpath, *args) or try_file_read(outpath) != try_file_read(cmppath):
        print("ERROR - test %s failed" % name)
        measure("new", outpath)
        measure("old", cmppath)
    elif measure_all and "--minify" in args:
        print("Measuring %s" % name)
        measure("out", outpath)
        measure("in", inpath, input=True)

def run():
    run_test("minify", "input.p8", "output.p8", "--minify", "--format", "code", "--preserve", "*.preserved_key,preserved_glob,preserving_obj.*")
    run_test("test", "test.p8", "test.p8", "--minify")
    #run_test("p82png", "test.p8", "testcvt.png", "--format", "png")
    #run_test("test_png", "test.png", "test.png", "--minify", "--format", "png")
    run_test("png2p8", "test.png", "testcvt.p8", "--format", "p8")

if __name__ == "__main__":
    os.makedirs("test_output", exist_ok=True)
    run()

    try:
        from private_run_tests import run
        run()
    except ImportError:
        pass
    print("All done")
