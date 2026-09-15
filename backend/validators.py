"""Input normalization shared by creation and editing."""
import base64
import datetime
import re
from .config import STAMP_LIMIT, IMAGE_MIMES

def patient(data):
    d = dict(data)
    for key in ('name', 'identity', 'phone', 'relation_type', 'relation_name', 'guardian_name', 'address', 'age', 'sex'):
        d[key] = str(d.get(key) or '').strip()
    d['is_minor'] = d.get('is_minor') in (True, 1, '1')
    if not d['name']:
        raise ValueError('Patient name required')
    ident = re.sub(r'\D', '', d['identity'])
    phone = re.sub(r'\D', '', d['phone'])
    if not re.fullmatch(r'\d{13}', ident):
        raise ValueError('CNIC format 00000-0000000-0 required')
    if not re.fullmatch(r'03\d{9}', phone):
        raise ValueError('Phone format 0300-0000000 required')
    d['identity'] = f'{ident[:5]}-{ident[5:12]}-{ident[12:]}'
    d['phone'] = f'{phone[:4]}-{phone[4:]}'
    if d['relation_type'] not in ('S/O', 'W/O', 'D/O') or not d['relation_name']:
        raise ValueError('Select S/O, W/O or D/O and enter related person name')
    if d['is_minor'] and not d['guardian_name']:
        raise ValueError('Guardian name required for child')
    if not d['age'] or d['sex'] not in ('Male', 'Female', 'Other'):
        raise ValueError('Age and sex are required')
    return d

def months(value):
    n = int(value)
    if not 1 <= n <= 120:
        raise ValueError('Interval must be 1-120 months')
    return n

def allowed_date(value):
    date = datetime.date.fromisoformat(value)
    if date < datetime.date.today():
        raise ValueError('Allowed date cannot be in the past')
    return date.isoformat()

def stamp(value):
    if not value:
        return ''
    if not isinstance(value, str) or ',' not in value:
        raise ValueError('Invalid stamp image')
    header, encoded = value.split(',', 1)
    if header not in tuple('data:' + mime + ';base64' for mime in IMAGE_MIMES):
        raise ValueError('Stamp must be PNG or JPEG')
    try:
        image = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError):
        raise ValueError('Invalid stamp encoding')
    valid = image.startswith(b'\x89PNG\r\n\x1a\n') if 'png' in header else image.startswith(b'\xff\xd8\xff')
    if not valid or not 0 < len(image) <= STAMP_LIMIT:
        raise ValueError('Stamp must be a PNG/JPEG image under 250 KB')
    return value
