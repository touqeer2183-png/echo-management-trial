import datetime
def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()
def today():
    return datetime.date.today().isoformat()
def audit(c, u, a):
    c.execute('INSERT INTO audit(time,user,action) VALUES(?,?,?)', (now(), u, a))

def result(value):
    return value
