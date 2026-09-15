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
            match = c.execute(f"SELECT id FROM patients WHERE COALESCE(is_minor,0)=0 AND replace({key},'-','')=? AND id<>?", (d[key].replace('-',''),pid)).fetchone()
            if match:
                person = get(c, match['id'])
                last = person['last_echo'][:10] if person['last_echo'] else 'No completed echo'
                raise ValueError(f"This {key} belongs to {person['name']} (Reg {person['reg_no']}). Last echo: {last}")

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
