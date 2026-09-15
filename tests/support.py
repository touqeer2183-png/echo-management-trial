import json
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer
from backend import config, security
from backend.handler import Handler
from backend.migrations import init


class ApiCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_db = config.DB
        config.DB = Path(self.temp.name) / 'echo.sqlite3'
        security.SESSIONS.clear()
        init()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.cookies = {}
        self.ok('setup', {'name': 'Admin', 'username': 'admin', 'password': 'test-password'})
        self.login('admin')
        self.doc = self.ok('doctors', {'name': 'Doctor One', 'qualification': 'Test', 'registration': 'TEST'}, 'admin')['id']
        for name, role in [('receptionist', 'receptionist'), ('operator', 'operator'), ('operator2', 'operator'), ('doctor', 'doctor')]:
            self.ok('users', {'name': name, 'username': name, 'role': role, 'password': 'test-password', 'doctor_id': self.doc}, 'admin')
            self.login(name)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        config.DB = self.previous_db
        security.SESSIONS.clear()
        self.temp.cleanup()

    def call(self, path, data=None, user=None, headers=None):
        h = {'Content-Type': 'application/json'}
        if user:
            h['Cookie'] = self.cookies[user]
        h.update(headers or {})
        req = urllib.request.Request(f'http://127.0.0.1:{self.server.server_port}/api/{path}', data=None if data is None else json.dumps(data).encode(), headers=h)
        try:
            response = urllib.request.urlopen(req, timeout=10)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            return response.status, json.load(response), response.headers

    def ok(self, path, data=None, user=None):
        status, body, _ = self.call(path, data, user)
        self.assertEqual(status, 200, body)
        return body

    def login(self, user):
        status, body, headers = self.call('login', {'username': user, 'password': 'test-password'})
        self.assertEqual(status, 200, body)
        self.cookies[user] = headers['Set-Cookie'].split(';')[0]
        return headers

    def patient(self, n=1, **extra):
        data = {'name': f'Test Patient {n}', 'identity': f'{1000000000000+n}', 'phone': f'030{n:08}', 'relation_type': 'S/O', 'relation_name': 'Test Parent', 'age': '35', 'sex': 'Male'}
        data.update(extra)
        return self.ok('patients', data, 'receptionist')

    def encounter(self, n=1, owner='operator'):
        p = self.patient(n)
        v = self.ok('token', {'patient_id': p['id']}, 'receptionist')
        self.ok('claim', {'id': v['id']}, owner)
        return p, v

    def report(self):
        return {'doctor_id': self.doc, 'values': {'EF': '60'}, 'findings': 'Manual test report', 'conclusion': 'Manual test conclusion', 'columns': ['A', 'B'], 'rows': [['x', 'y']], 'lines': ['Test line']}
