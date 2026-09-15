"""One-time extraction from the supplied, backed-up trial release."""
import ast
from pathlib import Path
import textwrap

ROOT = Path(__file__).resolve().parents[1]
SOURCE = sorted((ROOT / 'backups').glob('*/zip-server.py'))[-1].read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)
HANDLER = next(n for n in TREE.body if isinstance(n, ast.ClassDef))

def write(path, content):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(content).lstrip(), encoding='utf-8')

def extract(name, method=False):
    nodes = HANDLER.body if method else TREE.body
    node = next(n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == name)
    code = ast.unparse(node)
    if method:
        code = code.replace('(self, ', '(').replace('self.need(', 'need(').replace('self.sendj(', 'result(')
    return code + '\n'

for package in ['backend', 'backend/services', 'backend/routes', 'tests']:
    write(package + '/__init__.py', '"""Afzal Heart Centre echo system."""\n')

write('backend/config.py', '''
    """Deployment settings; tests may override DB before initialization."""
    import os
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[1]
    PUBLIC = ROOT / 'public'
    DB = Path(os.environ.get('ECHO_DB', str(ROOT / 'data' / 'echo.sqlite3')))
    PORT = int(os.environ.get('PORT', '8765'))
    SESSION_SECONDS = 28800
    REQUEST_LIMIT = 500000
    STAMP_LIMIT = 250000
    IMAGE_MIMES = ('image/png', 'image/jpeg')
''')
write('backend/database.py', '''
    """Central SQLite connections and serialized, atomic write transactions."""
    import sqlite3
    import threading
    from contextlib import contextmanager
    from . import config
    LOCK = threading.RLock()

    def connect():
        c = sqlite3.connect(config.DB, timeout=20)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA foreign_keys=ON')
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('PRAGMA busy_timeout=20000')
        return c

    @contextmanager
    def transaction(write=True):
        with LOCK:
            c = connect()
            try:
                c.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
                yield c
                c.commit()
            except Exception:
                c.rollback()
                raise
            finally:
                c.close()
''')
write('backend/permissions.py', '''
    """The single backend feature/role permission map."""
    PERMISSIONS = {
        'accounts': {'admin'}, 'doctors': {'admin'}, 'settings': {'admin'},
        'patients': {'receptionist'}, 'search': {'receptionist', 'operator'},
        'token': {'receptionist', 'operator'}, 'permission': {'operator'},
        'claim': {'operator'}, 'report': {'operator'},
        'analytics': {'admin', 'operator', 'doctor'},
    }

    def require(user, feature):
        need(user, *PERMISSIONS[feature])

    def need(user, *roles):
        if user['role'] not in roles:
            raise PermissionError('Access not allowed for this account')
''')
write('backend/services/common.py', 'import datetime\n' + extract('now') + extract('today') + extract('audit') + '''
def result(value):
    return value
''')
write('backend/security.py', '''
    """Password hashes, expiring sessions and HTTP request protections."""
    import datetime
    import hashlib
    import hmac
    import secrets
    from http.cookies import SimpleCookie, CookieError
    from .config import SESSION_SECONDS, REQUEST_LIMIT
    SESSIONS = {}

    def password(value, salt):
        return hashlib.pbkdf2_hmac('sha256', value.encode(), bytes.fromhex(salt), 300000).hex()

    def create_session(row):
        token = secrets.token_urlsafe(32)
        SESSIONS[token] = {key: row[key] for key in ('id', 'name', 'role', 'doctor_id')}
        SESSIONS[token]['expires'] = datetime.datetime.now().timestamp() + SESSION_SECONDS
        return token

    def session(headers, c):
        try:
            cookie = SimpleCookie(headers.get('Cookie', '')).get('session')
        except CookieError:
            return None, None
        token = cookie.value if cookie else None
        user = SESSIONS.get(token)
        if user:
            row = c.execute('SELECT active FROM users WHERE id=?', (user['id'],)).fetchone()
            if user['expires'] < datetime.datetime.now().timestamp() or not row or not row['active']:
                SESSIONS.pop(token, None)
                user = None
        return user, token

    def cookie(token=''):
        age = SESSION_SECONDS if token else 0
        return f'session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={age}'

    def check_origin(headers):
        origin = headers.get('Origin')
        if origin and origin != 'http://' + headers.get('Host', ''):
            raise PermissionError('Invalid origin')

    def request_length(headers):
        if headers.get('Transfer-Encoding'):
            raise ValueError('Transfer encoding is not supported')
        n = int(headers.get('Content-Length', 0))
        if not 0 <= n <= REQUEST_LIMIT:
            raise ValueError('Request too large or invalid content length')
        return n
''')
write('backend/validators.py', '''
    """Input normalization shared by creation and editing."""
    import base64
    import datetime
    import re
    from .config import STAMP_LIMIT, IMAGE_MIMES

    def patient(data):
        d = dict(data)
        for key in ('name', 'identity', 'phone', 'relation_type', 'relation_name', 'guardian_name', 'address', 'age', 'sex'):
            d[key] = str(d.get(key) or '').strip()
        d['is_minor'] = d.get('is_minor') in (True, 1, '1')
        if not d['name']:
            raise ValueError('Patient name required')
        ident = re.sub(r'\\D', '', d['identity'])
        phone = re.sub(r'\\D', '', d['phone'])
        if not re.fullmatch(r'\\d{13}', ident):
            raise ValueError('CNIC format 00000-0000000-0 required')
        if not re.fullmatch(r'03\\d{9}', phone):
            raise ValueError('Phone format 0300-0000000 required')
        d['identity'] = f'{ident[:5]}-{ident[5:12]}-{ident[12:]}'
        d['phone'] = f'{phone[:4]}-{phone[4:]}'
        if d['relation_type'] not in ('S/O', 'W/O', 'D/O') or not d['relation_name']:
            raise ValueError('Select S/O, W/O or D/O and enter related person name')
        if d['is_minor'] and not d['guardian_name']:
            raise ValueError('Guardian name required for child')
        if not d['age'] or d['sex'] not in ('Male', 'Female', 'Other'):
            raise ValueError('Age and sex are required')
        return d

    def months(value):
        n = int(value)
        if not 1 <= n <= 120:
            raise ValueError('Interval must be 1-120 months')
        return n

    def allowed_date(value):
        date = datetime.date.fromisoformat(value)
        if date < datetime.date.today():
            raise ValueError('Allowed date cannot be in the past')
        return date.isoformat()

    def stamp(value):
        if not value:
            return ''
        if not isinstance(value, str) or ',' not in value:
            raise ValueError('Invalid stamp image')
        header, encoded = value.split(',', 1)
        if header not in tuple('data:' + mime + ';base64' for mime in IMAGE_MIMES):
            raise ValueError('Stamp must be PNG or JPEG')
        try:
            image = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError):
            raise ValueError('Invalid stamp encoding')
        valid = image.startswith(b'\\x89PNG\\r\\n\\x1a\\n') if 'png' in header else image.startswith(b'\\xff\\xd8\\xff')
        if not valid or not 0 < len(image) <= STAMP_LIMIT:
            raise ValueError('Stamp must be a PNG/JPEG image under 250 KB')
        return value
''')

# Preserve the original additive table definitions; version later changes separately.
init = extract('init').replace('def init():', 'def migration_001(c):')
body = ast.parse(init).body[0]
body.body = body.body[1].body
init = ast.unparse(body)
init = init[:init.index('    yr =')]
write('backend/migrations.py', '''
import datetime
import json
from . import config
from .database import transaction
''' + extract('cols') + extract('addcol') + init + '''

def migration_002(c):
    # Preserve historical JSON exactly; only classify saved, assigned drafts.
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
    # Only map unambiguous legacy display names. Never assign private work arbitrarily.
    for column, old in [('assigned_operator_id', 'assigned_operator'), ('operator_id', 'operator')]:
        c.execute(f"UPDATE visits SET {column}=(SELECT id FROM users WHERE name=visits.{old} AND role='operator') WHERE {column} IS NULL AND (SELECT count(*) FROM users WHERE name=visits.{old} AND role='operator')=1")
    c.execute('CREATE TABLE IF NOT EXISTS early_permissions (id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patients(id), reason TEXT NOT NULL, allowed_date TEXT NOT NULL, operator_id INTEGER NOT NULL REFERENCES users(id), operator_name TEXT NOT NULL, created TEXT NOT NULL, consumed_visit_id INTEGER REFERENCES visits(id))')
    # Import outstanding permission only when it was granted AFTER the final report.
    # Legacy issuance also stored override_reason, so that field alone is not proof.
    for row in c.execute("SELECT v.* FROM visits v WHERE status='final' AND override_reason<>'' AND allowed_date IS NOT NULL AND id=(SELECT MAX(id) FROM visits WHERE patient_id=v.patient_id)"):
        actor = c.execute("SELECT id FROM users WHERE name=? AND role='operator'", (row['override_by'],)).fetchall()
        proof = c.execute("SELECT time FROM audit WHERE action=? AND user=? AND time>? ORDER BY time DESC LIMIT 1", ('Early echo permission patient '+str(row['patient_id']), row['override_by'], row['finalized'])).fetchone()
        if len(actor)==1 and proof:
            c.execute('INSERT INTO early_permissions(patient_id,reason,allowed_date,operator_id,operator_name,created) VALUES(?,?,?,?,?,?)', (row['patient_id'],row['override_reason'],row['allowed_date'],actor[0]['id'],row['override_by'],proof['time']))
    c.execute('CREATE INDEX IF NOT EXISTS visits_status_owner ON visits(status,assigned_operator_id)')
    c.execute('CREATE INDEX IF NOT EXISTS visits_patient ON visits(patient_id,id)')

def init():
    config.DB.parent.mkdir(parents=True, exist_ok=True)
    with transaction() as c:
        c.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied TEXT NOT NULL)')
        for version, migration in [(1, migration_001), (2, migration_002)]:
            if not c.execute('SELECT 1 FROM schema_migrations WHERE version=?', (version,)).fetchone():
                migration(c)
                c.execute('INSERT INTO schema_migrations VALUES(?,?)', (version, datetime.datetime.now(datetime.timezone.utc).isoformat()))
''')
# executescript implicitly commits; use individual DDL statements inside our transaction.
p=ROOT/'backend/migrations.py'; content=p.read_text(); tree=ast.parse(content)
class DDL(ast.NodeTransformer):
    def visit_Expr(self,n):
        if isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='executescript':
            return ast.For(target=ast.Name(id='statement',ctx=ast.Store()),iter=ast.Call(func=ast.Attribute(value=n.value.args[0],attr='split',ctx=ast.Load()),args=[ast.Constant(';')],keywords=[]),body=ast.parse("if statement.strip():\n c.execute(statement)").body,orelse=[])
        return n
p.write_text(ast.unparse(ast.fix_missing_locations(DDL().visit(tree)))+'\n',encoding='utf-8')

users = extract('add_user', True).replace("if role == 'doctor' and (not doc):", "if role == 'doctor' and (not doc or not c.execute('SELECT id FROM doctors WHERE id=?',(doc,)).fetchone()):")
write('backend/services/users.py', 'import secrets\nfrom ..security import password\n' + users)
write('backend/services/doctors.py', '''
    from ..validators import stamp

    def create(c, d):
        name = str(d.get('name') or '').strip()
        if not name:
            raise ValueError('Doctor name required')
        cur = c.execute('INSERT INTO doctors(name,qualification,registration,stamp_image) VALUES(?,?,?,?)',
                        (name, d.get('qualification', ''), d.get('registration', ''), stamp(d.get('stamp_image', ''))))
        return {'id': cur.lastrowid}
''')
write('backend/services/patients.py', '''
    import datetime
    from ..validators import patient as validate
    from .common import now, audit

    def get(c, pid):
        row = c.execute("SELECT p.*,(SELECT MAX(finalized) FROM visits WHERE patient_id=p.id AND status='final') last_echo FROM patients p WHERE id=?", (int(pid),)).fetchone()
        if not row:
            raise ValueError('Patient not found')
        return dict(row)

    def search(c, query='', limit=100, offset=0):
        s = '%' + query.strip() + '%'
        return [dict(r) for r in c.execute("SELECT p.*,(SELECT MAX(finalized) FROM visits WHERE patient_id=p.id AND status='final') last_echo FROM patients p WHERE name LIKE ? OR reg_no LIKE ? OR identity LIKE ? OR guardian_identity LIKE ? OR phone LIKE ? OR guardian_phone LIKE ? OR replace(identity,'-','') LIKE ? OR replace(guardian_identity,'-','') LIKE ? OR replace(phone,'-','') LIKE ? OR replace(guardian_phone,'-','') LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?", (s,)*10+(limit,offset))]

    def unique(c, d, pid=0):
        if not d['is_minor']:
            for key in ('identity','phone'):
                if c.execute(f"SELECT id FROM patients WHERE COALESCE(is_minor,0)=0 AND replace({key},'-','')=? AND id<>?", (d[key].replace('-',''),pid)).fetchone():
                    raise ValueError('This '+ ('CNIC' if key=='identity' else 'phone') +' is already registered')

    def create(c, u, data):
        d = validate(data)
        unique(c,d)
        year = datetime.date.today().year
        seq = c.execute("SELECT COALESCE(MAX(CAST(substr(reg_no,1,instr(reg_no,'/')-1) AS INTEGER)),0)+1 FROM patients WHERE reg_no LIKE ?", (f'%/{year}',)).fetchone()[0]
        reg = f'{seq:04d}/{year}'
        minor = d['is_minor']
        cur = c.execute('INSERT INTO patients(reg_no,name,relation_type,relation_name,identity,phone,age,sex,address,is_minor,guardian_name,guardian_identity,guardian_phone,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (reg,d['name'],d['relation_type'],d['relation_name'],None if minor else d['identity'],d['phone'],d['age'],d['sex'],d['address'],int(minor),d['guardian_name'] if minor else None,d['identity'] if minor else None,d['phone'] if minor else None,now(),now()))
        audit(c,u['name'],'Registered patient '+reg)
        return {'id':cur.lastrowid,'reg_no':reg}

    def edit(c,u,data):
        pid = int(data['id'])
        old = get(c,pid)
        old['identity'] = old['identity'] or old['guardian_identity']
        d = validate({**old,**data})
        unique(c,d,pid)
        minor=d['is_minor']
        c.execute('UPDATE patients SET name=?,relation_type=?,relation_name=?,identity=?,phone=?,age=?,sex=?,address=?,is_minor=?,guardian_name=?,guardian_identity=?,guardian_phone=?,updated=? WHERE id=?', (d['name'],d['relation_type'],d['relation_name'],None if minor else d['identity'],d['phone'],d['age'],d['sex'],d['address'],int(minor),d['guardian_name'] if minor else None,d['identity'] if minor else None,d['phone'] if minor else None,now(),pid))
        audit(c,u['name'],'Edited patient '+str(pid))
        return {'ok':True}

    def history(c,u,pid):
        get(c,pid)
        rows=[dict(r) for r in c.execute('SELECT * FROM visits WHERE patient_id=? ORDER BY id DESC',(int(pid),))]
        for row in rows:
            if row['status']!='final' and (u['role']!='operator' or row['assigned_operator_id']!=u['id']):
                row['report']=None
        return rows
''')
write('backend/services/repeat_policy.py', 'import datetime, calendar\nfrom ..validators import allowed_date\nfrom .common import today, now, audit\n' + extract('add_months') + '''
def grant(c,u,d):
    pid=int(d['patient_id']); reason=str(d.get('reason') or '').strip()
    date=allowed_date(d.get('allowed_date') or today())
    if len(reason)<5:
        raise ValueError('Permission reason required (at least 5 characters)')
    if not c.execute('SELECT id FROM patients WHERE id=?',(pid,)).fetchone():
        raise ValueError('Patient not found')
    if not c.execute("SELECT id FROM visits WHERE patient_id=? AND status='final'",(pid,)).fetchone():
        raise ValueError('No previous completed echo requires permission')
    if c.execute("SELECT id FROM visits WHERE patient_id=? AND status IN ('waiting','in_progress','draft')",(pid,)).fetchone():
        raise ValueError('Patient already has an active token')
    c.execute('INSERT INTO early_permissions(patient_id,reason,allowed_date,operator_id,operator_name,created) VALUES(?,?,?,?,?,?)',(pid,reason,date,u['id'],u['name'],now()))
    audit(c,u['name'],f'Early echo permission patient {pid}: {reason}; allowed {date}')
    return {'ok':True}

def eligibility(c,pid):
    last=c.execute("SELECT finalized FROM visits WHERE patient_id=? AND status='final' ORDER BY finalized DESC LIMIT 1",(pid,)).fetchone()
    months=c.execute('SELECT months FROM settings WHERE id=1').fetchone()[0]
    if last:
        date=datetime.datetime.fromisoformat(last['finalized'])
        if date.tzinfo is None: date=date.replace(tzinfo=datetime.timezone.utc)
        if datetime.datetime.now(datetime.timezone.utc)<add_months(date,months):
            permission=c.execute('SELECT * FROM early_permissions WHERE patient_id=? AND consumed_visit_id IS NULL ORDER BY id DESC LIMIT 1',(pid,)).fetchone()
            if not permission or permission['allowed_date']>today():
                raise ValueError(f'Repeat echo blocked for {months} month(s). Saved Operator permission is required.')
            return permission
    return None
''')
write('backend/services/tokens.py', '''
    from .common import today, now, audit
    from .patients import get
    from .repeat_policy import eligibility

    def create(c,u,d):
        pid=int(d['patient_id']); p=get(c,pid)
        if c.execute("SELECT id FROM visits WHERE patient_id=? AND status IN ('waiting','in_progress','draft')",(pid,)).fetchone():
            raise ValueError('Patient already has an active token')
        permission=eligibility(c,pid)
        date=today()
        seq=c.execute('SELECT COALESCE(MAX(token_no),0)+1 FROM visits WHERE token_date=?',(date,)).fetchone()[0]
        cur=c.execute("INSERT INTO visits(patient_id,token_no,token_date,created,creator,status,override_reason,override_by,allowed_date) VALUES(?,?,?,?,?,'waiting',?,?,?)",(pid,seq,date,now(),u['name'],permission['reason'] if permission else None,permission['operator_name'] if permission else None,permission['allowed_date'] if permission else None))
        # All older grants are superseded; no stale permission can authorize a later visit.
        c.execute('UPDATE early_permissions SET consumed_visit_id=? WHERE patient_id=? AND consumed_visit_id IS NULL',(cur.lastrowid,pid))
        audit(c,u['name'],f'Issued token {seq:02d} patient {p["reg_no"]}; permission '+str(permission['id'] if permission else 'none'))
        return {'id':cur.lastrowid,'token_no':seq}

    def claim(c,u,d):
        vid=int(d['id'])
        cur=c.execute("UPDATE visits SET status='in_progress',assigned_operator=?,assigned_operator_id=?,started=? WHERE id=? AND status='waiting'",(u['name'],u['id'],now(),vid))
        if cur.rowcount!=1:
            raise ValueError('This token has already been started by another operator')
        audit(c,u['name'],'Started echo '+str(vid))
        return {'ok':True}

    def release(c,u,d):
        vid=int(d['id'])
        cur=c.execute("UPDATE visits SET status='waiting',assigned_operator=NULL,assigned_operator_id=NULL,started=NULL WHERE id=? AND status='in_progress' AND assigned_operator_id=? AND (report IS NULL OR report='')",(vid,u['id']))
        if cur.rowcount!=1:
            raise ValueError('Only your unsaved active echo can be released; a saved draft stays assigned')
        audit(c,u['name'],'Released echo '+str(vid))
        return {'ok':True}
''')
write('backend/services/reports.py', '''
    import json
    from .common import now, audit
    from .patients import get
    from ..validators import stamp

    def save(c,u,d,final=False):
        v=c.execute('SELECT * FROM visits WHERE id=?',(int(d['id']),)).fetchone()
        if not v: raise ValueError('Encounter not found')
        if v['status']=='final': raise ValueError('Final report is locked')
        if v['status'] not in ('in_progress','draft') or v['assigned_operator_id']!=u['id']:
            raise PermissionError('Claim this echo before reporting; only its assigned operator may edit it')
        r=d.get('report')
        if not isinstance(r,dict): raise ValueError('Report must be an object')
        for key in ('findings','conclusion','color'):
            if not isinstance(r.get(key,''),str): raise ValueError(key+' must be text')
        if not isinstance(r.get('values',{}),dict) or any(not isinstance(v,str) for v in r.get('values',{}).values()):
            raise ValueError('Measurements must contain text values')
        for key in ('columns','lines'):
            if not isinstance(r.get(key,[]),list) or any(not isinstance(v,str) for v in r.get(key,[])):
                raise ValueError(key+' must contain text')
        if not isinstance(r.get('rows',[]),list) or any(not isinstance(row,list) or any(not isinstance(v,str) for v in row) for row in r.get('rows',[])):
            raise ValueError('Custom rows must contain text cells')
        doc=int(r.get('doctor_id') or 0)
        dr=c.execute('SELECT * FROM doctors WHERE id=?',(doc,)).fetchone()
        if not dr: raise ValueError('Select reporting doctor')
        if final and not r.get('conclusion','').strip(): raise ValueError('Conclusion required')
        r=dict(r); r['doctor']=dict(dr)
        r['doctor']['stamp_image']=stamp(r['doctor'].get('stamp_image',''))
        # Server-owned snapshots prevent client tampering and later patient edits changing this report.
        old=json.loads(v['report']) if v['report'] else {}
        r['patient']=old.get('patient') or get(c,v['patient_id'])
        previous=c.execute("SELECT MAX(finalized) FROM visits WHERE patient_id=? AND status='final'",(v['patient_id'],)).fetchone()[0]
        r['previous_echo']=old.get('previous_echo',previous)
        c.execute('UPDATE visits SET report=?,operator=?,operator_id=?,doctor_id=?,assigned_operator=?,assigned_operator_id=?,status=?,finalized=? WHERE id=?',(json.dumps(r),u['name'],u['id'],doc,u['name'],u['id'],'final' if final else 'draft',now() if final else None,v['id']))
        audit(c,u['name'],('Finalized' if final else 'Saved draft')+' report '+str(v['id']))
        return {'ok':True}

    def listing(c,u,status):
        query='SELECT v.*,p.name patient_name,p.reg_no FROM visits v JOIN patients p ON p.id=v.patient_id WHERE v.status=?'
        params=[status]
        if status=='draft':
            query+=' AND assigned_operator_id=?';params.append(u['id'])
        return [dict(r) for r in c.execute(query+' ORDER BY v.id DESC LIMIT 100',params)]
''')
analytics=extract('analytics',True).replace('self.', '')
analytics=analytics.replace("if u['role'] == 'operator':\n        operators = [x for x in operators if x['name'] == u['name']]", "if u['role'] == 'operator':\n        operators = [dict(r) for r in c.execute(\"SELECT operator name,count(*) total FROM visits WHERE status='final' AND finalized>=? AND finalized<? AND operator_id=? GROUP BY operator\",(s,e,u['id']))]")
analytics=analytics.replace("return result({'operators':", "if u['role'] != 'admin':\n        totals = {'completed': sum(x['total'] for x in (operators if u['role']=='operator' else doctors))}\n    return result({'operators':")
datefunc=extract('daterange').replace("return (s.isoformat(),", "if e < s:\n        raise ValueError('End date must not precede start date')\n    return (s.isoformat(),")
write('backend/services/analytics.py','import datetime\nfrom ..permissions import need\nfrom .common import result\n'+datefunc+analytics)
