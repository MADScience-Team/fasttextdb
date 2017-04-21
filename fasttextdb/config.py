import yaml
import os
import sqlalchemy
import logging.config
import secrets

from importlib import import_module
from copy import deepcopy

#from .web.authenticate import *
from .models import *

__all__ = [
    "CONFIG_SEARCH_PATH", "CONFIG_DEFAULTS", "ConfigException", "load_config"
]

CONFIG_SEARCH_PATH = [
    os.path.join(os.getcwd(), "fasttextdb.yml"),
    os.path.join(os.getcwd(), "config.yml"),
    os.path.join(os.path.expanduser('~'), ".fasttextdb.yml"),
    os.path.join(os.path.abspath(os.sep), "etc", "fasttextdb.yml"),
    os.path.join(os.path.abspath(os.sep), "etc", "fasttextdb", "config.yml")
]

if 'FASTTEXTDB_CONFIG' in os.environ:
    CONFIG_SEARCH_PATH = [os.environ['FASTTEXTDB_CONFIG']] + CONFIG_SEARCH_PATH

CONFIG_DEFAULTS = {
    'url': 'sqlite:///fasttext.db',
    'progress': False,
    'vectors': {
        'encoding': 'json',
        'compression': 'bz2'
    },
    'secret': secrets.token_hex(nbytes=16),
    'debug': False,
    'logging': {
        'version': 1
    },
    'authentication': {
        'loader': ('.authenticate.load_user', 'fasttextdb'),
        'headers': {
            'username': ['X-Fasttextdb-Username', 'X-Fasttextdb-Name'],
            'password': ['X-Fasttextdb-Password']
        },
        'form': {
            'username': ['username', 'name'],
            'password': ['password']
        },
        'json': {
            'username': ['username', 'userName'],
            'password': ['password']
        }
    },
    'users': {}
}


class ConfigException(Exception):
    pass


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
        kwargs = {'username': k, 'password_hash': user['password_hash']}
        config['users'][k] = kwargs

    if not callable(config['authentication']['loader']):
        config['authentication']['loader'] = _resolve_function(
            config['authentication']['loader'])

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
        file_.close()

    if args:
        configs.append(_config_from_args(args))

    cfg = _resolve_config_items(_merge_dict(cdef, *configs))
    logging.config.dictConfig(cfg['logging'])
    return cfg


def _config_from_args(args):
    c = {}

    if args.secret:
        c['secret'] = args.secret
    if args.url:
        c['url'] = args.url
    if args.debug:
        c['debug'] = args.debug
    if args.progress:
        c['progress'] = args.progress

    return c
