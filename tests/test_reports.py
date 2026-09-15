import json
from .support import ApiCase


class Reports(ApiCase):
    def test_final_lock_snapshot_and_legacy_route(self):
        p, v = self.encounter()
        report = self.report()
        self.assertEqual(self.call('report/finalize', {'id': v['id'], 'report': {**report, 'conclusion': ''}}, 'operator')[0], 400)
        self.ok('report', {'id': v['id'], 'report': report, 'final': True}, 'operator')
        before = self.ok('history', {'id': p['id']}, 'operator')[0]['report']
        self.ok('patient-edit', {'id': p['id'], 'name': 'Changed Later'}, 'receptionist')
        self.assertEqual(self.call('report', {'id': v['id'], 'report': report}, 'operator')[0], 400)
        after = self.ok('history', {'id': p['id']}, 'operator')[0]['report']
        self.assertEqual(before, after)
        self.assertEqual(json.loads(after)['patient']['name'], 'Test Patient 1')

    def test_stamp_validation(self):
        for stamp in ('data:image/svg+xml;base64,PHN2Zz4=', 'data:image/png;base64,bm90cG5n'):
            self.assertEqual(self.call('doctors', {'name': 'Bad stamp', 'stamp_image': stamp}, 'admin')[0], 400)
