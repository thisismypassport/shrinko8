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
        global g_code_file
        g_code_file = "shrinko8.py"

def fail_test():
    global g_status
    g_status = 1

def is_fail_test():
    return g_status != 0

def end_tests():
    print("\nAll passed" if g_status == 0 else "\nSome FAILED!")
    return g_status

def run_code(*args, exit_code=0):
    actual_code = 0
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
                        exec_script_by_path(g_code_file, name="__main__")
            except SystemExit as e:
                actual_code = e.code or 0
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
        print(f"Exit with unexpected code {actual_code}")
        return False, stdout

def run_pico8(p8_exe, cart_path, expected_printh=None, timeout=5.0, allow_timeout=False, with_window=False):
    try:
        if with_window:
            args = [p8_exe, "-run", cart_path, "-home", "private_pico8_home", "-volume", "0", "-windowed", "1", "-width", "128", "-height", "128"]
        else:
            args = [p8_exe, "-x", cart_path]
        
        stdout = subprocess.check_output(args, encoding="utf8", errors='replace', stderr=subprocess.STDOUT, timeout=timeout)
    except subprocess.SubprocessError as e:
        if allow_timeout and isinstance(e, subprocess.TimeoutExpired):
            stdout = e.stdout
        else:
            return False, f"Exception: {e}\n{e.stdout}"
    
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
