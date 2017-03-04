import json
import logging
import progressbar

from functools import wraps

from urllib.parse import urlparse, parse_qs

from .models import *
from .files import *
from .config import *


def inject_model(resolve=True):
    """
    Wraps a function/method so that a string (name) or int (id) or
    Model object can be passed in, and a Model instance will be
    resolved and passed in instead
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            service = args[0]
            model = args[1]

            if type(model) == int:
                if resolve and service.model_exists(model):
                    model = service.get_model()
                else:
                    model = Model(id=model)
            elif type(model) == str:
                if resolve and service.model_exists(model):
                    model = service.get_model()
                else:
                    model = Model(name=model)
            elif type(model) is not Model:
                model = None

            nargs = [service, model] + list(args[2:])
            return func(*nargs, **kwargs)

        return wrapper

    return decorator


class FasttextService(object):
    def __init__(self, url, name=None, config=None):
        if name is None:
            name = type(self).__name__

        self.name = name
        self.logger = logging.getLogger(name)

        if len(self.logger.handlers):
            self.logger.addHandler(logging.NullHandler())

        if config:
            self.config = config
        else:
            self.config = load_config()

        self.url = url
        x = urlparse(url)
        self.scheme = x.scheme
        self.hostname = x.hostname
        self.port = x.port
        self.username = x.username
        self.password = x.password
        self.path = x.path
        self.options = parse_qs(x.query)

        if not self.username and 'username' in self.config:
            self.username = self.config['username']
        if not self.password and 'password' in self.config:
            self.password = self.config['password']

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def open(self):
        self.logger.info('opening connection: %s' % self.url)

    def close(self):
        self.logger.info('closing connection: %s' % self.url)

    @inject_model(True)
    def commit_file(self, model, file, progress=False):
        self.logger.info('storing vectors from %s for model %s' %
                         (file.name, model.name))
        batch = []

        if progress:
            bar = progressbar.ProgressBar()

        cnt = 0

        with open_for_mime_type(file) as f:
            with model_file(f) as (num_words, dim, f):
                if progress:
                    bar.max_value = num_words

                if ((model.num_words != num_words) or (model.dim != dim)):
                    model = self.update_model(
                        model, num_words=num_words, dim=dim)

                for word, values in read_model_file(f):
                    vector = Vector(word=word)
                    vector.pack_values(values)
                    batch.append(vector)

                    if len(batch) == 1000:
                        self.create_vectors(model, batch)
                        cnt += len(batch)
                        batch = []
                        if progress:
                            bar.update(cnt)

                if len(batch) > 0:
                    self.create_vectors(model, batch)
                    cnt += len(batch)
                    if progress:
                        bar.update(cnt)
                    batch = []

        self.logger.info('%s vectors stored' % cnt)
