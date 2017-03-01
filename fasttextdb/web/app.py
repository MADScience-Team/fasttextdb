import logging
import os
import re
import csv
import magic
import bz2
import gzip
import json
import flask_login

from flask import Flask
from flask import request
from flask import render_template
from flask import send_from_directory
from flask import jsonify
from flask import make_response
from flask import Response
from flask import redirect
from flask import url_for
from flask import flash
from flask import get_flashed_messages

from sqlalchemy import create_engine, Column, Integer, String, Float

from sqlalchemy.orm import sessionmaker

from sqlalchemy.sql.expression import asc, desc

from ..vectors import *
from ..config import *
from ..models import *
from ..util import *
from ..exceptions import *
from ..authenticate import *

__all__ = ['app', 'run_app']

config = load_config()
engine = get_engine(config)
Session = sessionmaker(bind=engine)

app = Flask(__name__)
app.secret_key = config['secret']

login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

static_dir = os.path.join(app.root_path, 'static')
node_dir = os.path.join(static_dir, 'node_modules')

if config['debug']:
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
else:
    app.config['TEMPLATES_AUTO_RELOAD'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False


def run_app():
    app.run(host=config['host'], port=config['port'], debug=config['debug'])


def page_request(query):
    return query.offset(
        request.paging['page'] *
        request.paging['page_size']).limit(request.paging['page_size'])


def get_param(param, default=None, type_=None):
    camel = under_to_camel(param)
    search = [param, camel, camel.lower(), camel.upper(), param.upper]
    for s in search:
        if s in request.args:
            return request.args.get(s, default, type_)

    return request.args.get(param, default, type_)


def get_param_list(param, type_=None):
    camel = under_to_camel(param)
    search = [param, camel, camel.lower(), camel.upper(), param.upper]

    for s in search:
        if s in request.args:
            return request.args.getlist(param, type_)

    return request.args.getlist(param, type_)


@login_manager.user_loader
def user_loader(name):
    credentials = config['authentication']['credentials']
    name, password = get_credentials(config, request, name, None, True)
    loader = config['authentication']['loader']
    user = loader(config, request, name, password, True)
    verify = config['authentication']['verify']
    user._authenticated = verify(config, request, user, name, password, True)
    request.user = user
    return user


@login_manager.request_loader
def request_loader(request):
    credentials = config['authentication']['credentials']
    name, password = credentials(config, request, None, None, False)
    loader = config['authentication']['loader']
    user = loader(config, request, name, password, False)

    if user is None:
        return user

    verify = config['authentication']['verify']
    user._authenticated = verify(config, request, user, name, password, False)

    if not user.is_authenticated():
        return None

    request.user = user
    return user


@app.before_first_request
def prepare_db():
    Base.metadata.create_all(engine)


@app.before_request
def prepare_request():
    request.session = Session()

    request.paging = {
        'page': get_param('page', 0, int),
        'page_size': get_param('page_size', 25, int)
    }

    request.camel = get_param('camel', False, bool)
    request.packed = get_param('camel', False, bool)
    request.include_model = get_param('include_model', False, bool)
    request.include_model_id = get_param('include_model_id', False, bool)
    request.words = get_param_list('word')


@app.after_request
def cleanup(response):
    if request.session.is_active:
        request.session.commit()
        request.session.close()
    return response


@app.errorhandler(Exception)
def handle_errors(exception):
    request.session.rollback()
    logging.error(exception, exc_info=True)
    return 'Something went wrong', 500


@app.errorhandler(WebException)
def handler_web_exception(e):
    if get_requested_type() == 'json':
        return make_response(
            jsonify(message=e.message, status=e.status), e.status)
    else:
        return render_template('error.html', error=e)


@app.route('/bootstrap/<path:file>')
def bootstrap(file):
    return send_from_directory(
        os.path.join(node_dir, 'bootstrap', 'dist'), file)
