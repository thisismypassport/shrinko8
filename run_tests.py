from utils import *
from unittest.mock import patch
from pico_cart import write_code, to_pico_chars

code = file_read_text("timp_p8_tools.py")

def measure(kind, data):
    print("Measuring %s:" % kind)
    write_code(BinaryWriter(BytesIO()), to_pico_chars(data.decode()))

def run_test(input, output, *args, private=False):
    prefix = "private_" if private else ""
    inpath = path_join(prefix + "test_input", input)
    outpath = path_join(prefix + "test_output", output)
    cmppath = path_join(prefix + "test_compare", output)
    with patch.object(sys, "argv", ["dontcare", inpath, outpath, *args]):
        exec(code, {})
    
    outdata = try_file_read(outpath)
    cmpdata = try_file_read(cmppath)
    if outdata != cmpdata:
        print("ERROR - test %s failed" % input)
        if "--measure" in sys.argv[1:]: # slow unless using pypy...
            measure("new", outdata)
            measure("old", cmpdata)

def run():
    run_test("input.p8", "output.p8", "--minify", "--format", "code", "--preserve", "*.preserved_key,preserved_glob,preserving_obj.*")
    run_test("test.p8", "test.p8", "--minify")

if __name__ == "__main__":
    os.makedirs("test_output", exist_ok=True)
    run()

    try:
        from private_run_tests import run
        run()
    except ImportError:
        pass
    print("All done")
