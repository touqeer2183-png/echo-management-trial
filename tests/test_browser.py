"""Optional browser workflow checks: python -m unittest tests.test_browser -v."""
from pathlib import Path
from tests.support import ApiCase
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None
import unittest


@unittest.skipIf(sync_playwright is None, 'Install Playwright for optional browser checks')
class Browser(ApiCase):
    def test_roles_drafts_final_print_and_assets(self):
        patient = self.patient()
        encounter = self.ok('token', {'patient_id': patient['id']}, 'receptionist')
        origin = f'http://127.0.0.1:{self.server.server_port}'
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            errors = []
            contexts = []
            def login(name):
                context = browser.new_context(viewport={'width': 1440, 'height': 1050})
                contexts.append(context)
                key, value = self.cookies[name].split('=', 1)
                context.add_cookies([{'name': key, 'value': value, 'url': origin}])
                page = context.new_page()
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(origin)
                page.wait_for_selector('#logout')
                page.evaluate('() => { window.print = () => { window.printCalls = (window.printCalls || 0) + 1; }; }')
                return page
            for role in ('admin', 'doctor'):
                page = login(role)
                self.assertEqual(page.locator('[data-page="patients"]').count(), 0)
                page.evaluate("page='editor';render()")
                self.assertEqual(page.locator('#report').count(), 0)
                page.close()
            reception = login('receptionist')
            reception.locator('[data-page="queue"]').click()
            reception.locator('[data-reprint]').first.click()
            reception.wait_for_selector('.ticket', state='attached')
            self.assertEqual(reception.locator('.ticket').count(), 3)
            self.assertIn(patient['reg_no'], reception.locator('#print').inner_text())
            reception.wait_for_function('window.printCalls === 1')
            self.assertEqual(reception.evaluate('window.printCalls'), 1)
            operator = login('operator')
            other = login('operator2')
            operator.locator('[data-start]').first.click()
            operator.wait_for_selector('#doctor')
            other.wait_for_function('document.querySelectorAll("[data-start]").length === 0')
            expected_panels = [
                ['Aortic Root', 'Annulus AO/PV', 'LA', 'LA Area', 'RV', '2D MV Area'],
                ['LVISD', 'LVPWD', 'LVIDD', 'LVIDS', 'EF', 'FS'],
            ]
            panels = operator.locator('#measurementGroups [data-group]')
            self.assertEqual(panels.count(), 3)
            self.assertEqual(panels.nth(0).locator('thead th').nth(2).inner_text().strip(), 'NORMAL')
            self.assertEqual(panels.nth(0).locator('.measurement-reference').all_text_contents(), ['20-40mm', '', '19-39mm', '', '7-26mm', ''])
            for index, names in enumerate(expected_panels):
                self.assertEqual(panels.nth(index).locator('[data-cell="0"]').evaluate_all('(els) => els.map(el => el.value)'), names)
            self.assertEqual(panels.nth(1).locator('[data-cell="2"]').all_text_contents(), ['8-12mm', '7-11mm', '36-56mm', '25-41mm', '(50-70%)', '(29-37%)'])
            self.assertEqual(operator.locator('#measurementGroups input[data-cell="2"]').count(), 0)
            reference = panels.nth(1).locator('.measurement-reference').first
            self.assertEqual(reference.evaluate('(el) => getComputedStyle(el).pointerEvents'), 'none')
            reference.evaluate('(el) => el.focus()')
            self.assertFalse(reference.evaluate('(el) => el === document.activeElement'))
            boxes = [panels.nth(i).bounding_box() for i in range(3)]
            self.assertTrue(boxes[0]['x'] < boxes[1]['x'] < boxes[2]['x'])
            self.assertEqual(boxes[0]['y'], boxes[2]['y'])
            # Tab moves down the same column, across tables, and exits at the end.
            cells = operator.locator('#measurementGroups input[data-cell="1"]')
            cells.first.focus()
            for index in range(1, cells.count()):
                operator.keyboard.press('Tab')
                self.assertTrue(cells.nth(index).evaluate('(el) => el === document.activeElement'))
            operator.keyboard.press('Tab')
            self.assertTrue(operator.locator('#addrow').evaluate('(el) => el === document.activeElement'))
            cells.last.focus()
            for index in range(cells.count() - 2, -1, -1):
                operator.keyboard.press('Shift+Tab')
                self.assertTrue(cells.nth(index).evaluate('(el) => el === document.activeElement'))
            operator.keyboard.press('Shift+Tab')
            self.assertTrue(operator.locator('#doctor').evaluate('(el) => el === document.activeElement'))
            operator.select_option('#doctor', str(self.doc))
            operator.fill('[data-measure="EF"]', '61')
            operator.fill('[data-measure="FS"]', '33')
            operator.fill('[data-measure="E Wave"]', '80')
            operator.fill('[data-measure="A Wave"]', '60')
            operator.fill('#conclusion', 'Manual browser test conclusion')
            operator.locator('#addrow').click()
            operator.locator('[data-row] input').first.fill('<script>literal text</script>')
            operator.locator('#addline').click()
            operator.locator('[data-line]').fill('Saved custom line')
            operator.locator('#save').click()
            operator.wait_for_selector('[data-draft]')
            self.assertIsNone(operator.evaluate('window.printCalls'))
            operator.reload()
            operator.wait_for_selector('#logout')
            operator.locator('[data-page="drafts"]').click()
            operator.locator('[data-draft]').click()
            operator.wait_for_selector('#conclusion')
            self.assertEqual(operator.input_value('[data-measure="EF"]'), '61')
            self.assertEqual(operator.input_value('[data-measure="FS"]'), '33')
            self.assertEqual(operator.locator('[data-group="dimensions_lv"] .measurement-reference').all_text_contents(), ['8-12mm', '7-11mm', '36-56mm', '25-41mm', '(50-70%)', '(29-37%)'])
            self.assertEqual(operator.input_value('[data-measure="E Wave"]'), '80')
            self.assertEqual(operator.input_value('[data-measure="A Wave"]'), '60')
            self.assertEqual(operator.input_value('[data-line]'), 'Saved custom line')
            self.assertEqual(operator.input_value('#doctor'), str(self.doc))
            operator.evaluate('() => { window.print = () => { window.printCalls = (window.printCalls || 0) + 1; }; }')
            operator.on('dialog', lambda dialog: dialog.accept())
            operator.get_by_role('button', name='Finalize & Print', exact=True).click()
            operator.wait_for_selector('#printReport')
            self.assertTrue(operator.locator('#printReport').is_enabled())
            operator.wait_for_function('window.printCalls === 1')
            self.assertEqual(operator.evaluate('window.printCalls'), 1)
            self.assertEqual(operator.locator('.print-meta').get_by_text('Operator Name:').count(), 0)
            self.assertIn('Created by: operator', operator.locator('#print').inner_text())
            printed = operator.locator('.report-tables > table')
            self.assertEqual(printed.count(), 3)
            self.assertEqual(printed.nth(0).locator('thead tr').nth(1).locator('th').nth(2).text_content(), 'Normal')
            for index, names in enumerate(expected_panels):
                self.assertEqual(printed.nth(index).locator('tbody tr td:first-child').all_text_contents(), names)
            self.assertIn('33', printed.nth(1).inner_text())
            self.assertIn('Saved custom line', operator.locator('#print').inner_text())
            for name, value in [('E Wave', '80'), ('A Wave', '60')]:
                row = operator.locator('#print tr').filter(has_text=name)
                self.assertIn(value, row.inner_text())
                self.assertIn('cm/sec', row.inner_text())
            self.assertEqual(operator.locator('#print script').count(), 0)
            for image in operator.locator('.print-head img').all():
                self.assertTrue(image.evaluate('(img) => img.complete && img.naturalWidth > 0'))
            # Final print continues to use the stored patient snapshot after an edit.
            self.ok('patient-edit', {'id': patient['id'], 'name': 'Changed Name'}, 'receptionist')
            operator.locator('[data-page="historyPage"]').click()
            operator.locator('[data-history]').click()
            operator.locator('#printReport').click()
            self.assertIn('Test Patient 1', operator.locator('.print-meta').inner_text())
            self.assertNotIn('Changed Name', operator.locator('.print-meta').inner_text())
            evidence = Path(__file__).resolve().parents[1] / 'artifacts'
            evidence.mkdir(exist_ok=True)
            operator.screenshot(path=str(evidence / 'completed-report-screen.png'), full_page=True)
            operator.evaluate("document.body.className='printing-report'")
            operator.pdf(path=str(evidence / 'test-report.pdf'), format='A4', prefer_css_page_size=True)
            operator.emulate_media(media='print')
            operator.screenshot(path=str(evidence / 'test-report.png'), full_page=True)
            reception.evaluate("document.body.className='printing-token'")
            reception.pdf(path=str(evidence / 'test-token.pdf'), format='A4', prefer_css_page_size=True)
            reception.emulate_media(media='print')
            reception.screenshot(path=str(evidence / 'test-token.png'), full_page=True)
            self.assertEqual(errors, [])
            for context in contexts: context.close()
            browser.close()
