from ..services import patients, tokens


def dispatch(c, u, path, d):
    handlers = {'/api/patients': patients.create, '/api/patient-edit': patients.edit}
    if path in handlers:
        result = handlers[path](c, u, d)
        if path == '/api/patients' and d.get('issue_token') is True:
            result['visit'] = tokens.create(c, u, {'patient_id': result['id']})
        return result
    if path == '/api/patient':
        return patients.get(c, d['id'])
    return patients.history(c, u, d['id'])
