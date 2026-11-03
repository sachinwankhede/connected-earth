"""build/live_check.py against a small local site: passes on a good site, fails on a wrong build stamp, a missing file, and a stale page."""
import hashlib, http.server, json, os, subprocess, sys, tempfile, threading, unittest, functools
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
SCRIPT = os.path.join(ROOT, 'build', 'live_check.py')

def write(root, path, data):
    p = os.path.join(root, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'wb').write(data if isinstance(data, bytes) else json.dumps(data).encode())

def make_site(root, sw_stamp=None, drop=None):
    html = b'<html>Connected Earth page</html>'
    stamp = hashlib.md5(html).hexdigest()[:8]
    write(root, 'index.html', html)
    write(root, 'pilot/index.html', html)
    write(root, 'sw.js', ('const V = "%s";\n' % (sw_stamp or stamp)).encode())
    write(root, 'api/places/main/index-world.json', [1])
    write(root, 'api/places/main/cards-world.json', [1])
    write(root, 'api/yellowstone.json', {'nodes': list(range(10))})
    write(root, 'api/species/abies-balsamea.json', {'t': 'x' * 40})
    write(root, 'api/search/meta.json', {'a': 1})
    write(root, 'api/ties/alabama.json', {'a': 1})
    if drop: os.remove(os.path.join(root, drop))
    return stamp

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

def run(root, stamp):
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=root))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        r = subprocess.run([sys.executable, SCRIPT, 'http://127.0.0.1:%d' % srv.server_address[1], stamp, '--tries', '2', '--wait', '0.1'], capture_output=True, text=True)
    finally:
        srv.shutdown()
    return r.returncode, r.stdout

class LiveCheck(unittest.TestCase):
    def test_good_site_passes(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run(d, make_site(d))[0], 0)

    def test_stale_stamp_fails(self):
        with tempfile.TemporaryDirectory() as d:
            make_site(d, sw_stamp='00000000')
            real = hashlib.md5(open(os.path.join(d, 'index.html'), 'rb').read()).hexdigest()[:8]
            code, out = run(d, real)
            self.assertEqual(code, 1); self.assertIn('sw.js carries build 00000000', out)

    def test_expected_stamp_differs_from_live(self):
        with tempfile.TemporaryDirectory() as d:
            make_site(d)
            code, out = run(d, 'deadbeef')
            self.assertEqual(code, 1); self.assertIn('index.html is build', out)

    def test_missing_file_fails(self):
        for gone in ('api/search/meta.json', 'api/ties/alabama.json', 'api/places/main/cards-world.json'):
            with tempfile.TemporaryDirectory() as d:
                code, out = run(d, make_site(d, drop=gone))
                self.assertEqual(code, 1, gone); self.assertIn(gone, out)

if __name__ == '__main__': unittest.main()
