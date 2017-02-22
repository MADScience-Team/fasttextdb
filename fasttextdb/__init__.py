import requests
import json

from requests.auth import AuthBase

from functools import wraps

from .models import *
from .files import *
from .vectors import *
from .args import *
from .config import *


class FasttextAuth(AuthBase):
    """Attaches username/password authentication to the given Request object."""

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


def raise_response_error(func):
    @wraps(func)
    def response_error_wrapper(*args, **kwargs):
        response = func(*args, **kwargs)
        response.raise_for_status()
        args[0].session = response.cookies['session']
        return json.loads(response.text)

    return response_error_wrapper


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

    def _get_url(self, endpoint):
        return 'http://%s:%s/api/%s' % (self.host, self.port, endpoint)

    def _get_cookies(self):
        if self.session:
            return {'session': self.session}
        else:
            return {}

    @raise_response_error
    def get(self, endpoint, **kwargs):
        return requests.get(
            self._get_url(endpoint),
            cookies=self._get_cookies(),
            auth=FasttextAuth(self.username, self.password, self.config),
            **kwargs)

    @raise_response_error
    def put(self, endpoint, **kwargs):
        return requests.put(
            self._get_url(endpoint),
            cookies=self._get_cookies(),
            auth=FasttextAuth(self.username, self.password, self.config),
            **kwargs)

    @raise_response_error
    def post(self, endpoint, **kwargs):
        return requests.post(
            self._get_url(endpoint),
            cookies=self._get_cookies(),
            auth=FasttextAuth(self.username, self.password, self.config),
            **kwargs)

    def upload_file(self, file, id=None, name=None):
        if id:
            return self.post(
                'model/%s/upload/vectors' % id, files={'file': file})
        elif name:
            return self.post(
                'model/name/%s/upload/vectors' % name, files={'file': file})
        else:
            raise Exception('must specify either model ID or name')

    def create_vectors(self, vectors, id=None, name=None):
        if id:
            return self.post('model/%s/vectors' % id, json=vectors)
        elif name:
            return self.post('model/name/%s/vectors' % name, json=vectors)
        else:
            raise Exception('must specify either model ID or name')
