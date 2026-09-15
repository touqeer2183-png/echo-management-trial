import datetime
from .support import ApiCase
from backend.database import transaction


class Patients(ApiCase):
    def test_adult_uniqueness_child_reuse_and_search(self):
        self.patient()
        self.assertEqual(self.call('patients', {'name': 'Missing fields'}, 'receptionist')[0], 400)
        for changes in ({'identity': '1000000000001'}, {'phone': '03000000001'}):
            with self.assertRaises(AssertionError):
                self.patient(2, **changes)
        self.patient(3, is_minor=True, identity='1000000000001', phone='03000000001', guardian_name='Parent')
        self.patient(4, is_minor=True, identity='1000000000001', phone='03000000001', guardian_name='Parent')
        rows = self.ok('state?q=10000-0000000-1', user='receptionist')['patients']
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]['phone'], '0300-0000001')
        self.assertEqual(rows[0]['address'], '')

    def test_registration_uses_max_and_year(self):
        year = datetime.date.today().year
        p = self.patient()
        self.assertEqual(p['reg_no'], f'0001/{year}')
        with transaction() as c:
            c.execute('UPDATE patients SET reg_no=? WHERE id=?', (f'0009/{year}', p['id']))
        self.assertEqual(self.patient(2)['reg_no'], f'0010/{year}')
        with transaction() as c:
            c.execute('UPDATE patients SET reg_no=replace(reg_no,?,?)', (str(year), str(year-1)))
        self.assertEqual(self.patient(3)['reg_no'], f'0001/{year}')

    def test_edits_are_validated(self):
        p = self.patient()
        self.assertEqual(self.call('patient-edit', {'id': p['id'], 'name': ''}, 'receptionist')[0], 400)
        self.assertEqual(self.call('patient-edit', {'id': p['id'], 'relation_type': 'bad'}, 'receptionist')[0], 400)
