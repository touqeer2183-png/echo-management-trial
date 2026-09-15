import datetime
from ..permissions import need
from .common import result
def daterange(period, start=None, end=None):
    d = datetime.date.today()
    if period == 'today':
        s = e = d
    elif period == 'week':
        s = d - datetime.timedelta(days=d.weekday())
        e = d
    elif period == 'month':
        s = d.replace(day=1)
        e = d
    elif period == 'year':
        s = d.replace(month=1, day=1)
        e = d
    else:
        s = datetime.date.fromisoformat(start)
        e = datetime.date.fromisoformat(end)
    if e < s:
        raise ValueError('End date must not precede start date')
    return (s.isoformat(), (e + datetime.timedelta(days=1)).isoformat())
def analytics(c, u, d):
    need(u, 'admin', 'operator', 'doctor')
    s, e = daterange(d.get('period', 'today'), d.get('start'), d.get('end'))
    params = (s, e)
    operators = [dict(r) for r in c.execute("SELECT operator name,count(*) total FROM visits WHERE status='final' AND finalized>=? AND finalized<? GROUP BY operator ORDER BY total DESC", params)]
    doctors = [dict(r) for r in c.execute("SELECT d.id,d.name,count(v.id) total FROM doctors d LEFT JOIN visits v ON v.doctor_id=d.id AND v.status='final' AND v.finalized>=? AND v.finalized<? GROUP BY d.id ORDER BY total DESC", params)]
    if u['role'] == 'operator':
        operators = [dict(r) for r in c.execute("SELECT operator name,count(*) total FROM visits WHERE status='final' AND finalized>=? AND finalized<? AND operator_id=? GROUP BY operator",(s,e,u['id']))]
    if u['role'] == 'doctor':
        doctors = [x for x in doctors if x['id'] == u['doctor_id']]
    if u['role'] == 'operator':
        doctors = []
    totals = {'issued': c.execute('SELECT count(*) FROM visits WHERE created>=? AND created<?', params).fetchone()[0], 'completed': c.execute("SELECT count(*) FROM visits WHERE status='final' AND finalized>=? AND finalized<?", params).fetchone()[0]}
    if u['role'] != 'admin':
        totals = {'completed': sum(x['total'] for x in (operators if u['role']=='operator' else doctors))}
    return result({'operators': operators, 'doctors': doctors, 'totals': totals, 'start': s, 'end': e})
