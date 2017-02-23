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


@app.route("/api/model/create", methods=['POST'])
@app.route("/api/model", methods=['POST'])
@api_auth
def api_create_model():
    model = Model(**request.json)
    request.session.add(model)
    request.session.commit()
    return jsonify(model.to_dict()), 201


@app.route("/api/model/<int:id>", methods=['GET'])
@api_auth
def api_get_model(id):
    model = request.session.query(Model).get(id)

    if model:
        return jsonify(model.to_dict())
    else:
        raise NotFoundException('Could not find a model with ID %s' % id)


@app.route("/api/model/<int:id>", methods=['PUT'])
@api_auth
def api_update_model(id):
    model = request.session.query(Model).get(id)

    if not model:
        raise NotFoundException('Could not find a model with ID %s' % id)

    for k in request.json:
        if k != 'id':
            setattr(model, k, model_data[k])

    request.session.commit()
    return jsonify(model.to_dict())


@app.route("/api/models")
@app.route("/api/model", methods=['GET'])
@api_auth
def api_get_models():
    models = request.session.query(Model)
    models = page_request(models)
    return jsonify([m.to_dict() for m in models])


@app.route("/api/model/name/<name>")
@api_auth
def api_get_model_by_name(name):
    models = list(request.session.query(Model).filter(Model.name == name))

    if len(models) == 0:
        raise NotFoundException('no model found with name %s' % name)

    return jsonify(models[0].to_dict())


@app.route("/api/models/count")
@api_auth
def count_models():
    return jsonify(count=Model.count_models(request.session))


@app.route('/api/model/<int:id>/vectors/words/count', methods=['GET', 'POST'])
@api_auth
def api_count_vectors_for_words(id):
    model = request.session.query(Model).get(id)

    if not model:
        raise NotFoundException('Model with ID %s was not found' % id)

    if request.method == 'POST':
        words = request.json
    else:
        words = request.words

    count = Vector.count_vectors_for_words(request.session, words, model)
    return jsonify(count=count)


def _vectors_response(vectors, template, method, **kwargs):
    at = get_requested_type()

    if at == 'csv':
        return Response(
            _iter_csv([v.to_list() for v in vectors]), mimetype='text/csv')

    return jsonify([v.to_dict() for v in vectors])


@app.route('/api/model/<int:id>/vectors', methods=['GET'])
@api_auth
def api_vectors_for_model(id):
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


@app.route('/api/model/<int:id>/vectors/count')
@api_auth
def api_count_vectors_for_model(id):
    model = request.session.query(Model).get(id)

    if not model:
        raise NotFoundException('Model with ID %s was not found' % id)

    count = Vector.count_vectors_for_model(request.session, model)
    return jsonify(count=count)


def _vectors_from_json(model, json):
    for vector in json:
        v = Vector(word=vector['word'], model=model)
        v.pack_values(vector['values'])
        yield v


@app.route('/api/model/<int:id>/vectors', methods=['POST'])
@api_auth
def api_create_vectors_for_model_id(id):
    model = request.session.query(Model).get(id)

    if not model:
        raise NotFoundException('Model with ID %s was not found' % id)

    vectors = list(_vectors_from_json(model, request.json))
    request.session.add_all(vectors)
    return jsonify({'count': len(vectors)})


@app.route('/api/model/name/<name>/vectors', methods=['POST'])
@api_auth
def api_create_vectors_for_model_name(name):
    models = list(request.session.query(Model).filter(Model.name == name))

    if len(models) == 0:
        raise NotFoundException('Model with ID %s was not found' % id)

    model = models[0]
    vectors = list(_vectors_from_json(model, request.json))
    request.session.add_all(vectors)
    return jsonify({'count': len(vectors)})


@app.route('/api/model/<int:id>/vectors/word/<word>')
@api_auth
def api_vectors_for_word(id, word):
    model = request.session.query(Model).get(id)

    if not model:
        raise NotFoundException('Model with ID %s was not found' % id)

    vectors = Vector.vectors_for_word(request.session, word,
                                      model).order_by(asc(Vector.word))
    vectors = page_request(vectors)
    return jsonify([v.to_dict() for v in vectors])


@app.route('/api/model/<int:id>/vectors/words', methods=['PUT', 'POST'])
@api_auth
def api_vectors_for_words_list(id):
    model = request.session.query(Model).get(id)

    if not model:
        raise NotFoundException('Model with ID %s was not found' % id)

    if request.method == 'POST':
        words = request.json
    else:
        words = request.words

    vectors = Vector.vectors_for_words(request.session, words,
                                       model).order_by(asc(Vector.word))
    vectors = page_request(vectors)
    return jsonify([v.to_dict() for v in vectors])


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
