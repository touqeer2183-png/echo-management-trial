from ..services.analytics import analytics


def dispatch(c, u, path, d):
    return analytics(c, u, d)
