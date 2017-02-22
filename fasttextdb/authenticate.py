from passlib.hash import sha256_crypt

from .util import *
from .models import *

__all__ = ['load_user', 'sha256_verify', 'get_credentials']


def load_user(config, request, name, password, from_session):
    print('#load_user %s %s %s %s' % (request, name, password, from_session))
    if not name:
        return None

    if name in config['users']:
        user = config['users'][name]
    else:
        users = list(request.session.query(User).filter(User.name == name))

        if len(users) == 0:
            user = None
        else:
            user = users[0]

    return user


def sha256_verify(config, request, user, name, password, from_session):
    print('#sha256_verify %s %s %s %s' %
          (request, name, password, from_session))
    return from_session or sha256_crypt.verify(password, user.password_hash)


def get_credentials(config, request, name, password, from_session):
    print('#get_credentials %s %s %s %s' %
          (request, name, password, from_session))
    c = config['authentication']
    headers = c['headers']
    form = c['form']
    keys = c['json']

    if name is None:
        if any(h in request.headers for h in headers['name']):
            for h in headers['name']:
                if h in request.headers:
                    name = request.headers[h]
                    break
        elif get_content_type() == 'json':
            for k in keys['name']:
                if k in request.json:
                    name = request.json[k]
                    break
        elif get_content_type() == 'form':
            for k in form['name']:
                if k in request.form:
                    name = request.form[k]

    if not from_session and password is None:
        if any(h in request.headers for h in headers['password']):
            for h in headers['password']:
                if h in request.headers:
                    password = request.headers[h]
                    break
        elif get_content_type() == 'json':
            for k in keys['password']:
                if k in request.json:
                    password = request.json[k]
                    break
        elif get_content_type() == 'form':
            for k in form['password']:
                if k in request.form:
                    password = request.form[k]

    return name, password
