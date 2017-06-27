from flask import jsonify
from flask import request
from flask import session

from functools import wraps

from ..models import *
from .app import app, user_loader
from ..exceptions import *
from .pages import upload_vectors_for_model


def api_auth(func):
    """Decorator, checks user credentials or session info when the
    user attempts to use a protected endpoint"""

    @wraps(func)
    def check_auth(*args, **kwargs):
        if not request.authenticated or request.user is None:
            raise UnauthorizedException(
                'authentication required for API access')

        return func(*args, **kwargs)

    return check_auth


class Line(object):
    def __init__(self):
        self._line = None

    def write(self, line):
        self._line = line

    def read(self):
        return self._line


def _iter_csv(data):
    line = Line()
    writer = csv.writer(line)
    for csv_line in data:
        writer.writerow(csv_line)
        yield line.read()


@app.route("/api/model/<name>/words", methods=['POST', 'GET'])
@api_auth
def api_get_words(name):
    if request.service.model_exists(name):
        if request.method == 'POST':
            words = request.json
        else:
            words = request.words

        if words and len(words):
            words = request.service.get_words(name, words, exact=request.exact)
        else:
            words = request.service.get_words(name)

        return jsonify(words)
    else:
        raise NotFoundException('Could not find a model with name %s' % name)


@app.route("/api/model/<name>/vectors", methods=['POST'])
@api_auth
def api_create_vectors(name):
    if request.service.model_exists(name):
        return jsonify(request.service.create_vectors(name, request.json))
    else:
        raise NotFoundException('Could not find a model with ID %s' % id)


@app.route("/api/model/<name>/vectors", methods=['PUT'])
@api_auth
def api_update_vectors(name):
    if request.service.model_exists(name):
        return jsonify(request.service.update_vectors(name, request.json))
    else:
        raise NotFoundException('Could not find a model with ID %s' % id)


@app.route("/api/model/<name>/exists", methods=['GET'])
@api_auth
def api_model_exists(name):
    exists = request.service.model_exists(name)
    return jsonify({'exists': exists})


@app.route("/api/model/<name>", methods=['GET'])
@api_auth
def api_get_model(name):
    if request.service.model_exists(name):
        model = request.service.get_model(name)
        return jsonify(model)
    else:
        raise NotFoundException('Could not find a model with name %s' % name)


@app.route("/api/model/create", methods=['POST'])
@app.route("/api/model", methods=['POST'])
@api_auth
def api_create_model():
    return jsonify(request.service.create_model(**request.json)), 201


@app.route("/api/search/model", methods=['PUT', 'POST'])
@api_auth
def api_find_models():
    return jsonify(request.service.find_models(**request.json))


@app.route("/api/model/<name>", methods=['PUT'])
@api_auth
def api_update_model(name):
    if request.service.model_exists(name):
        model = request.service.update_model(name, **request.json)
        return jsonify(model)
    else:
        raise NotFoundException('Could not find a model with ID %s' % id)


@app.route("/api/model/<name>/vectors/count", methods=['GET', 'POST'])
@api_auth
def api_count_vectors_for_model(name):
    if request.service.model_exists(name):
        if request.method == 'POST':
            words = request.json
        else:
            words = request.words

        if words and len(words):
            count = request.service.count_vectors_for_words(name, words)
        else:
            count = request.service.count_vectors_for_model(name)

        return jsonify({'count': count})
    else:
        raise NotFoundException('Could not find a model with name %s' % name)


@app.route("/api/model/<name>/vectors/words", methods=['GET', 'POST'])
@api_auth
def api_get_vectors_for_model(name):
    if request.service.model_exists(name):
        if request.method == 'POST':
            words = request.json
        else:
            words = request.words

        if words and len(words):
            vectors = request.service.get_vectors_for_words(
                name,
                words,
                sort=request.sort,
                page=request.page,
                page_size=request.page_size,
                exact=request.exact)
        else:
            vectors = request.service.get_vectors_for_model(
                name,
                sort=request.sort,
                page=request.page,
                page_size=request.page_size)

        return jsonify(vectors)
    else:
        raise NotFoundException('Could not find a model with name %s' % name)


@app.route('/api/model/<int:id>/upload/vectors', methods=['POST'])
@api_auth
def api_upload_vectors_file_for_model_id(id):
    model = request.session.query(Model).get(id)

    if not model:
        raise NotFoundException('Model with ID %s was not found' % id)

    cnt = upload_vectors_for_model(model)
    return jsonify({'count': cnt})


@app.route('/api/model/name/<name>/upload/vectors', methods=['POST'])
@api_auth
def api_upload_vectors_file_for_model_name(name):
    models = list(request.session.query(Model).filter(Model.name == name))

    if len(models) == 0:
        raise NotFoundException('Model with name %s was not found' % name)

    cnt = upload_vectors_for_model(models[0])
    return jsonify({'count': cnt})
