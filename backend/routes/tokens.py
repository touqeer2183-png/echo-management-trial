from ..services import tokens, repeat_policy


def dispatch(c, u, path, d):
    handlers = {'/api/token': tokens.create, '/api/permission': repeat_policy.grant,
                '/api/claim': tokens.claim, '/api/release': tokens.release}
    return handlers[path](c, u, d)
