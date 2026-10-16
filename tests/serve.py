"""Test-only static server: python3 -m http.server plus vercel.json's rewrites (the game paths /strike, /smash, ..., the camera games /drums, /bubbles, /paint, /stars serve /index.html)
   and its headers (sw.js no-cache, the manifest's content type, ...).
   python3 tests/serve.py [port]   (default 8765, bound to 127.0.0.1, serves the repo root)
   test_pwa.py imports Handler and serves a copy of the site from another directory (functools.partial(Handler, directory=...))."""
import functools, http.server, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_rules():
    """vercel.json's rewrites as (regex, destination) pairs (only the ':name(a|b)' and literal forms it uses); redirects as (path, location); headers as (regex, [(key, value)])."""
    cfg = json.load(open(os.path.join(ROOT, 'vercel.json')))
    def rx(src): return re.compile('^' + re.sub(r':\w+\(([^)]*)\)', r'(?:\1)', src) + '$')
    return ([(rx(r['source']), r['destination']) for r in cfg.get('rewrites', [])], {r['source']: r['destination'] for r in cfg.get('redirects', [])},
            [(rx(h['source']), [(x['key'], x['value']) for x in h['headers']]) for h in cfg.get('headers', [])])

class Handler(http.server.SimpleHTTPRequestHandler):
    rewrites, redirects, vheaders = load_rules()
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, '.webmanifest': 'application/manifest+json', '.js': 'application/javascript', '.mjs': 'text/javascript', '.glb': 'model/gltf-binary'}
    def log_message(self, *a): pass
    def end_headers(self):  # vercel.json's headers for the path asked (the Content-Type is the static handler's own)
        path = getattr(self, '_asked', self.path).split('?', 1)[0]
        for r, hs in self.vheaders:
            if r.match(path):
                for k, v in hs:
                    if k.lower() != 'content-type': self.send_header(k, v)
        super().end_headers()
    def _route(self):
        self._asked = self.path
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
