import requests
import json

from functools import wraps
from requests.auth import AuthBase

from .service import inject_model, FasttextService
from .vectors import *


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
        if 'headers' in self.config and 'username' in self.config['headers']:
            name_header = self.config['headers']['username'][0]
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

        if 'session' in response.cookies:
            args[0].session = response.cookies['session']
        else:
            args[0].session = None

        return response.json()

    return response_error_wrapper


class WebService(FasttextService):
    def __init__(self,
                 url,
                 name=None,
                 config=None,
                 auto_page=False,
                 auto_page_size=1000,
                 **kwargs):
        super().__init__(url, name=name, config=config)
        self.auto_page = auto_page
        self.auto_page_size = auto_page_size

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
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            auth=FasttextAuth(self.username, self.password, self.config),
            **kwargs)

    @_raise_response_error
    def put(self, endpoint, **kwargs):
        return requests.put(
            self._get_url(endpoint),
            cookies=self._get_cookies(),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            auth=FasttextAuth(self.username, self.password, self.config),
            **kwargs)

    @_raise_response_error
    def post(self, endpoint, **kwargs):
        return requests.post(
            self._get_url(endpoint),
            cookies=self._get_cookies(),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            auth=FasttextAuth(self.username, self.password, self.config),
            **kwargs)

    def model_exists(self, name):
        response = self.get('model/%s/exists' % name)
        return response['exists']

    def get_model(self, name):
        return self.get('model/%s' % name)

    def create_model(self, **kwargs):
        return self.post('model', json=kwargs)

    def create_vectors(self, name, vectors):
        vectors = encode_vectors(pack_vectors(vectors))
        return self.post('model/%s/vectors' % name, json=list(vectors))

    def update_vectors(self, name, vectors):
        vectors = encode_vectors(pack_vectors(vectors))
        return self.put('model/%s/vectors' % name, json=list(vectors))

    def find_models(self,
                    owner=None,
                    name=None,
                    description=None,
                    num_words=None,
                    dim=None,
                    input_file=None,
                    output=None,
                    lr=None,
                    lr_update_rate=None,
                    ws=None,
                    epoch=None,
                    min_count=None,
                    neg=None,
                    word_ngrams=None,
                    loss=None,
                    bucket=None,
                    minn=None,
                    maxn=None,
                    thread=None,
                    t=None):
        return self.post(
            'search/model',
            json={
                'owner': owner,
                'name': name,
                'description': description,
                'num_words': num_words,
                'dim': dim,
                'input_file': input_file,
                'output': output,
                'lr': lr,
                'lr_update_rate': lr_update_rate,
                'ws': ws,
                'epoch': epoch,
                'min_count': min_count,
                'neg': neg,
                'word_ngrams': word_ngrams,
                'loss': loss,
                'bucket': bucket,
                'minn': minn,
                'maxn': maxn,
                'thread': thread,
                't': t
            })

    def update_model(self, name, **kwargs):
        return self.put('model/%s' % name, json=kwargs)

    def get_words(self, name, words=None, exact=False):
        if words is None:
            return self.get('model/%s/words' % name)
        else:
            return self.post(
                'model/%s/words' % name, json=words, params={'exact': exact})

    def count_vectors_for_model(self, name):
        return self.post('model/%s/vectors/count' % name, json=[])['count']

    def get_vectors_for_model(self, name, sort=None, page=None,
                              page_size=None):

        if sort is None or not len(sort):
            sort = ['word']

        return self.post(
            'model/%s/vectors/words' % name,
            json=[],
            params={'sort': sort,
                    'page': page,
                    'page_size': page_size})

    def count_vectors_for_words(self, name, words):
        return self.post('model/%s/vectors/count' % name, json=words)['count']

    def get_vectors_for_words(self,
                              name,
                              words,
                              sort=None,
                              page=None,
                              page_size=None,
                              exact=False):

        if sort is None or not len(sort):
            sort = ['word']

        return self.post(
            'model/%s/vectors/words' % name,
            json=words,
            params={
                'sort': sort,
                'page': page,
                'page_size': page_size,
                'exact': exact
            })
