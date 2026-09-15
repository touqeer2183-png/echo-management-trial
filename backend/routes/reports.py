from ..services import reports


def dispatch(c, u, path, d):
    if path in ('/api/reports/drafts', '/api/reports/completed'):
        return reports.listing(c, u, 'draft' if path.endswith('drafts') else 'final')
    if path == '/api/report/amend':
        return reports.save(c, u, d, final=True, amendment=True)
    action = d.get('action')
    if action is not None and action not in ('draft', 'finalize'):
        raise ValueError('Invalid report action')
    final = path.endswith('/finalize') or (path == '/api/report' and (action == 'finalize' or (action is None and d.get('final') is True)))
    return reports.save(c, u, d, final=final)
