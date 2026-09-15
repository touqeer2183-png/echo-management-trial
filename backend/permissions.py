"""The single backend feature/role permission map."""
PERMISSIONS = {
    'accounts': {'admin'}, 'doctors': {'admin'}, 'settings': {'admin'},
    'patients': {'receptionist'}, 'search': {'receptionist', 'operator'},
    'token': {'receptionist', 'operator'}, 'permission': {'operator'},
    'claim': {'operator'}, 'report': {'operator'},
    'analytics': {'admin', 'operator', 'doctor'},
}

def require(user, feature):
    need(user, *PERMISSIONS[feature])

def need(user, *roles):
    if user['role'] not in roles:
        raise PermissionError('Access not allowed for this account')
