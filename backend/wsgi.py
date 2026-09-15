"""WSGI transport for hosted Python services; reuse the existing API routes."""
from email.message import Message
from http import HTTPStatus
from io import BytesIO
from urllib.parse import quote
from .handler import Handler


class WsgiRequest(Handler):
    # Deliberately do not initialize BaseHTTPRequestHandler: the hosting WSGI
    # server owns sockets, HTTP parsing, and request/response transmission.
    def __init__(self, environ):
        self.path = quote(environ.get('PATH_INFO', '/'), safe='/')
        if environ.get('QUERY_STRING'):
            self.path += '?' + environ['QUERY_STRING']
        self.headers = Message()
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                self.headers[key[5:].replace('_', '-')] = value
        for key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            if environ.get(key):
                self.headers[key.replace('_', '-')] = environ[key]
        self.rfile = environ['wsgi.input']
        self.wfile = BytesIO()
        self.status = 200
        self.response_headers = []

    def send_response(self, code, message=None):
        self.status = code

    def send_header(self, keyword, value):
        self.response_headers.append((keyword, str(value)))

    def end_headers(self):
        pass

    def send_error(self, code, message=None, explain=None):
        self.sendj({'error': HTTPStatus(code).phrase}, code)


def application(environ, start_response):
    request = WsgiRequest(environ)
    method = environ.get('REQUEST_METHOD', 'GET')
    if method in ('GET', 'HEAD'):
        request.do_GET()
    elif method == 'POST':
        request.do_POST()
    else:
        request.send_error(405)
    start_response(f'{request.status} {HTTPStatus(request.status).phrase}',
                   request.response_headers)
    return [b'' if method == 'HEAD' else request.wfile.getvalue()]
