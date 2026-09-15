import io
import json
from urllib.parse import urlsplit
from wsgiref.util import setup_testing_defaults
from .support import ApiCase
from backend.wsgi import application


class HostedTransport(ApiCase):
    def call(self, path, data=None, user=None, headers=None):
        parsed = urlsplit('/api/' + path)
        body = b'' if data is None else json.dumps(data).encode()
        environ = {}
        setup_testing_defaults(environ)
        environ.update(PATH_INFO=parsed.path, QUERY_STRING=parsed.query,
                       REQUEST_METHOD='GET' if data is None else 'POST',
                       CONTENT_TYPE='application/json', CONTENT_LENGTH=str(len(body)))
        environ['wsgi.input'] = io.BytesIO(body)
        if user:
            environ['HTTP_COOKIE'] = self.cookies[user]
        for key, value in (headers or {}).items():
            environ['HTTP_' + key.upper().replace('-', '_')] = value
        response = {}
        def start(status, response_headers):
            response.update(status=int(status.split()[0]), headers=dict(response_headers))
        result = b''.join(application(environ, start))
        return response['status'], json.loads(result), response['headers']

    def test_hosted_patient_and_draft_workflow(self):
        patient, visit = self.encounter()
        self.assertEqual(self.call('state')[0], 401)
        self.assertEqual(self.call('history', {'patient_id': patient['id']}, 'doctor')[0], 403)
        report = self.report()
        self.ok('report/draft', {'id': visit['id'], 'report': report}, 'operator')
        rows = self.ok('reports/drafts', user='operator')
        self.assertEqual(json.loads(rows[0]['report'])['findings'], report['findings'])
        self.ok('report/finalize', {'id': visit['id'], 'report': report}, 'operator')
        self.assertEqual(len(self.ok('reports/completed', user='operator')), 1)
        self.ok('logout', {}, 'operator')
        self.assertEqual(self.call('state', user='operator')[0], 401)

    def test_hosted_origin_rejection(self):
        self.assertEqual(self.call('login', {}, headers={'Origin': 'https://evil.example'})[0], 403)
