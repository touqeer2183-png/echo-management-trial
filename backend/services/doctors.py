from ..validators import stamp

def create(c, d):
    name = str(d.get('name') or '').strip()
    if not name:
        raise ValueError('Doctor name required')
    cur = c.execute('INSERT INTO doctors(name,qualification,registration,stamp_image) VALUES(?,?,?,?)',
                    (name, d.get('qualification', ''), d.get('registration', ''), stamp(d.get('stamp_image', ''))))
    return {'id': cur.lastrowid}
