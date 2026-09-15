import datetime, calendar
from ..validators import allowed_date
from .common import today, now, audit
def add_months(dt, n):
    m = dt.month - 1 + n
    y = dt.year + m // 12
    m = m % 12 + 1
    return dt.replace(year=y, month=m, day=min(dt.day, calendar.monthrange(y, m)[1]))

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
