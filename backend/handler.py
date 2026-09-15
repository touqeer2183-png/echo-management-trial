"""HTTP transport and route registration; domain work belongs to services."""
import json
import logging
import sqlite3
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from . import config, security
from .database import transaction
from .permissions import require
from .routes import auth, state, patients, tokens, reports, analytics, admin

ROUTES = {
    ('POST', '/api/patients'): ('patients', patients),
    ('POST', '/api/patient-edit'): ('patients', patients),
    ('POST', '/api/patient'): ('search', patients),
    ('POST', '/api/history'): ('search', patients),
    ('POST', '/api/token'): ('token', tokens),
    ('POST', '/api/permission'): ('permission', tokens),
    ('POST', '/api/claim'): ('claim', tokens),
    ('POST', '/api/release'): ('claim', tokens),
    ('POST', '/api/report'): ('report', reports),
    ('POST', '/api/report/amend'): ('report', reports),
    ('POST', '/api/report/draft'): ('report', reports),
    ('POST', '/api/report/finalize'): ('report', reports),
    ('GET', '/api/reports/drafts'): ('report', reports),
    ('GET', '/api/reports/completed'): ('report', reports),
    ('POST', '/api/analytics'): ('analytics', analytics),
    ('POST', '/api/users'): ('accounts', admin),
    ('POST', '/api/doctors'): ('doctors', admin),
    ('POST', '/api/settings'): ('settings', admin),
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def setup(self):
        super().setup()
        self.connection.settimeout(20)

    def sendj(self, obj, status=200, cookie=None):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        if cookie:
            self.send_header('Set-Cookie', cookie)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith('/api/'):
            return self.api('GET')
        path = unquote(urlparse(self.path).path)
        aliases = {'/logo-left.png': '/assets/logo-left.png', '/logo-right.png': '/assets/logo-right.png', '/hospital-bg.jpg': '/assets/hospital-bg.jpg'}
        path = aliases.get(path, path)
        target = (config.PUBLIC / ('index.html' if path == '/' else path.lstrip('/'))).resolve()
        if not target.is_relative_to(config.PUBLIC.resolve()) or not target.is_file():
            return self.send_error(404)
        body = target.read_bytes()
        self.send_response(200)
        mime = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg'}
        self.send_header('Content-Type', mime.get(target.suffix.lower(), 'application/octet-stream'))
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        self.api('POST')

    def api(self, method):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            data = {}
            if method == 'POST':
                security.check_origin(self.headers)
                data = json.loads(self.rfile.read(security.request_length(self.headers)) or b'{}')
                if not isinstance(data, dict):
                    raise ValueError('Request must be a JSON object')
            response_cookie = None
            # Commit before sending success, so failed commits cannot look successful.
            with transaction(write=method == 'POST') as c:
                if path in ('/api/session', '/api/setup', '/api/login'):
                    result, response_cookie = auth.dispatch(c, method, path, data, self.headers)
                else:
                    user, token = security.session(self.headers, c)
                    if not user:
                        raise auth.AuthenticationError('Please sign in')
                    if path == '/api/logout' and method == 'POST':
                        security.SESSIONS.pop(token, None)
                        result, response_cookie = {'ok': True}, security.cookie()
                    elif path == '/api/state' and method == 'GET':
                        result = state.dispatch(c, user, parse_qs(parsed.query))
                    else:
                        entry = ROUTES.get((method, path))
                        if not entry:
                            raise LookupError('Not found')
                        feature, module = entry
                        require(user, feature)
                        result = module.dispatch(c, user, path, data)
            self.sendj(result, cookie=response_cookie)
        except auth.AuthenticationError as exc:
            self.sendj({'error': str(exc)}, 401)
        except PermissionError as exc:
            self.sendj({'error': str(exc)}, 403)
        except sqlite3.IntegrityError:
            self.sendj({'error': 'Duplicate or invalid record'}, 409)
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            self.sendj({'error': str(exc)}, 400)
        except LookupError:
            self.sendj({'error': 'Not found'}, 404)
        except Exception:
            logging.exception('Request failed')
            self.sendj({'error': 'Unable to complete request'}, 500)
