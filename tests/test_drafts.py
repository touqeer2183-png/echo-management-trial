from .support import ApiCase
from backend import security
from backend.migrations import init


class Drafts(ApiCase):
    def test_draft_privacy_persistence_and_finalization(self):
        p, v = self.encounter()
        report = self.report()
        self.ok('report/draft', {'id': v['id'], 'report': report}, 'operator')
        self.assertEqual(self.ok('reports/drafts', user='operator2'), [])
        for user in ('operator2', 'receptionist'):
            self.assertIsNone(self.ok('history', {'id': p['id']}, user)[0]['report'])
        self.assertEqual(self.call('report/draft', {'id': v['id'], 'report': report}, 'operator2')[0], 403)
        self.assertEqual(self.call('token', {'patient_id': p['id']}, 'receptionist')[0], 400)
        self.assertEqual(self.call('release', {'id': v['id']}, 'operator')[0], 400)
        self.ok('logout', {}, 'operator')
        security.SESSIONS.clear()
        init()
        self.login('operator')
        rows = self.ok('reports/drafts', user='operator')
        self.assertEqual(rows[0]['status'], 'draft')
        import json
        restored = json.loads(rows[0]['report'])
        for key in report:
            self.assertEqual(str(restored[key]), str(report[key]))
        self.ok('report/finalize', {'id': v['id'], 'report': report}, 'operator')
        self.assertEqual(self.ok('reports/drafts', user='operator'), [])
        self.assertEqual(len(self.ok('reports/completed', user='operator')), 1)

    def test_cannot_save_unclaimed_or_other_operators_echo(self):
        p = self.patient()
        v = self.ok('token', {'patient_id': p['id']}, 'receptionist')
        self.assertEqual(self.call('report', {'id': v['id'], 'report': self.report()}, 'operator')[0], 403)
