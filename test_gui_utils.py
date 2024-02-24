from utils import *

class ProcessInfo(Tuple):
    pid = path = start_time = None

if os.name == 'nt':
    import win32api, win32gui, win32process, win32timezone, win32con as wc, pywintypes # type: ignore
    wc.MAPVK_VK_TO_VSC_EX = 4 # missing...

    def iter_windows():
        hwnds = []
        def on_window(hwnd, _):
            hwnds.append(hwnd)
        win32gui.EnumWindows(on_window, None)
        return hwnds

    def get_window_title(hwnd):
        return win32gui.GetWindowText(hwnd)

    def get_window_process_info(hwnd):
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = win32api.OpenProcess(wc.PROCESS_QUERY_INFORMATION | wc.PROCESS_VM_READ, False, pid)
            if proc:
                try:
                    ppath = win32process.GetModuleFileNameEx(proc, None)
                    ptimes = win32process.GetProcessTimes(proc)
                finally:
                    proc.close()
                return ProcessInfo(pid, ppath, ptimes["CreationTime"])
        except pywintypes.error:
            pass # e.g. can't access hwnd, or hwnd/process died
        return ProcessInfo()

    def set_foreground_window(hwnd):
        try:
            win32gui.SetForegroundWindow(hwnd)
            return True
        except pywintypes.error:
            return False # e.g. hwnd died

    _key_map = {
        "ENTER": "RETURN", "BACKSPACE": "BACK",
        "PAGEUP": "PRIOR", "PAGEDOWN": "NEXT",
        "CAPSLOCK": "CAPITAL", "PRINTSCREEN": "PRINT",
        "LCTRL": "LCONTROL", "RCTRL": "RCONTROL", "CTRL": "CONTROL",
        "LALT": "LMENU", "RALT": "RMENU", "ALT": "MENU",
    }

    _ext_key_set = {
        wc.VK_END, wc.VK_HOME, wc.VK_DOWN, wc.VK_UP, wc.VK_LEFT, wc.VK_RIGHT,
        wc.VK_PRIOR, wc.VK_NEXT, wc.VK_INSERT, wc.VK_DELETE, wc.VK_DIVIDE,
        wc.VK_PRINT, wc.VK_NUMLOCK, wc.VK_RCONTROL, wc.VK_RSHIFT, wc.VK_RMENU,
        wc.VK_LWIN, wc.VK_RWIN, wc.VK_APPS,
    }

    def key(name):
        name = name.upper()
        name = _key_map.get(name, name)
        key = getattr(wc, "VK_" + name, None)
        if key is None:
            if len(name) == 1 and (name in string.ascii_letters or name in string.digits):
                key = ord(name)
            else:
                raise Exception(f"no such key: {name}")
        return key

    def send_key(vk, state=None, delay=None, shift=False, ctrl=False, alt=False, numpad=False):
        if isinstance(vk, str):
            vk = key(vk)

        if state is None:
            send_key(vk, True, delay, shift, ctrl, alt, numpad)
            if delay: time.sleep(delay)
            send_key(vk, False, delay, shift, ctrl, alt, numpad)
            return
        
        if state:
            if shift: send_key(wc.VK_LSHIFT, state)
            if ctrl: send_key(wc.VK_LCONTROL, state)
            if alt: send_key(wc.VK_LMENU, state)

        scode = win32api.MapVirtualKey(vk, wc.MAPVK_VK_TO_VSC_EX)
        flags = 0 if state else wc.KEYEVENTF_KEYUP
        if scode >= 0x100:
            flags |= wc.KEYEVENTF_EXTENDEDKEY
            scode >>= 8
        elif (vk in _ext_key_set and not numpad) or (numpad and vk == wc.VK_RETURN):
            flags |= wc.KEYEVENTF_EXTENDEDKEY
        win32api.keybd_event(vk, scode, flags, 0)
        
        if not state:
            if shift: send_key(wc.VK_LSHIFT, state)
            if ctrl: send_key(wc.VK_LCONTROL, state)
            if alt: send_key(wc.VK_LMENU, state)
    
    def send_text(text, delay=None):
        for ch in text:
            if ch == '\n': ch = '\r'
            result = win32api.VkKeyScan(ch)
            if result != -1:
                vk = result & 0xff
                send_key(vk, shift=result & 0x100, ctrl=result & 0x200, alt=result & 0x400)
                if delay: time.sleep(delay)

else:
    raise ImportError("test_gui_utils not supported")
