import requests

from functools import wraps
from requests.auth import AuthBase

from .service import inject_model, FasttextService
from .models import *


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


def from_dict(cls, multiple=True):
    """
    Takes a single (or list) of dict responses from a function/method
    and maps them to models using the model type's from_dict method.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response = func(*args, **kwargs)

            if multiple:
                return [cls.from_dict(i) for i in response]
            else:
                return cls.from_dict(response)

        return wrapper

    return decorator


def _raise_response_error(func):
    @wraps(func)
    def response_error_wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        response.raise_for_status()
        args[0].session = response.cookies['session']
        return json.loads(response.text)

    return response_error_wrapper


class WebService(object):
    def open(self):
        super().open()
        self.session = None

    def _get_url(self, endpoint):
        return '%s://%s:%s/api/%s' % (self.scheme, self.hostname, self.port,
                                      endpoint)

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

    @inject_model
    def create_vectors(self, model, vectors):
        model = _to_model(model)

        if model.id:
            url = 'model/%s/vectors' % model.id
        elif model.name:
            url = 'model/name/%s/vectors' % model.name
        else:
            raise Exception('must specify either model ID or name')

        return self.post(url, json=[v.to_dict() for v in vectors])

    @from_dict(Model)
    def find_models(self,
                    owner=None,
                    name=None,
                    description=None,
                    num_words=None,
                    dim=None,
                    input_file=None,
                    output_file=None,
                    learning_rate=None,
                    learning_rate_update_rate_change=None,
                    window_size=None,
                    epoch=None,
                    min_count=None,
                    negatives_sampled=None,
                    word_ngrams=None,
                    loss_function=None,
                    num_buckets=None,
                    min_ngram_len=None,
                    max_ngram_len=None,
                    num_threads=None,
                    sampling_threshold=None,
                    session=None):
        raise Exception('not yet implemented')

    @inject_model(resolve=False)
    def model_exists(self, model, session=None):
        raise Exception('not yet implemented')

    @from_dict(Model, multiple=False)
    @inject_model(resolve=False)
    def get_model(self, model):
        if model.id:
            return self.get('model/%s' % model.id)
        elif model.name:
            return self.get('model/name/%s' % model.name)
        else:
            raise Exception('must specify either model name or ID')

    @inject_model()
    def count_vectors_for_words(self, model, words):
        return self.post(
            'model/%s/vectors/words/count' % model.id, json=words)['count']

    @from_dict(Vector)
    @inject_model()
    def get_vectors_for_words(self, model, words):
        return self.post('model/%s/vectors/words' % model.id, json=words)
