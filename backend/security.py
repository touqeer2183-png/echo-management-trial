"""Password hashes, expiring sessions and HTTP request protections."""
import datetime
import hashlib
import hmac
import secrets
from http.cookies import SimpleCookie, CookieError
from .config import SESSION_SECONDS, REQUEST_LIMIT
from . import config
SESSIONS = {}

def password(value, salt):
    return hashlib.pbkdf2_hmac('sha256', value.encode(), bytes.fromhex(salt), 300000).hex()

def create_session(row):
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = {key: row[key] for key in ('id', 'name', 'role', 'doctor_id')}
    SESSIONS[token]['expires'] = datetime.datetime.now().timestamp() + SESSION_SECONDS
    return token

def session(headers, c):
    try:
        cookie = SimpleCookie(headers.get('Cookie', '')).get('session')
    except CookieError:
        return None, None
    token = cookie.value if cookie else None
    user = SESSIONS.get(token)
    if user:
        row = c.execute('SELECT active FROM users WHERE id=?', (user['id'],)).fetchone()
        if user['expires'] < datetime.datetime.now().timestamp() or not row or not row['active']:
            SESSIONS.pop(token, None)
            user = None
    return user, token

def cookie(token=''):
    age = SESSION_SECONDS if token else 0
    secure = '; Secure' if config.PUBLIC_ORIGIN else ''
    return f'session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={age}{secure}'

def check_origin(headers):
    origin = headers.get('Origin')
    expected = config.PUBLIC_ORIGIN or 'http://' + headers.get('Host', '')
    if origin and origin != expected:
        raise PermissionError('Invalid origin')

def request_length(headers):
    if headers.get('Transfer-Encoding'):
        raise ValueError('Transfer encoding is not supported')
    n = int(headers.get('Content-Length', 0))
    if not 0 <= n <= REQUEST_LIMIT:
        raise ValueError('Request too large or invalid content length')
    return n
