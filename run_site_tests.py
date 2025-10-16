from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import sys, os, argparse

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--address", default="localhost", help="the address to serve the server on")
parser.add_argument("-p", "--port", type=int, default=0, help="the port to serve the server on")
parser.add_argument("-d", "--dir", required=True, help="the directory with the site")
parser.add_argument("-t", "--timeout", type=int, help="the timeout in seconds (reset on every request)")
parser.add_argument("-T", "--test", action="store_true", help="test the site via playwright")
parser.add_argument("--test-args", nargs=argparse.REMAINDER, help="test arguments for playwright test")
opts = parser.parse_args()

os.chdir(opts.dir)

g_exitcode = None

class SiteTestHandler(SimpleHTTPRequestHandler):
    def end_headers(m):
        m.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        m.send_header("Pragma", "no-cache")
        m.send_header("Expires", "0")
        super().end_headers()

    def do_POST(m):
        if m.path in ("/test-ok", "/test-fail"):
            print(m.rfile.read(int(m.headers['Content-Length'])).decode())
            m.send_response(200)
            m.end_headers()
            global g_exitcode
            g_exitcode = 0 if m.path == "/test-ok" else 1
        else:
            super().do_post()

class SiteTestServer(TCPServer):
    timeout = opts.timeout

    def handle_timeout(m):
        print("timeout!")
        global g_exitcode
        g_exitcode = 2
    
    def __init__(m):
        super().__init__((opts.address, opts.port), SiteTestHandler)

def run_playwright(address, port):
    from playwright.sync_api import sync_playwright
    from threading import Thread
    from urllib.parse import quote_plus as urlescape
    import shlex
    
    def run():
        def on_console(msg):
            print(f"browser {msg.type}: {msg.text}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.on("console", on_console)
            
            url = f"http://{address}:{port}/?test=post"
            if opts.test_args:
                url += f"&test-args={urlescape(shlex.join(opts.test_args))}"
            page.goto(url)
            print(f"playwright launched. title: {page.title()}")
            
            page.wait_for_function("() => window.testsFinished", timeout=(opts.timeout or 0)*1000)
            print("playwright finished")
            browser.close()
    
    Thread(target=run).start()

if __name__ == '__main__':
    with SiteTestServer() as server:
        if opts.test:
            run_playwright(*server.server_address)
        while g_exitcode is None:
            server.handle_request()
        server.server_close()
    sys.exit(g_exitcode)
