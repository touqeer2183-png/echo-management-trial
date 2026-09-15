import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from backend import config
from backend.migrations import init
from backend.database import transaction


class Database(unittest.TestCase):
    def test_copied_database_preserves_all_existing_rows_and_final_json(self):
        backup = sorted((config.ROOT / 'backups').glob('*/echo-consistent.sqlite3'))
        if not backup:
            self.skipTest('Local upgrade backup is not distributed')
        previous = config.DB
        with tempfile.TemporaryDirectory() as temp:
            config.DB = Path(temp) / 'echo.sqlite3'
            src = sqlite3.connect(backup[-1]); dst = sqlite3.connect(config.DB)
            src.backup(dst); src.close(); dst.close()
            c = sqlite3.connect(config.DB)
            tables = ('patients', 'visits', 'users', 'doctors', 'settings', 'audit')
            counts = {t: c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in tables}
            finals = c.execute("SELECT id,report FROM visits WHERE status='final' ORDER BY id").fetchall()
            c.close()
            try:
                init(); init()
                with transaction(False) as c:
                    self.assertEqual(counts, {t: c.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in tables})
                    self.assertEqual(finals, [tuple(r) for r in c.execute("SELECT id,report FROM visits WHERE status='final' ORDER BY id")])
                    self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            finally:
                config.DB = previous

    def test_only_saved_legacy_drafts_migrate(self):
        previous = config.DB
        with tempfile.TemporaryDirectory() as temp:
            config.DB = Path(temp) / 'echo.sqlite3'
            try:
                init()
                with transaction() as c:
                    c.execute("INSERT INTO visits(id,status,assigned_operator,report) VALUES(1,'in_progress','One',?)", (json.dumps({'values': {}}),))
                    c.execute("INSERT INTO visits(id,status,assigned_operator) VALUES(2,'in_progress','One')")
                    c.execute('DELETE FROM schema_migrations WHERE version=2')
                init()
                with transaction(False) as c:
                    self.assertEqual([r[0] for r in c.execute('SELECT status FROM visits ORDER BY id')], ['draft', 'in_progress'])
            finally:
                config.DB = previous
