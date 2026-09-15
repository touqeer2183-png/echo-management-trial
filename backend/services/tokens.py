from .common import today, now, audit
from .patients import get
from .repeat_policy import eligibility

def create(c,u,d):
    pid=int(d['patient_id']); p=get(c,pid)
    if c.execute("SELECT id FROM visits WHERE patient_id=? AND status IN ('waiting','in_progress','draft')",(pid,)).fetchone():
        raise ValueError('Patient already has an active token')
    reason = str(d.get('reason') or '').strip()
    ordered_by = str(d.get('ordered_by') or '').strip()
    if len(reason) > 500 or len(ordered_by) > 120:
        raise ValueError('Reason must be at most 500 characters; Ordered by at most 120')
    try:
        permission=eligibility(c,pid)
    except ValueError:
        if len(reason) < 5 or not ordered_by:
            raise ValueError('Early echo: enter a reason (at least 5 characters) and Ordered by, or obtain a saved Operator permission.')
        permission={'id': None, 'reason': reason, 'operator_name': u['name'], 'allowed_date': today()}
    order = ordered_by if permission else None
    if permission and not order:
        order = permission['operator_name']
    date=today()
    seq=c.execute('SELECT COALESCE(MAX(token_no),0)+1 FROM visits WHERE token_date=?',(date,)).fetchone()[0]
    cur=c.execute("INSERT INTO visits(patient_id,token_no,token_date,created,creator,status,override_reason,override_by,allowed_date,ordered_by) VALUES(?,?,?,?,?,'waiting',?,?,?,?)",(pid,seq,date,now(),u['name'],permission['reason'] if permission else None,permission['operator_name'] if permission else None,permission['allowed_date'] if permission else None,order))
    # All older grants are superseded; no stale permission can authorize a later visit.
    c.execute('UPDATE early_permissions SET consumed_visit_id=? WHERE patient_id=? AND consumed_visit_id IS NULL',(cur.lastrowid,pid))
    audit(c,u['name'],f'Issued token {seq:02d} patient {p["reg_no"]}; permission '+str(permission['id'] if permission else 'none') + (f'; reason: {permission["reason"]}; ordered by: {order}' if permission else ''))
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
