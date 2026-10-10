"""Test-only static server: python3 -m http.server plus vercel.json's rewrites (the game paths /strike, /smash, ..., the camera games /drums, /bubbles, /paint, /stars serve /index.html).
   python3 tests/serve.py [port]   (default 8765, bound to 127.0.0.1, serves the repo root)"""
import functools, http.server, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_rules():
    """vercel.json's rewrites as (regex, destination) pairs (only the ':name(a|b)' and literal forms it uses); redirects as (path, location)."""
    cfg = json.load(open(os.path.join(ROOT, 'vercel.json')))
    def rx(src): return re.compile('^' + re.sub(r':\w+\(([^)]*)\)', r'(?:\1)', src) + '$')
    return [(rx(r['source']), r['destination']) for r in cfg.get('rewrites', [])], {r['source']: r['destination'] for r in cfg.get('redirects', [])}

class Handler(http.server.SimpleHTTPRequestHandler):
    rewrites, redirects = load_rules()
    def log_message(self, *a): pass
    def _route(self):
        path, q = (self.path.split('?', 1) + [''])[:2]
        if path in self.redirects:
            self.send_response(308); self.send_header('Location', self.redirects[path]); self.end_headers(); return False
        for r, dest in self.rewrites:
            if r.match(path): self.path = dest + ('?' + q if q else ''); break
        return True
    def do_GET(self):
        if self._route(): super().do_GET()
    def do_HEAD(self):
        if self._route(): super().do_HEAD()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    http.server.ThreadingHTTPServer.allow_reuse_address = True
    http.server.ThreadingHTTPServer(('127.0.0.1', port), functools.partial(Handler, directory=ROOT)).serve_forever()
