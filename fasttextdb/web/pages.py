import magic

from io import BytesIO
from bz2 import BZ2File
from gzip import GzipFile

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

from flask_login import login_required, logout_user

from sqlalchemy import Integer, Float

from .app import app, page_request, engine
from ..models import *
from ..exceptions import *
from ..util import *
from ..vectors import *


def templ(template, **kwargs):
    kwargs['page'] = request.paging['page']
    kwargs['page_size'] = request.paging['page_size']
    return render_template(template, **kwargs)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        credentials = config['authentication']['credentials']
        name, password = credentials(config, request, None, None, False)
        loader = config['authentication']['loader']
        user = loader(config, request, name, password, False)
        request.user = user

        if not user:
            return render_template(
                'login.html', message="Bad username or password"), 401

        verify = config['authentication']['verify']
        user.set_authenticated(
            verify(config, request, user, name, password, False))

        if not user.is_authenticated():
            return render_template(
                'login.html', message="Bad username or password"), 401

        if flask_login.login_user(user):
            return redirect(request.args['next'] or url_for('protected'))

    return render_template(
        'login.html', message="An error occurred while logging in"), 401


def _get_request_model_data():
    model_data = {camel_to_under(k): request.form[k] for k in request.form}

    for k in model_data:
        col = getattr(Model, k)

        if type(col.property.columns[0].type) is Float:
            model_data[k] = float(model_data[k])
        elif type(col.property.columns[0].type) is Integer:
            model_data[k] = int(model_data[k])

    model_data['description'] = model_data['description'].strip()
    return model_data


@app.route("/model/create", methods=['POST'])
@login_required
def submit_model_create_form():
    model_data = _get_request_model_data()
    model = Model(**model_data)
    request.session.add(model)
    request.session.commit()
    return templ('model.html', model=model), 201


@app.route("/model/<int:id>", methods=['GET'])
@login_required
def get_model(id):
    model = request.session.query(Model).get(id)

    if model:
        return templ('model.html', model=model)
    else:
        raise NotFoundException('Could not find a model with ID %s' % id)


@app.route("/model/<int:id>/update", methods=['GET'])
@login_required
def get_model_update_form(id):
    model = request.session.query(Model).get(id)

    if not model:
        raise NotFoundException('Could not find a model with ID %s' % id)

    return templ(
        'modelForm.html',
        model=model,
        submit_action='/model/%s' % id,
        submit_method='put')


@app.route("/model/<int:id>", methods=['PUT'])
@login_required
def update_model(id):
    model = request.session.query(Model).get(id)

    if not model:
        raise NotFoundException('Could not find a model with ID %s' % id)

    model_data = _get_request_model_data()

    for k in model_data:
        if k != 'id':
            setattr(model, k, model_data[k])

    request.session.commit()
    return templ('model.html', model=model)


@app.route("/model/create", methods=['GET'])
@login_required
def get_model_create_form():
    return templ(
        'modelForm.html',
        model=Model(),
        submit_action='/model/create',
        submit_method='post')


@app.route("/models")
@app.route("/model", methods=['GET'])
@login_required
def get_models():
    models = request.session.query(Model)
    models = page_request(models)
    total = Model.count_models(request.session)
    start = request.paging['page'] * request.paging['page_size']
    end = start + request.paging['page_size']
    end = min(end, total)
    return templ(
        'models.html', models=models, start=start, end=end, total=total)


def _vectors_for_words(id, words):
    model = request.session.query(Model).get(id)

    if not model:
        raise NotFoundException('Model with ID %s was not found' % id)

    vectors = Vector.vectors_for_words(request.session, words,
                                       model).order_by(asc(Vector.word))
    vectors = page_request(vectors)

    return vectors_response(
        template='vectors.html',
        method='vectors_for_words',
        model=model,
        vectors=vectors,
        words=words)


@app.route('/model/<int:id>/vectors/words', methods=['GET'])
@login_required
def vectors_for_words(id):
    return _vectors_for_words(id, request.words)


def _vectors_response(vectors, template, method, **kwargs):
    start = request.paging['page'] * request.paging['page_size']
    end = start + request.paging['page_size']
    return templ(
        template,
        vectors=vectors,
        method=method,
        start=start,
        end=end,
        **kwargs)


@app.route('/model/<int:id>/vectors')
@login_required
def vectors_for_model(id):
    model = request.session.query(Model).get(id)

    if not model:
        raise NotFoundException('Model with ID %s was not found' % id)

    vectors = Vector.vectors_for_model(request.session,
                                       model).order_by(asc(Vector.word))
    vectors = page_request(vectors)

    return vectors_response(
        template='vectors.html',
        method='vectors_for_model',
        model=model,
        vectors=vectors)


@app.route('/model/<int:id>/vectors/word/<word>')
@login_required
def vectors_for_word(id, word):
    model = request.session.query(Model).get(id)

    if not model:
        raise NotFoundException('Model with ID %s was not found' % id)

    vectors = Vector.vectors_for_word(request.session, word,
                                      model).order_by(asc(Vector.word))
    vectors = page_request(vectors)
    total = Vector.count_vectors_for_word(request.session, word, model)
    start = request.paging['page'] * request.paging['page_size']
    end = start + request.paging['page_size']
    end = min(end, total)

    return templ(
        'vectors.html',
        method='vectors_for_word',
        model=model,
        vectors=vectors,
        start=start,
        word=word,
        end=end)


@app.route('/model/<int:id>/upload/vectors', methods=['GET'])
@login_required
def upload_vectors_file_form(id):
    model = request.session.query(Model).get(id)

    if not model:
        raise NotFoundException('Model with ID %s was not found' % id)

    return templ('upload.html', model=model)


def upload_vectors_for_model(model):
    file = request.files['file']

    if file.filename == '':
        raise BadRequestException('no filename specified')

    mime_type = magic.from_buffer(file.stream.read(1024), mime=True)

    print('#upload_vectors_for_model %s' % mime_type)
    file.stream.seek(0)

    if mime_type == 'application/x-gzip' or mime_type == 'application/gzip':
        f = GzipFile(fileobj=file.stream)
    elif mime_type == 'application/x-bzip2':
        f = BZ2File(filename=file.stream)
    else:
        f = file.stream

    cnt = 0

    for vector in commit_file(
            f,
            engine=engine,
            name="foo",
            description="test model",
            model=model,
            session=request.session):
        cnt += 1

    return cnt


@app.route('/model/<int:id>/upload/vectors', methods=['POST'])
@login_required
def upload_vectors_file_for_model_id(id):
    model = request.session.query(Model).get(id)

    if not model:
        raise NotFoundException('Model with ID %s was not found' % id)

    cnt = upload_vectors_for_model(model)
    return Response('%s' % cnt, mimetype='text/plain')


@app.route('/model/name/<name>/upload/vectors', methods=['POST'])
@login_required
def upload_vectors_file_for_model_name(name):
    models = list(request.session.query(Model).filter(Model.name == name))

    if len(models) == 0:
        raise NotFoundException('Model with name %s was not found' % name)

    cnt = upload_vectors_for_model(model)
    return Response('%s' % cnt, mimetype='text/plain')


@app.route('/logout')
def logout():
    logout_user()
    return render_template('logoutSuccess.html')
