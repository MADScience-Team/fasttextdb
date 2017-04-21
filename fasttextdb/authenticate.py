from flask import request, session

from passlib.hash import sha256_crypt

from .util import *
from .models import *

__all__ = ['load_user']


def _get_username():
    if 'username' in session:
        return session['username'], True

    config = request.config
    c = config['authentication']
    headers = c['headers']
    form = c['form']
    json = c['json']

    for h in headers['username']:
        if h in request.headers:
            return request.headers[h], False

    if request.form is not None:
        for x in form['username']:
            if x in request.form:
                return request.form[x], False

    if request.json is not None:
        for x in json['username']:
            if x in request.json:
                return request.json[x], False

    return None, False


def _get_password():
    config = request.config
    c = config['authentication']
    headers = c['headers']
    form = c['form']
    json = c['json']

    for h in headers['password']:
        if h in request.headers:
            return request.headers[h]

    if request.form is not None:
        for x in form['password']:
            if x in request.form:
                return request.form[x]

    if request.json is not None:
        for x in json['password']:
            if x in request.json:
                return request.json[x], False

    return None


def _get_user():
    username, authenticated = _get_username()

    if username is None:
        return None, authenticated

    user = request.service.get_user(username)

    if user is None:
        config = request.config

        if username in config['users']:
            return config['users'][username], authenticated
        else:
            return None, authenticated
    else:
        return user, authenticated


def load_user():
    user, authenticated = _get_user()

    if not authenticated:
        password = _get_password()

        if password is not None:
            authenticated = sha256_crypt.verify(password,
                                                user['password_hash'])

    return user, authenticated
