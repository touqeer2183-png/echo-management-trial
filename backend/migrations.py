import datetime
import json
from . import config
from .database import transaction

def cols(c, t):
    return {r[1] for r in c.execute(f'PRAGMA table_info({t})')}

def addcol(c, t, n, d):
    if n not in cols(c, t):
        c.execute(f'ALTER TABLE {t} ADD COLUMN {n} {d}')

def migration_001(c):
    for statement in "\n  CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT NOT NULL,username TEXT UNIQUE NOT NULL,password TEXT NOT NULL,salt TEXT NOT NULL,role TEXT NOT NULL,doctor_id INTEGER,active INTEGER DEFAULT 1);\n  CREATE TABLE IF NOT EXISTS patients(id INTEGER PRIMARY KEY,reg_no TEXT UNIQUE,name TEXT NOT NULL,relation_type TEXT,relation_name TEXT,identity TEXT,phone TEXT,age TEXT,sex TEXT,address TEXT,is_minor INTEGER DEFAULT 0,guardian_name TEXT,guardian_identity TEXT,guardian_phone TEXT,created TEXT,updated TEXT);\n  CREATE TABLE IF NOT EXISTS visits(id INTEGER PRIMARY KEY,patient_id INTEGER REFERENCES patients(id),token_no INTEGER,token_date TEXT,created TEXT,creator TEXT,status TEXT DEFAULT 'waiting',assigned_operator TEXT,started TEXT,override_reason TEXT,override_by TEXT,allowed_date TEXT,report TEXT,operator TEXT,doctor_id INTEGER,finalized TEXT);\n  CREATE TABLE IF NOT EXISTS doctors(id INTEGER PRIMARY KEY,name TEXT NOT NULL,qualification TEXT,registration TEXT,stamp_image TEXT);\n  CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY,months INTEGER NOT NULL DEFAULT 1);\n  CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,time TEXT,user TEXT,action TEXT);\n  INSERT OR IGNORE INTO settings(id,months) VALUES(1,1);\n  ".split(';'):
        if statement.strip():
            c.execute(statement)
    for n, d in [('doctor_id', 'INTEGER'), ('active', 'INTEGER DEFAULT 1')]:
        addcol(c, 'users', n, d)
    for n, d in [('reg_no', 'TEXT'), ('relation_type', 'TEXT'), ('relation_name', 'TEXT'), ('address', 'TEXT'), ('is_minor', 'INTEGER DEFAULT 0'), ('guardian_name', 'TEXT'), ('guardian_identity', 'TEXT'), ('guardian_phone', 'TEXT'), ('updated', 'TEXT')]:
        addcol(c, 'patients', n, d)
    for n, d in [('token_no', 'INTEGER'), ('token_date', 'TEXT'), ('assigned_operator', 'TEXT'), ('started', 'TEXT'), ('override_by', 'TEXT'), ('allowed_date', 'TEXT'), ('doctor_id', 'INTEGER')]:
        addcol(c, 'visits', n, d)
    for n, d in [('months', 'INTEGER DEFAULT 1')]:
        addcol(c, 'settings', n, d)

def migration_002(c):
    for row in c.execute("SELECT id,report FROM visits WHERE status='in_progress' AND assigned_operator IS NOT NULL AND report IS NOT NULL"):
        try:
            report = json.loads(row['report'])
        except (ValueError, TypeError):
            continue
        if isinstance(report, dict) and report:
            c.execute("UPDATE visits SET status='draft' WHERE id=?", (row['id'],))
    for row in c.execute("SELECT id,created FROM patients WHERE reg_no IS NULL OR reg_no='' ORDER BY id"):
        try:
            year = datetime.datetime.fromisoformat(row['created']).year
        except (ValueError, TypeError):
            year = datetime.date.today().year
        seq = c.execute("SELECT COALESCE(MAX(CAST(substr(reg_no,1,instr(reg_no,'/')-1) AS INTEGER)),0)+1 FROM patients WHERE reg_no LIKE ?", (f'%/{year}',)).fetchone()[0]
        c.execute('UPDATE patients SET reg_no=? WHERE id=?', (f'{seq:04d}/{year}', row['id']))
    addcol(c, 'doctors', 'stamp_image', 'TEXT')
    addcol(c, 'visits', 'assigned_operator_id', 'INTEGER')
    addcol(c, 'visits', 'operator_id', 'INTEGER')
    for column, old in [('assigned_operator_id', 'assigned_operator'), ('operator_id', 'operator')]:
        c.execute(f"UPDATE visits SET {column}=(SELECT id FROM users WHERE name=visits.{old} AND role='operator') WHERE {column} IS NULL AND (SELECT count(*) FROM users WHERE name=visits.{old} AND role='operator')=1")
    c.execute('CREATE TABLE IF NOT EXISTS early_permissions (id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patients(id), reason TEXT NOT NULL, allowed_date TEXT NOT NULL, operator_id INTEGER NOT NULL REFERENCES users(id), operator_name TEXT NOT NULL, created TEXT NOT NULL, consumed_visit_id INTEGER REFERENCES visits(id))')
    for row in c.execute("SELECT v.* FROM visits v WHERE status='final' AND override_reason<>'' AND allowed_date IS NOT NULL AND id=(SELECT MAX(id) FROM visits WHERE patient_id=v.patient_id)"):
        actor = c.execute("SELECT id FROM users WHERE name=? AND role='operator'", (row['override_by'],)).fetchall()
        proof = c.execute('SELECT time FROM audit WHERE action=? AND user=? AND time>? ORDER BY time DESC LIMIT 1', ('Early echo permission patient ' + str(row['patient_id']), row['override_by'], row['finalized'])).fetchone()
        if len(actor) == 1 and proof:
            c.execute('INSERT INTO early_permissions(patient_id,reason,allowed_date,operator_id,operator_name,created) VALUES(?,?,?,?,?,?)', (row['patient_id'], row['override_reason'], row['allowed_date'], actor[0]['id'], row['override_by'], proof['time']))
    c.execute('CREATE INDEX IF NOT EXISTS visits_status_owner ON visits(status,assigned_operator_id)')
    c.execute('CREATE INDEX IF NOT EXISTS visits_patient ON visits(patient_id,id)')

def migration_003(c):
    addcol(c, 'visits', 'ordered_by', 'TEXT')
    addcol(c, 'visits', 'report_revision', 'INTEGER NOT NULL DEFAULT 0')
    c.execute("CREATE TABLE IF NOT EXISTS report_revisions (id INTEGER PRIMARY KEY, visit_id INTEGER NOT NULL REFERENCES visits(id), revision INTEGER NOT NULL, previous_report TEXT NOT NULL, replacement_report TEXT NOT NULL, reason TEXT NOT NULL, operator_id INTEGER NOT NULL REFERENCES users(id), created TEXT NOT NULL, UNIQUE(visit_id, revision))")


def init():
    config.DB.parent.mkdir(parents=True, exist_ok=True)
    with transaction() as c:
        c.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied TEXT NOT NULL)')
        for version, migration in [(1, migration_001), (2, migration_002), (3, migration_003)]:
            if not c.execute('SELECT 1 FROM schema_migrations WHERE version=?', (version,)).fetchone():
                migration(c)
                c.execute('INSERT INTO schema_migrations VALUES(?,?)', (version, datetime.datetime.now(datetime.timezone.utc).isoformat()))
