import hmac
from .. import security
from ..services.users import add_user


class AuthenticationError(Exception):
    pass


def dispatch(c, method, path, data, headers):
    if path == '/api/session' and method == 'GET':
        user, _ = security.session(headers, c)
        return {'user': user, 'setup': c.execute('SELECT count(*) FROM users').fetchone()[0] == 0}, None
    if path == '/api/setup' and method == 'POST':
        if c.execute('SELECT count(*) FROM users').fetchone()[0]:
            raise ValueError('Setup already completed')
        add_user(c, {**data, 'role': 'admin'})
        return {'ok': True}, None
    if path == '/api/login' and method == 'POST':
        row = c.execute('SELECT * FROM users WHERE username=? AND active=1', (data.get('username', ''),)).fetchone()
        if not row or not hmac.compare_digest(security.password(data.get('password', ''), row['salt']), row['password']):
            raise AuthenticationError('Incorrect username or password')
        return {'ok': True}, security.cookie(security.create_session(row))
    raise LookupError('Not found')
