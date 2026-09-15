from ..services import users, doctors
from ..services.common import audit
from ..validators import months


def dispatch(c, u, path, d):
    result = {'ok': True}
    if path == '/api/users':
        users.add_user(c, d)
    elif path == '/api/doctors':
        result = doctors.create(c, d)
    else:
        c.execute('UPDATE settings SET months=? WHERE id=1', (months(d['months']),))
    audit(c, u['name'], path)
    return result
