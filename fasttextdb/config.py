import yaml
import os
import sqlalchemy

from importlib import import_module
from copy import deepcopy

#from .web.authenticate import *
from .models import *

__all__ = [
    "CONFIG_SEARCH_PATH", "CONFIG_DEFAULTS", "ConfigException", "get_engine",
    "load_config"
]

CONFIG_SEARCH_PATH = [
    os.path.join(os.getcwd(), "fasttextdb.yml"),
    os.path.join(os.getcwd(), "config.yml"),
    os.path.join(os.path.expanduser('~'), ".fasttextdb.yml"),
    os.path.join(os.path.abspath(os.sep), "etc", "fasttextdb", "config.yml")
]

if 'FASTTEXTDB_CONFIG' in os.environ:
    CONFIG_SEARCH_PATH = [os.environ['FASTTEXTDB_CONFIG']] + CONFIG_SEARCH_PATH

CONFIG_DEFAULTS = {
    'db': {
        'url': 'sqlite:///fasttext.db',
        'echo': False
    },
    'vectors': {
        'encoding': 'json',
        'compression': 'bz2'
    },
    'host': '127.0.0.1',
    'port': 8888,
    'debug': False,
    'authentication': {
        'credentials': ('.authenticate.get_credentials', 'fasttextdb'),
        'verify': ('.authenticate.sha256_verify', 'fasttextdb'),
        'loader': ('.authenticate.load_user', 'fasttextdb'),
        'headers': {
            'name': ['X-Fasttextdb-Username'],
            'password': ['X-Fasttextdb-Password']
        },
        'form': {
            'name': ['name', 'username'],
            'password': ['password']
        },
        'json': {
            'name': ['name', 'username', 'userName'],
            'password': ['password']
        }
    },
    'users': {}
}


class ConfigException(Exception):
    pass


def get_engine(config):
    """
    Return an sqlalchemy.engine.Engine instance, based on the
    configuration provided in the db key of the config dictionary
    passed in.
    """
    return sqlalchemy.engine_from_config(config['db'], prefix='')


def _merge_dict(target, *sources):
    for source in sources:
        for k in target:
            if k in source:
                if type(source[k]) is dict:
                    _merge_dict(target[k], source[k])
                else:
                    target[k] = source[k]

        for k in source:
            if k not in target:
                target[k] = source[k]

    return target


def _resolve_function(fn):
    if type(fn) is tuple:
        package = fn[1]
        fn = fn[0]
    else:
        package = None

    parts = fn.split('.')
    module = import_module('.'.join(parts[:-1]), package)
    return getattr(module, parts[-1])


def _resolve_config_items(config):
    for k in config['users']:
        user = config['users'][k]
        kwargs = {'name': k, 'password_hash': user['password_hash']}
        config['users'][k] = User(**kwargs)

    if not callable(config['authentication']['loader']):
        config['authentication']['loader'] = _resolve_function(
            config['authentication']['loader'])

    if not callable(config['authentication']['verify']):
        config['authentication']['verify'] = _resolve_function(
            config['authentication']['verify'])

    if not callable(config['authentication']['credentials']):
        config['authentication']['credentials'] = _resolve_function(
            config['authentication']['credentials'])

    return config


def load_config(path=None, file_=None, args=None):
    """
    Load a YAML configuration from one of these sources, in order of
    priority:

    - config_string (plain string with YAML code)
    - env_var (an envrionment variable pointing to some YAML)
    - file_ (a file pointer with some YAML in it)
    - path (a path to a file with some YAML in it)
    - FASTTEXTDB_CONFIG (environment variable pointing to a path to a file)

    If none of those are specified, I'll look in CONFIG_SEARCH_PATH
    for an existing file to read. The configuration (if found) will be
    returned as a dict, merged with the CONFIG_DEFAULTS.
    """
    cdef = deepcopy(CONFIG_DEFAULTS)
    configs = []

    search_path = CONFIG_SEARCH_PATH

    if args and args.config_path:
        search_path = [args.config_path]

    if not file_:
        if not path:
            for p in search_path:
                if os.path.isfile(p):
                    path = p
                    break

        if not path:
            return cdef

        file_ = open(path)

    if file_:
        configs.append(yaml.load(file_))

    if args:
        configs.append(_config_from_args(args))

    return _resolve_config_items(_merge_dict(cdef, *configs))


def _config_from_args(args):
    c = {}

    if args.secret:
        c['secret'] = args.secret
    if args.host:
        c['host'] = args.host
    if args.port:
        c['port'] = args.port
    if args.debug:
        c['debug'] = args.debug
    if args.username:
        c['username'] = args.username
    if args.password:
        c['password'] = args.password

    return c
