from .support import ApiCase


class Permissions(ApiCase):
    def test_role_matrix_and_no_patient_leaks(self):
        self.encounter()
        forbidden = {'admin': ['patients', 'patient-edit', 'token', 'claim', 'permission', 'report', 'history'], 'receptionist': ['claim', 'permission', 'report', 'analytics', 'users', 'settings'], 'operator': ['patients', 'patient-edit', 'users', 'doctors', 'settings'], 'doctor': ['patients', 'history', 'patient', 'token', 'claim', 'report', 'users']}
        for role, paths in forbidden.items():
            for path in paths:
                with self.subTest(role=role, path=path):
                    self.assertEqual(self.call(path, {}, role)[0], 403)
        for role in ('admin', 'doctor'):
            state = self.ok('state', user=role)
            for key in ('patients', 'waiting', 'active', 'drafts', 'history', 'issued'):
                self.assertEqual(state[key], [])

    def test_auth_origin_methods_and_cookie(self):
        self.assertEqual(self.call('state')[0], 401)
        self.assertEqual(self.call('settings', {}, 'admin', {'Origin': 'http://bad.example'})[0], 403)
        self.assertEqual(self.call('settings', user='admin')[0], 404)
        self.assertEqual(self.call('setup', {'name': 'x'})[0], 400)
        headers = self.login('operator')
        self.assertIn('HttpOnly', headers['Set-Cookie'])
        self.assertIn('SameSite=Strict', headers['Set-Cookie'])
        self.ok('logout', {}, 'operator')
        self.assertEqual(self.call('state', user='operator')[0], 401)
