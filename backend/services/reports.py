import json

from .common import now, audit
from .patients import get
from ..validators import stamp


def save(c, u, d, final=False, amendment=False):
    v = c.execute('SELECT * FROM visits WHERE id=?', (int(d['id']),)).fetchone()
    if not v:
        raise ValueError('Encounter not found')

    if amendment:
        if v['status'] != 'final' or v['operator_id'] != u['id']:
            raise PermissionError('Only the original operator may correct this completed report')
        reason = str(d.get('reason') or '').strip()
        if not 5 <= len(reason) <= 500:
            raise ValueError('Enter a correction reason of 5 to 500 characters')
        if d.get('expected_revision') != v['report_revision']:
            raise ValueError('Report was updated elsewhere. Reopen it before editing.')
    elif v['status'] == 'final':
        raise ValueError('Final report is locked; use Edit Report with a correction reason')

    if not amendment and (v['status'] not in ('in_progress', 'draft') or v['assigned_operator_id'] != u['id']):
        raise PermissionError('Claim this echo before reporting; only its assigned operator may edit it')

    r = d.get('report')
    if not isinstance(r, dict):
        raise ValueError('Report must be an object')
    for key in ('findings', 'conclusion', 'color'):
        if not isinstance(r.get(key, ''), str):
            raise ValueError(key + ' must be text')
    if not isinstance(r.get('values', {}), dict) or any(not isinstance(v, str) for v in r.get('values', {}).values()):
        raise ValueError('Measurements must contain text values')
    for key in ('columns', 'lines'):
        if not isinstance(r.get(key, []), list) or any(not isinstance(v, str) for v in r.get(key, [])):
            raise ValueError(key + ' must contain text')
    if not isinstance(r.get('rows', []), list) or any(
        not isinstance(row, list) or any(not isinstance(v, str) for v in row)
        for row in r.get('rows', [])
    ):
        raise ValueError('Custom rows must contain text cells')

    tables = r.get('measurement_tables')
    if tables is not None:
        # Group names are labels supplied by the active frontend. Accept them
        # without changing the report data; validate every table below.
        if not isinstance(tables, dict) or not tables or any(
            not isinstance(group, str) or not group.strip() for group in tables
        ):
            raise ValueError('Invalid measurement groups')
        for table in tables.values():
            if not isinstance(table, dict):
                raise ValueError('Invalid measurement table')
            columns, rows = table.get('columns'), table.get('rows')
            if not isinstance(columns, list) or not 3 <= len(columns) <= 12 or any(
                not isinstance(x, str) or len(x) > 120 for x in columns
            ):
                raise ValueError('Measurements require 3 to 12 text columns')
            if not isinstance(rows, list) or len(rows) > 100:
                raise ValueError('Use at most 100 parameters per group')
            for row in rows:
                if not isinstance(row, list) or len(row) != len(columns) or any(
                    not isinstance(x, str) or len(x) > 2000 for x in row
                ):
                    raise ValueError('Invalid measurement row')
                if any(row[i].strip() for i in range(1, len(row)) if i != 2) and not row[0].strip():
                    raise ValueError('Enter a parameter name for each measurement')

    doc = int(r.get('doctor_id') or 0)
    dr = c.execute('SELECT * FROM doctors WHERE id=?', (doc,)).fetchone()
    if not dr:
        raise ValueError('Select reporting doctor')
    if final and not r.get('conclusion', '').strip():
        raise ValueError('Conclusion required')
    r = dict(r)
    r['doctor'] = dict(dr)
    r['doctor']['stamp_image'] = stamp(r['doctor'].get('stamp_image', ''))

    # Server-owned snapshots prevent client tampering and later patient edits changing this report.
    old = json.loads(v['report']) if v['report'] else {}
    r['patient'] = old.get('patient') or get(c, v['patient_id'])
    previous = c.execute(
        "SELECT MAX(finalized) FROM visits WHERE patient_id=? AND status='final' AND id<>?",
        (v['patient_id'], v['id'])
    ).fetchone()[0]
    r['previous_echo'] = old.get('previous_echo', previous)
    c.execute(
        'UPDATE visits SET report=?,operator=?,operator_id=?,doctor_id=?,assigned_operator=?,assigned_operator_id=?,status=?,finalized=? WHERE id=?',
        (json.dumps(r), u['name'], u['id'], doc, u['name'], u['id'], 'final' if final else 'draft', (v['finalized'] if amendment else now()) if final else None, v['id'])
    )
    if amendment:
        revision = v['report_revision'] + 1
        c.execute(
            'INSERT INTO report_revisions(visit_id,revision,previous_report,replacement_report,reason,operator_id,created) VALUES(?,?,?,?,?,?,?)',
            (v['id'], revision, v['report'], json.dumps(r), reason, u['id'], now())
        )
        c.execute('UPDATE visits SET report_revision=? WHERE id=?', (revision, v['id']))
        audit(c, u['name'], f"Corrected report {v['id']}; revision {revision}; reason: {reason}")
        return {'ok': True, 'revision': revision}
    audit(c, u['name'], ('Finalized' if final else 'Saved draft') + ' report ' + str(v['id']))
    return {'ok': True}


def listing(c, u, status):
    query = 'SELECT v.*,p.name patient_name,p.reg_no FROM visits v JOIN patients p ON p.id=v.patient_id WHERE v.status=?'
    params = [status]
    if status == 'draft':
        query += ' AND assigned_operator_id=?'
        params.append(u['id'])
    return [dict(r) for r in c.execute(query + ' ORDER BY v.id DESC LIMIT 100', params)]
