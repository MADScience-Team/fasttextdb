from flask import jsonify
from flask import request
from flask import session

from flask_login import login_user

from functools import wraps

from ..models import *
from .app import app, user_loader, request_loader, page_request
from ..exceptions import *
from .pages import upload_vectors_for_model


def api_auth(func):
    @wraps(func)
    def check_auth(*args, **kwargs):
        user = user_loader(session.get('user_id'))

        if user is None:
            user = request_loader(request)

            if user is None:
                raise UnauthorizedException(
                    'authentication required for API access')

        login_user(user)
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


@app.route("/api/model/<id_or_name>/vectors", methods=['POST'])
def create_vectors(id_or_name):
    if id_or_name.isdigit():
        id_or_name = int(id_or_name)

    if request.service.model_exists(id_or_name):
        vectors = [Vector.from_dict(**v) for v in request.json]
        vectors = request.service.create_vectors(id_or_name, vectors)
        return jsonify([v.to_json() for v in vectors])
    else:
        raise NotFoundException('Could not find a model with ID %s' % id)


@app.route("/api/model/<id_or_name>/exists", methods=['GET'])
@api_auth
def model_exists(id_or_name):
    if id_or_name.isdigit():
        id_or_name = int(id_or_name)

    exists = request.service.model_exists(id_or_name)
    return jsonify({'exists': exists})


@app.route("/api/model/<id_or_name>", methods=['GET'])
@api_auth
def get_model(id_or_name):
    if id_or_name.isdigit():
        id_or_name = int(id_or_name)

    if request.service.model_exists(id_or_name):
        model = request.service.get_model(id_or_name)
        return jsonify(model.to_dict())
    else:
        raise NotFoundException('Could not find a model with ID %s' % id)


@app.route("/api/model/create", methods=['POST'])
@app.route("/api/model", methods=['POST'])
@api_auth
def create_model():
    model = request.service.create_model(**request.json)
    return jsonify(model.to_dict()), 201


@app.route("/api/search/model", methods=['GET'])
@api_auth
def find_models():
    models = request.service.find_models(**request.json)
    return jsonify([m.to_dict() for m in models])


@app.route("/api/model/<id_or_name>", methods=['PUT'])
@api_auth
def update_model(id_or_name):
    if id_or_name.isdigit():
        id_or_name = int(id_or_name)

    if request.service.model_exists(id_or_name):
        model = request.service.get_model(id_or_name)
        model = request.service.update_model(id_or_name, **request.json)
        return jsonify(model.to_dict())
    else:
        raise NotFoundException('Could not find a model with ID %s' % id)


@app.route("/api/model/vectors/count", methods=['GET', 'POST'])
@api_auth
def count_vectors_for_model(id_or_name):
    if id_or_name.isdigit():
        id_or_name = int(id_or_name)

    if request.service.model_exists(id_or_name):
        if request.method == 'POST':
            words = request.json
        else:
            words = request.words

        if words and len(words):
            count = request.service.count_vectors_for_words(id_or_name, words)
        else:
            count = request.service.count_vectors_for_model(id_or_name)
        return jsonify({'count': count})
    else:
        raise NotFoundException('Could not find a model with ID %s' % id)


@app.route("/api/model/vectors", methods=['GET', 'POST'])
@api_auth
def get_vectors_for_model(id_or_name):
    if id_or_name.isdigit():
        id_or_name = int(id_or_name)

    if request.service.model_exists(id_or_name):
        if request.method == 'POST':
            words = request.json
        else:
            words = request.words

        if words and len(words):
            vectors = request.service.get_vectors_for_words(id_or_name, words)
        else:
            vectors = request.service.get_vectors_for_model(id_or_name)

        return jsonify([v.to_json() for v in vectors])
    else:
        raise NotFoundException('Could not find a model with ID %s' % id)


def _vectors_response(vectors, template, method, **kwargs):
    at = get_requested_type()

    if at == 'csv':
        return Response(
            _iter_csv([v.to_list() for v in vectors]), mimetype='text/csv')

    return jsonify([v.to_dict() for v in vectors])


def _vectors_from_json(model, json):
    for vector in json:
        v = Vector(word=vector['word'], model=model)
        v.pack_values(vector['values'])
        yield v


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
