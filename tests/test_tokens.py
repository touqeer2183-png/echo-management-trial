from concurrent.futures import ThreadPoolExecutor
from .support import ApiCase
from backend.database import transaction


class Tokens(ApiCase):
    def test_concurrent_sequence_and_claim(self):
        patients = [self.patient(n) for n in range(1, 6)]
        with ThreadPoolExecutor(max_workers=5) as pool:
            visits = list(pool.map(lambda p: self.ok('token', {'patient_id': p['id']}, 'receptionist'), patients))
        self.assertEqual(sorted(v['token_no'] for v in visits), [1, 2, 3, 4, 5])
        with ThreadPoolExecutor(max_workers=2) as pool:
            codes = list(pool.map(lambda user: self.call('claim', {'id': visits[0]['id']}, user)[0], ['operator', 'operator2']))
        self.assertEqual(sorted(codes), [200, 400])
        for user in ('operator', 'operator2'):
            self.assertNotIn(visits[0]['id'], [v['id'] for v in self.ok('state', user=user)['waiting']])
        self.assertEqual(self.call('token', {'patient_id': patients[0]['id']}, 'receptionist')[0], 400)
        with transaction() as c:
            c.execute("UPDATE visits SET token_date='2000-01-01'")
        p = self.patient(6)
        self.assertEqual(self.ok('token', {'patient_id': p['id']}, 'operator')['token_no'], 1)

    def test_permission_saved_dated_consumed_and_audited(self):
        p, v = self.encounter()
        self.ok('report/finalize', {'id': v['id'], 'report': self.report()}, 'operator')
        data = {'patient_id': p['id']}
        self.assertEqual(self.call('token', {**data, 'reason': 'Inline bypass'}, 'operator')[0], 400)
        self.ok('permission', {**data, 'reason': 'Manual approval', 'allowed_date': '2099-01-01'}, 'operator')
        self.assertEqual(self.call('token', data, 'receptionist')[0], 400)
        self.ok('permission', {**data, 'reason': 'Manual approval'}, 'operator')
        second = self.ok('token', data, 'receptionist')
        self.ok('claim', {'id': second['id']}, 'operator')
        self.ok('report/finalize', {'id': second['id'], 'report': self.report()}, 'operator')
        self.assertEqual(self.call('token', data, 'operator')[0], 400)
        with transaction(False) as c:
            self.assertEqual(c.execute('SELECT count(*) FROM early_permissions WHERE consumed_visit_id IS NULL').fetchone()[0], 0)
            self.assertGreater(c.execute("SELECT count(*) FROM audit WHERE action LIKE 'Early echo permission%'").fetchone()[0], 0)
