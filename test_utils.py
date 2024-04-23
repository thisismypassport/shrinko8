from utils import *
from unittest.mock import patch
import subprocess, pstats, cProfile

def init_tests(opts): # use: opts.exe and opts.profile
    global g_num_ran, g_num_failed
    g_num_ran = g_num_failed =0

    global g_profile, g_profile_stats_files
    g_profile = opts.profile
    if g_profile:
        g_profile = cProfile.Profile()
        g_profile_stats_files = []
    
    global g_use_exe
    g_use_exe = opts.exe
    if g_use_exe:
        global g_exe_path
        g_exe_path = "dist/shrinko8/shrinko8.exe"
    else:
        global g_code_file
        g_code_file = "shrinko8.py"

def start_test():
    global g_num_ran
    g_num_ran += 1

def fail_test():
    global g_num_failed
    g_num_failed += 1

def get_test_results():
    stats_file = None
    if g_profile:
        stats_file = file_temp()
        g_profile.dump_stats(stats_file)

    return g_num_ran, g_num_failed, stats_file

def add_test_results(results):
    ran, failed, stats_file = results
    global g_num_ran, g_num_failed, g_profile_stats_files

    g_num_ran += ran
    g_num_failed += failed
    
    if stats_file:
        g_profile_stats_files.append(stats_file)

def end_tests():
    status = 0
    if g_num_failed:
        print("\n%d/%d FAILED!" % (g_num_failed, g_num_ran))
        status = 1
    elif g_num_ran:
        print("\nAll %d passed" % g_num_ran)
    else:
        print("\nNo tests ran!")
        status = 2
    
    if g_profile:
        stats = pstats.Stats()
        for src in [g_profile, *g_profile_stats_files]:
            try:
                stats.add(src)
            except TypeError:
                pass # workaround due to potentially empty data
        stats.sort_stats("cumtime")
        stats.print_stats()
        for stats_file in g_profile_stats_files:
            file_delete(stats_file)
    
    return status

def run_code(*args, exit_code=0):
    actual_code = 0
    stdout = ""
    
    if g_profile:
        g_profile.enable()

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
    
    finally:
        if g_profile:
            g_profile.disable()
    
    if exit_code == actual_code:
        return True, stdout
    else:
        print(f"Exit with unexpected code {actual_code}")
        return False, stdout

def run_pico8(p8_exe, cart_path, expected_printh=None, timeout=5.0, allow_timeout=False):
    try:
        stdout = subprocess.check_output([p8_exe, "-x", cart_path], encoding="utf8", errors='replace', stderr=subprocess.STDOUT, timeout=timeout)
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
        actual_printh = "\n".join(actual_printh_lines)
        success = actual_printh == expected_printh
        return success, actual_printh # more interesting than stdout
    else:
        return success, stdout

def run_interactive_pico8(p8_exe, cart_path):
    try:
        args = [p8_exe, "-run", cart_path, "-home", "private_pico8_home", "-volume", "0", "-windowed", "1", "-width", "128", "-height", "128"]
        return True, subprocess.check_output(args, encoding="utf8", errors='replace', stderr=subprocess.STDOUT)
    except subprocess.SubprocessError as e:
        return False, f"Exception: {e}"

def interact_with_pico8s(pico8_paths, timeout): # for use in daemon thread
    import test_gui_utils as gui

    pico8_paths = set(path_resolve(pico8) for pico8 in pico8_paths)

    pico8_keys = [gui.key("left"), gui.key("right"), gui.key("up"), gui.key("down"), gui.key('x'), gui.key('z')]
    pico8_key_counts = [0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 3, 3, 4]
    window_data = defaultdict(lambda: Dynamic(keys=[], pid=None, abandoned=False))
    interact_start_time = 4.5 # before this, it's booting

    while True:
        # either shutdown an old pico8 window or send keys to a random pico8 window
        curr_time = datetime.now(timezone.utc)

        pico8_windows = []
        old_pico8_windows = []
        for window in gui.iter_windows():
            proc = gui.get_window_process_info(window)
            if proc.path and path_resolve(proc.path) in pico8_paths:
                wdata = window_data[window]
                run_time = (curr_time - proc.start_time).total_seconds()
                if wdata.pid != proc.pid:
                    wdata.keys.clear()
                    wdata.pid = proc.pid
                    wdata.abandoned = False

                if run_time > interact_start_time and not wdata.abandoned:
                    pico8_windows.append(window)
                    if run_time > timeout:
                        old_pico8_windows.append(window)

        if pico8_windows:
            if old_pico8_windows:
                window = old_pico8_windows[0]
            else:
                window = random.choice(pico8_windows)
            
            if gui.set_foreground_window(window):
                key_count = random.choice(pico8_key_counts)
                keys = random.sample(pico8_keys, k=key_count)
                prev_keys = window_data[window].keys

                for key in prev_keys:
                    if key not in keys:
                        gui.send_key(key, False)
                
                if old_pico8_windows:
                    # the escape will terminate a running pico8 cart, yet pivot a failed pico8 cart to the code editor
                    gui.send_key("escape")
                    time.sleep(0.05)
                    gui.send_text("shutdown\n")
                    window_data[window].abandoned = True # leave on screen, if shutdown failed
                else:
                    for key in keys:
                        if key not in prev_keys:
                            gui.send_key(key, True)

        time.sleep(0.05)
