import re

from flask import request

__all__ = [
    'camel_to_under', 'under_to_camel', 'get_requested_type',
    'get_content_type'
]

_first_cap_re = re.compile('(.)([A-Z][a-z]+)')
_all_cap_re = re.compile('([a-z0-9])([A-Z])')


def camel_to_under(name):
    s1 = _first_cap_re.sub(r'\1_\2', name)
    return _all_cap_re.sub(r'\1_\2', s1).lower()


def under_to_camel(under):
    spl = under.split('_')
    spl[0] = spl[0].lower()
    return ''.join(x.capitalize() or '_' for x in spl)


def int_or_str(s):
    if s.isdigit():
        return int(s)
    else:
        return s


def ints_or_strs(*values):
    return [int_or_str(v) for v in values]


def get_requested_type():
    best = request.accept_mimetypes.best_match(
        ['application/json', 'text/html', 'text/csv'])

    if request.accept_mimetypes[best] > request.accept_mimetypes['text/html']:
        return best.split('/')[1]
    else:
        return 'html'


def get_content_type():
    if 'Content-Type' in request.headers:
        ct = request.headers['Content-Type']

        if ct == 'application/json':
            return 'json'
        elif ct == 'application/x-www-form-urlencoded':
            return 'form'
        else:
            return 'unknown'
    else:
        return None
