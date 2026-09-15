"""Stage frontend only, with a required HTTPS backend for the Netlify trial."""
import os
import shutil
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def build():
    backend = os.environ.get('ECHO_BACKEND_URL', '').strip().rstrip('/')
    parsed = urlsplit(backend)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username
            or parsed.password or parsed.path or parsed.query or parsed.fragment
            or any(c.isspace() for c in backend)):
        raise ValueError('Set ECHO_BACKEND_URL to the HTTPS backend origin before deploying')
    target = ROOT / 'dist' / 'netlify-trial'
    if target.exists():
        raise FileExistsError('Staging folder already exists; use a clean checkout for a new build')
    shutil.copytree(ROOT / 'public', target)
    (target / '_redirects').write_text(
        f'/api/* {backend}/api/:splat 200!\n', encoding='utf-8')
    (target / '_headers').write_text(
        '/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: same-origin\n'
        '/api/*\n  Cache-Control: no-store\n', encoding='utf-8')
    print(target)


if __name__ == '__main__':
    build()
