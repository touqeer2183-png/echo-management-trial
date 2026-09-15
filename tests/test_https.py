"""HTTPS proxy compatibility; all API records use a temporary database."""
from unittest.mock import patch
from backend import config, security
from .support import ApiCase


class HttpsOrigin(ApiCase):
    def test_https_login_and_cross_origin_rejection(self):
        with patch.object(config, 'PUBLIC_ORIGIN', 'https://echo.example.com'):
            status, body, headers = self.call('login',
                {'username': 'operator', 'password': 'test-password'},
                headers={'Origin': 'https://echo.example.com'})
            self.assertEqual(status, 200, body)
            self.assertIn('; Secure', headers['Set-Cookie'])
            self.assertIn('; Secure', security.cookie())
            for origin in ('http://echo.example.com', 'https://evil.example'):
                status, _, _ = self.call('login', {}, headers={
                    'Origin': origin, 'X-Forwarded-Proto': 'https',
                    'X-Forwarded-Host': 'echo.example.com'})
                self.assertEqual(status, 403)

    def test_local_http_cookie_still_works(self):
        with patch.object(config, 'PUBLIC_ORIGIN', ''):
            self.assertNotIn('; Secure', self.login('operator')['Set-Cookie'])
