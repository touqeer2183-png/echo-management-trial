"""Deployment settings; tests may override DB before initialization."""
import os
from pathlib import Path
from urllib.parse import urlsplit
ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'public'
DB = Path(os.environ.get('ECHO_DB', str(ROOT / 'data' / 'echo.sqlite3')))
PORT = int(os.environ.get('PORT', '8765'))
PUBLIC_ORIGIN = os.environ.get('ECHO_PUBLIC_ORIGIN', '').strip().rstrip('/')
if PUBLIC_ORIGIN:
    _origin = urlsplit(PUBLIC_ORIGIN)
    if (_origin.scheme != 'https' or not _origin.hostname or _origin.username
            or _origin.password or _origin.path or _origin.query or _origin.fragment):
        raise ValueError('ECHO_PUBLIC_ORIGIN must be an HTTPS origin, e.g. https://echo.example.com')
HOST = os.environ.get('ECHO_HOST', '127.0.0.1' if PUBLIC_ORIGIN else '0.0.0.0')
SESSION_SECONDS = 28800
REQUEST_LIMIT = 500000
STAMP_LIMIT = 250000
IMAGE_MIMES = ('image/png', 'image/jpeg')
