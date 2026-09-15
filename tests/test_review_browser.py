"""Regression checks for navigation, old records and identity lookup."""
import unittest
from pathlib import Path
from tests.support import ApiCase
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None


@unittest.skipIf(sync_playwright is None, 'Install Playwright for browser checks')
class ReviewBrowser(ApiCase):
    def test_active_screen_old_patient_edit_and_lookup(self):
        old = self.patient(1)
        # Keep the old patient outside the default 100-record state response.
        from backend.database import transaction
        with transaction() as c:
            for n in range(2, 103):
                c.execute("INSERT INTO patients(reg_no,name,created) VALUES(?,?,?)",
                          (f'{n:04d}/2000', f'Archive {n}', '2000-01-01'))
        first = self.ok('token', {'patient_id': old['id']}, 'receptionist')
        self.ok('claim', {'id': first['id']}, 'operator')
        other = self.patient(103)
        pending = self.ok('token', {'patient_id': other['id']}, 'receptionist')
        origin = f'http://127.0.0.1:{self.server.server_port}'
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            errors = []
            def login(role):
                context = browser.new_context(viewport={'width': 1440, 'height': 1000})
                key, value = self.cookies[role].split('=', 1)
                context.add_cookies([{'name': key, 'value': value, 'url': origin}])
                page = context.new_page()
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(origin)
                page.wait_for_selector('#logout')
                return page
            operator = login('operator')
            operator.locator('[data-page="queue"]').click()
            self.assertEqual(operator.locator('[data-start]').count(), 0)
            self.assertEqual(operator.locator('[data-openactive]').count(), 1)
            operator.locator('[data-page="dashboard"]').click()
            self.assertEqual(operator.locator(f'[data-start="{pending["id"]}"]').count(), 1)
            receptionist = login('receptionist')
            receptionist.locator('[data-go="register"]').click()
            self.assertTrue(receptionist.locator('[name="identity"]').evaluate('(el) => el === document.activeElement'))
            receptionist.locator('[name="identity"]').fill('1000000000001')
            receptionist.wait_for_selector('#openMatch')
            # Periodic refresh must not change the record captured by the match link.
            receptionist.wait_for_timeout(3300)
            receptionist.locator('#openMatch').click()
            receptionist.wait_for_selector('#editPatient')
            self.assertIn('Test Patient 1', receptionist.locator('.hero').inner_text())
            receptionist.once('dialog', lambda dialog: dialog.accept('Updated old patient'))
            receptionist.locator('#editPatient').click()
            receptionist.wait_for_function("document.querySelector('.hero h2')?.textContent === 'Updated old patient'")
            receptionist.locator('#back').click()
            receptionist.locator('[name="phone"]').fill('03000000001')
            receptionist.wait_for_selector('#openMatch')
            receptionist.locator('[name="phone"]').fill('03999999999')
            receptionist.wait_for_function("document.querySelector('#matchNotice')?.textContent.includes('No existing record')")
            self.assertEqual(receptionist.locator('#openMatch').count(), 0)
            receptionist.locator('[name="phone"]').fill('03000000001')
            receptionist.locator('[data-page="dashboard"]').click()
            receptionist.wait_for_timeout(600)
            self.assertTrue(receptionist.locator('.app-company-footer').is_visible())
            self.assertEqual(errors, [])
            Path('artifacts').mkdir(exist_ok=True)
            operator.screenshot(path='artifacts/review-pending-queue.png', full_page=True)
            browser.close()

    def test_duplicate_identity_and_phone_show_last_echo(self):
        patient, visit = self.encounter()
        self.ok('report/finalize', {'id': visit['id'], 'report': self.report()}, 'operator')
        from backend.database import transaction
        with transaction() as c:
            c.execute("UPDATE visits SET finalized='2026-08-12T10:30:00' WHERE id=?", (visit['id'],))
            # Legacy records may store phone digits without the input mask's hyphen.
            c.execute("UPDATE patients SET phone='03000000001' WHERE id=?", (patient['id'],))
        origin = f'http://127.0.0.1:{self.server.server_port}'
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            key, value = self.cookies['receptionist'].split('=', 1)
            context.add_cookies([{'name': key, 'value': value, 'url': origin}])
            page = context.new_page()
            page.goto(origin)
            page.wait_for_selector('#logout')
            page.locator('[data-go="register"]').click()
            for field, value in [('identity', '1000000000001'), ('phone', '03000000001'), ('phone', '0300-0000001')]:
                page.locator('[name="identity"]').fill('')
                page.locator('[name="phone"]').fill('')
                page.locator(f'[name="{field}"]').fill(value)
                page.wait_for_selector('#openMatch')
                notice = page.locator('#matchNotice').inner_text()
                self.assertIn('Test Patient 1', notice)
                self.assertIn(patient['reg_no'], notice)
                expected = page.evaluate("fmtDate('2026-08-12T10:30:00')")
                self.assertIn('Last echo: ' + expected, notice)
            page.screenshot(path='artifacts/duplicate-patient-echo.png', full_page=True)
            browser.close()
