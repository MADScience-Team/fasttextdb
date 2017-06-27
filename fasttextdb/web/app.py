import logging
import os
import re
import csv
import magic
import bz2
import gzip
import json

from flask import (Flask, request, render_template, send_from_directory,
                   jsonify, make_response, Response, redirect, url_for, flash,
                   get_flashed_messages, session)

from sqlalchemy import create_engine, Column, Integer, String, Float

from sqlalchemy.orm import sessionmaker

from sqlalchemy.sql.expression import asc, desc

from ..vectors import *
from ..config import *
from ..models import *
from ..util import *
from ..exceptions import *
from ..authenticate import *
from ..urlhandler import *

__all__ = ['app', 'run_app']

config = load_config()
engine = None
Session = None
ftdb = None

app = Flask(__name__)
app.secret_key = config['secret']

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


def user_loader():
    return config['authentication']['loader']()


@app.before_first_request
def prepare_db():
    global engine, Session, ftdb
    engine = create_engine(config['url'])
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    ftdb = fasttextdb(config['url'])


@app.before_request
def prepare_request():
    request.config = config
    request.service = ftdb
    request.service.open()
    request.user, request.authenticated = config['authentication']['loader']()

    if request.user and request.authenticated:
        session['username'] = request.user['username']

    request.page = get_param('page', 0, int)
    request.page_size = get_param('page_size', 25, int)
    request.camel = get_param('camel', False, bool)
    request.packed = get_param('camel', False, bool)
    request.include_model = get_param('include_model', False, bool)
    request.include_model_id = get_param('include_model_id', False, bool)
    request.words = get_param_list('word')
    request.sort = get_param_list('sort')
    request.model = list(ints_or_strs(*get_param_list('model')))
    request.exact = get_param('exact', False, bool)


@app.after_request
def cleanup(response):
    request.service.close()
    return response


@app.errorhandler(Exception)
def handle_errors(exception):
    request.service.close(exception)
    logging.error(exception, exc_info=True)
    return 'Something went wrong', 500


@app.errorhandler(WebException)
def handler_web_exception(e):
    if get_requested_type() == 'json':
        return make_response(
            jsonify(message=e.message, status=e.status), e.status)
    else:
        return render_template('error.html', error=e), e.status


@app.route('/bootstrap/<path:file>')
def bootstrap(file):
    return send_from_directory(
        os.path.join(node_dir, 'bootstrap', 'dist'), file)
