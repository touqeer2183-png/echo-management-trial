import json
from unittest.mock import patch
from .support import ApiCase
from backend.database import transaction


class WorkflowUpdate(ApiCase):
    def test_registration_and_token_are_atomic(self):
        data = dict(name='One click', identity='1234512345671', phone='03012345678', relation_type='S/O', relation_name='Parent', age='40', sex='Male', issue_token=True)
        with patch('backend.routes.patients.tokens.create', side_effect=ValueError('Token failed')):
            self.assertEqual(self.call('patients', data, 'receptionist')[0], 400)
        with transaction(False) as c:
            self.assertEqual(c.execute('SELECT count(*) FROM patients').fetchone()[0], 0)
        result = self.ok('patients', data, 'receptionist')
        self.assertEqual(result['visit']['token_no'], 1)
        self.assertEqual(len(self.ok('history', {'id':result['id']}, 'receptionist')), 1)
        self.assertEqual(self.call('patients', data, 'receptionist')[0], 400)
        self.assertEqual(self.call('patients', data, 'operator')[0], 403)

    def test_early_reception_token_requires_both_details_and_reprints(self):
        patient, visit = self.encounter()
        self.ok('report/finalize', {'id':visit['id'], 'report':self.report()}, 'operator')
        for extra in ({}, {'reason':'Urgent review'}, {'ordered_by':'Dr One'}):
            self.assertEqual(self.call('token', {'patient_id':patient['id'], **extra}, 'receptionist')[0], 400)
        issued = self.ok('token', {'patient_id':patient['id'], 'reason':'Urgent review', 'ordered_by':'Dr One'}, 'receptionist')
        row = next(v for v in self.ok('state', user='receptionist')['issued'] if v['id']==issued['id'])
        self.assertEqual(row['override_reason'], 'Urgent review')
        self.assertEqual(row['ordered_by'], 'Dr One')
        self.assertEqual(row['override_by'], 'receptionist')
        self.assertEqual(self.call('token', {'patient_id':patient['id'], 'reason':'Urgent review', 'ordered_by':'Dr One'}, 'receptionist')[0], 400)

    def test_correction_preserves_previous_version_owner_and_counts(self):
        patient, visit = self.encounter()
        self.ok('report/finalize', {'id':visit['id'], 'report':self.report()}, 'operator')
        before = self.ok('history', {'id':patient['id']}, 'operator')[0]
        data = {'id':visit['id'], 'report':{**self.report(), 'conclusion':'Corrected manual conclusion'}, 'reason':'Corrected transcription', 'expected_revision':0}
        self.assertEqual(self.call('report/amend', data, 'operator2')[0], 403)
        self.assertEqual(self.call('report/amend', {**data, 'reason':''}, 'operator')[0], 400)
        self.ok('report/amend', data, 'operator')
        after = self.ok('history', {'id':patient['id']}, 'operator')[0]
        self.assertEqual(after['status'], 'final')
        self.assertEqual(after['finalized'], before['finalized'])
        self.assertEqual(after['report_revision'], 1)
        self.assertEqual(self.call('report/amend', data, 'operator')[0], 400)
        with transaction(False) as c:
            version = c.execute('SELECT * FROM report_revisions').fetchone()
            self.assertEqual(version['previous_report'], before['report'])
            self.assertEqual(version['replacement_report'], after['report'])
        self.assertEqual(self.ok('analytics', {'period':'today'}, 'operator')['totals']['completed'], 1)

    def test_measurement_tables_validate_and_restore(self):
        patient, visit = self.encounter()
        tables = {'dimensions':{'columns':['Parameter','Result','Reference','Notes'], 'rows':[['Custom parameter','12','mm','Manual']]}, 'doppler':{'columns':['Parameter','Result','Reference'], 'rows':[]}}
        report = {**self.report(), 'measurement_tables':tables}
        self.ok('report/draft', {'id':visit['id'], 'report':report}, 'operator')
        saved = json.loads(self.ok('history', {'id':patient['id']}, 'operator')[0]['report'])
        self.assertEqual(saved['measurement_tables'], tables)
        self.assertEqual(self.call('report/draft', {'id':visit['id'], 'report':{**report, 'measurement_tables':{'dimensions':[]}}}, 'operator')[0], 400)
