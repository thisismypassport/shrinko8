from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import sys, os, argparse, subprocess

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--address", default="localhost", help="the address to serve the server on")
parser.add_argument("-p", "--port", type=int, default=0, help="the port to serve the server on")
parser.add_argument("-d", "--dir", default="site", help="the directory with the site")
parser.add_argument("-t", "--timeout", type=int, help="the timeout in seconds (reset on every request)")
parser.add_argument("-x", "--execute", help="command to execute once server is up and terminate before it ends")
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

if __name__ == '__main__':
    with SiteTestServer() as server:
        if opts.execute:
            proc = subprocess.Popen(opts.execute)
        while g_exitcode is None:
            server.handle_request()
        if opts.execute:
            proc.terminate()
    sys.exit(g_exitcode)
