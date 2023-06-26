from utils import *
from unittest.mock import patch
import subprocess

def init_tests(use_exe=False):
    global g_status
    g_status = 0
    
    global g_use_exe
    g_use_exe = use_exe
    if use_exe:
        global g_exe_path
        g_exe_path = "dist/shrinko8/shrinko8.exe"
    else:
        global g_code_file, g_code
        g_code_file = "shrinko8.py"
        g_code = file_read_text(g_code_file)

def fail_test():
    global g_status
    g_status = 1

def is_fail_test():
    return g_status != 0

def exit_tests():
    print("\nAll passed" if g_status == 0 else "\nSome FAILED!")
    sys.exit(g_status)

def run_code(*args, exit_code=None):
    actual_code = None
    stdout = ""

    try:
        if g_use_exe:
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
            except Exception:
                traceback.print_exc()
                actual_code = -1
            
            stdout = stdout_io.getvalue()

    except Exception:
        traceback.print_exc()
        return False, stdout
            
    if exit_code == actual_code:
        return True, stdout
    else:
        print("Exit with unexpected code %s" % actual_code)
        return False, stdout

def run_pico8(p8_exe, cart_path, expected_printh=None, timeout=5.0, allow_timeout=False):
    try:
        stdout = subprocess.check_output([p8_exe, "-x", cart_path], encoding="utf8", errors='replace', stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.SubprocessError as e:
        if allow_timeout and isinstance(e, subprocess.TimeoutExpired):
            stdout = e.stdout
        else:
            return False, "Exception: %s\n%s" % (e, e.stdout)
    
    actual_printh_lines = []
    success = True
    for line in stdout.splitlines():
        if line.startswith("INFO:"):
            actual_printh_lines.append(str_after_first(line, ':').strip())
        elif line.startswith("runtime error") or line.startswith("syntax error"):
            success = False

    if success and expected_printh != None:
        success = "\n".join(actual_printh_lines) == expected_printh

    return success, stdout
