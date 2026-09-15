from ..services.state import load


def dispatch(c, u, query):
    offset = max(0, int(query.get('offset', ['0'])[0]))
    return load(c, u, query.get('q', [''])[0], offset)
