from .support import ApiCase


class Analytics(ApiCase):
    def test_final_only_and_scope(self):
        _, one = self.encounter(1)
        self.ok('report/finalize', {'id': one['id'], 'report': self.report()}, 'operator')
        _, two = self.encounter(2, owner='operator2')
        self.ok('report/draft', {'id': two['id'], 'report': self.report()}, 'operator2')
        own = self.ok('analytics', {'period': 'today'}, 'operator2')
        self.assertEqual(own['totals']['completed'], 0)
        self.assertEqual(own['doctors'], [])
        doctor = self.ok('analytics', {'period': 'today'}, 'doctor')
        self.assertEqual([d['id'] for d in doctor['doctors']], [self.doc])
        self.assertEqual(doctor['totals']['completed'], 1)
        for period in ('today', 'week', 'month', 'year', 'custom'):
            data = {'period': period, 'start': '2000-01-01', 'end': '2099-01-01'}
            self.assertEqual(self.ok('analytics', data, 'admin')['totals']['completed'], 1)
        self.assertEqual(self.call('analytics', {'period': 'custom', 'start': '2026-09-02', 'end': '2026-09-01'}, 'admin')[0], 400)
