import requests
import json

from requests.auth import AuthBase

from functools import wraps

from urllib.parse import urlparse
from sqlalchemy.orm import sessionmaker

from .models import *
from .files import *
from .vectors import *
from .args import *
from .config import *


class FasttextAuth(AuthBase):
    """
    Attaches username/password authentication to the given Request
    object.
    """

    def __init__(self, username=None, password=None, config=None):
        self.username = username
        self.password = password

        if config:
            self.config = config['authentication']
        else:
            self.config = {}

    def __call__(self, r):
        if 'headers' in self.config and 'name' in self.config['headers']:
            name_header = self.config['headers']['name'][0]
        else:
            name_header = 'X-Fasttextdb-Username'

        if 'headers' in self.config and 'password' in self.config['headers']:
            password_header = self.config['headers']['password'][0]
        else:
            password_header = 'X-Fasttextdb-Password'

        r.headers[name_header] = self.username
        r.headers[password_header] = self.password
        return r


def _raise_response_error(func):
    @wraps(func)
    def response_error_wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        response.raise_for_status()
        args[0].session = response.cookies['session']
        return json.loads(response.text)

    return response_error_wrapper


def fasttextdb(url, config=None, engine=None, Session=None, session=None):
    result = urlparse(url)

    if x.scheme == 'http' or x.scheme == 'https':
        return FasttextApi(
            host=x.host,
            port=x.port,
            username=x.username,
            password=x.password,
            config=config)
    else:
        return FasttextDb(
            url=url,
            engine=engine,
            Session=session,
            session=session,
            config=config)


def _to_model(model):
    if isinstance(model, int):
        return Model(id=model)
    elif isinstance(model, str):
        return Model(name=model)
    elif isinstance(model, dict):
        return Model(**model)
    else:
        return model


class FasttextDb(object):
    def __init__(self,
                 url,
                 engine=None,
                 Session=None,
                 session=None,
                 config=None):
        self.url = url
        self.engine = engine
        self.Session = Session
        self.session = session

        if config:
            self.config = config
        else:
            self.config = load_config()

    def open(self):
        if not self.Session:
            if not self.engine:
                self.engine = get_engine(config)

            self.Session = sessionmaker(bind=self.engine)

        self.session = self.Sesssion()
        return self.session

    def close(self):
        if self.session and self.session.is_active:
            self.session.commit()
        if self.session:
            self.session.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def commit_file(self, model, file, session=None):
        batch = []
        model = _to_model(model)

        with open_for_mime_type(file) as f:
            with model_file(f) as num_words, dim, f:
                model.num_words = num_words
                model.dim = dim

                for word, values in read_model_file(f):
                    vector = Vector(word=word)
                    vector.pack_values(values)
                    batch.append(vector)

                    if len(batch) == 1000:
                        self.create_vectors(model, batch)
                        batch = []

                if len(batch) > 0:
                    self.create_vectors(model, batch)
                    batch = []

    def create_vectors(self, model, vectors, session=None):
        model = _to_model(model)

        if not session:
            session = self.open()

        for vector in vectors:
            vector.model = model
            session.add(vector)

        session.commit()

    def get_model(self, model, session=None):
        model = _to_model(model)

        if not session:
            session = self.open()

        if model.id:
            return session.query(Model).get(model.id)
        elif model.name:
            models = list(
                session.query(Model).filter(Model.name == model.name))

            if len(models):
                return models[0]
            else:
                return None
        else:
            raise Exception('must specify either model name or ID')

    def count_vectors_for_words(self, words, model=None, session=None):
        if not session:
            session = self.open()

        model = _to_model(model)
        model = self.get_model(model)
        return Vector.count_vectors_for_words(session, words, model)

    def get_vectors_for_words(self, words, model=None, session=None):
        if not session:
            session = self.open()

        model = _to_model(model)
        model = self.get_model(model)

        return [
            v.to_dict()
            for v in Vector.vectors_for_words(session, words, model)
        ]


class FasttextApi(object):
    def __init__(self,
                 host='localhost',
                 port=8888,
                 username=None,
                 password=None,
                 config=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.session = None

        if config:
            self.config = config
        else:
            self.config = load_config()

        if not self.username and 'username' in self.config:
            self.username = self.config['username']
        if not self.password and 'password' in self.config:
            self.password = self.config['password']

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def _get_url(self, endpoint):
        return 'http://%s:%s/api/%s' % (self.host, self.port, endpoint)

    def _get_cookies(self):
        if self.session:
            return {'session': self.session}
        else:
            return {}

    @_raise_response_error
    def get(self, endpoint, **kwargs):
        return requests.get(
            self._get_url(endpoint),
            cookies=self._get_cookies(),
            auth=FasttextAuth(self.username, self.password, self.config),
            **kwargs)

    @_raise_response_error
    def put(self, endpoint, **kwargs):
        return requests.put(
            self._get_url(endpoint),
            cookies=self._get_cookies(),
            auth=FasttextAuth(self.username, self.password, self.config),
            **kwargs)

    @_raise_response_error
    def post(self, endpoint, **kwargs):
        return requests.post(
            self._get_url(endpoint),
            cookies=self._get_cookies(),
            auth=FasttextAuth(self.username, self.password, self.config),
            **kwargs)

    def commit_file(self, model, file):
        model = _to_model(model)

        if model.id:
            return self.post(
                'model/%s/upload/vectors' % model.id, files={'file': file})
        elif model.name:
            return self.post(
                'model/name/%s/upload/vectors' % model.name,
                files={'file': file})
        else:
            raise Exception('must specify either model ID or name')

    def create_vectors(self, model, vectors):
        model = _to_model(model)

        if model.id:
            url = 'model/%s/vectors' % model.id
        elif model.name:
            url = 'model/name/%s/vectors' % model.name
        else:
            raise Exception('must specify either model ID or name')

        return self.post(url, json=[v.to_dict() for v in vectors])

    def get_model(self, model):
        model = _to_model(model)

        if model.id:
            return Model(**self.get('model/%s' % model.id))
        elif model.name:
            return Model(**self.get('model/name/%s' % model.name))
        else:
            raise Exception('must specify either model name or ID')

    def count_vectors_for_words(self, words, model=None):
        model = _to_model(model)
        model = self.get_model(model)
        return self.post(
            'model/%s/vectors/words/count' % model.id, json=words)['count']

    def get_vectors_for_words(self, words, model=None):
        model = _to_model(model)
        model = self.get_model(model)
        return self.post('model/%s/vectors/words' % model.id, json=words)
