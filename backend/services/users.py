import secrets
from ..security import password
def add_user(c, d):
    n = d.get('name', '').strip()
    un = d.get('username', '').strip()
    pw = d.get('password', '')
    role = d.get('role')
    if not n or not un or len(pw) < 8:
        raise ValueError('Name, username and password of at least 8 characters required')
    if role not in ['admin', 'receptionist', 'operator', 'doctor']:
        raise ValueError('Invalid role')
    doc = d.get('doctor_id') or None
    if role == 'doctor' and (not doc or not c.execute('SELECT id FROM doctors WHERE id=?',(doc,)).fetchone()):
        raise ValueError('Select linked doctor')
    salt = secrets.token_hex(16)
    c.execute('INSERT INTO users(name,username,password,salt,role,doctor_id) VALUES(?,?,?,?,?,?)', (n, un, password(pw, salt), salt, role, doc))
