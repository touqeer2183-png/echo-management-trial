"""Role-filtered state; private reports stay behind the service boundary."""
from . import patients, reports
from .common import today


def load(c, u, query='', offset=0):
    role = u['role']
    td = today()
    state = {'patients': [], 'waiting': [], 'active': [], 'drafts': [], 'history': [],
             'issued': [], 'counts': {}, 'users': [], 'doctors': [],
             'today': td,
             'months': c.execute('SELECT months FROM settings WHERE id=1').fetchone()[0]}
    if role != 'doctor':
        queries = {
            'issued_today': ('SELECT count(*) FROM visits WHERE token_date=?', (td,)),
            'pending': ("SELECT count(*) FROM visits WHERE status='waiting' AND token_date=?", (td,)),
            'completed_today': ("SELECT count(*) FROM visits WHERE status='final' AND substr(finalized,1,10)=?", (td,)),
            'in_progress': ("SELECT count(*) FROM visits WHERE status='in_progress'", ()),
            'registered_today': ('SELECT count(*) FROM patients WHERE substr(created,1,10)=?', (td,)),
            'total_patients': ('SELECT count(*) FROM patients', ()),
        }
        state['counts'] = {key: c.execute(sql, args).fetchone()[0] for key, (sql, args) in queries.items()}
    if role in ('receptionist', 'operator'):
        state['patients'] = patients.search(c, query, offset=offset)
        state['waiting'] = [dict(r) for r in c.execute("SELECT v.*,p.name patient_name,p.reg_no,p.age,p.sex FROM visits v JOIN patients p ON p.id=v.patient_id WHERE v.status='waiting' ORDER BY v.id")]
    if role == 'receptionist':
        state['issued'] = [dict(r) for r in c.execute('SELECT v.id,v.patient_id,v.token_no,v.token_date,v.created,v.creator,v.status,v.override_reason,v.override_by,v.ordered_by,p.name patient_name,p.reg_no,p.age,p.sex FROM visits v JOIN patients p ON p.id=v.patient_id WHERE token_date=? ORDER BY token_no', (td,))]
    if role == 'operator':
        state['active'] = [dict(r) for r in c.execute("SELECT v.*,p.name patient_name,p.reg_no FROM visits v JOIN patients p ON p.id=v.patient_id WHERE status='in_progress' AND assigned_operator_id=? ORDER BY v.id", (u['id'],))]
        state['drafts'] = reports.listing(c, u, 'draft')
        state['history'] = reports.listing(c, u, 'final')
    if role in ('admin', 'operator'):
        state['doctors'] = [dict(r) for r in c.execute('SELECT * FROM doctors ORDER BY name')]
    if role == 'admin':
        state['users'] = [dict(r) for r in c.execute('SELECT id,name,username,role,doctor_id,active FROM users ORDER BY name')]
    return state
