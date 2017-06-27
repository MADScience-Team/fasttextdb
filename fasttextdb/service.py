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
                    model = service.get_model(model)
                else:
                    model = Model(id=model)
            elif type(model) == str:
                if resolve and service.model_exists(model):
                    model = service.get_model(model)
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

    def create_vectors(self, model, vectors):
        raise Exception('requires subclass implementation')

    def model_exists(self, model):
        raise Exception('requires subclass implementation')

    def get_model(self, model):
        raise Exception('requires subclass implementation')

    def create_model(self, **kwargs):
        raise Exception('requires subclass implementation')

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
                    t=None,
                    session=None):
        raise Exception('requires subclass implementation')

    def update_model(self,
                     model,
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
        if owner:
            model.owner = owner
        if name:
            model.name = name
        if description:
            model.description = description
        if num_words:
            model.num_words = num_words
        if dim:
            model.dim = dim
        if input_file:
            model.input_file = input_file
        if output:
            model.output = output
        if lr:
            model.lr = lr
        if lr_update_rate:
            model.lr_update_rate = lr_update_rate
        if ws:
            model.ws = ws
        if epoch:
            model.epoch = epoch
        if min_count:
            model.min_count = min_count
        if neg:
            model.neg = neg
        if word_ngrams:
            model.word_ngrams = word_ngrams
        if loss:
            model.loss = loss
        if bucket:
            model.bucket = bucket
        if minn:
            model.minn = minn
        if maxn:
            model.maxn = maxn
        if thread:
            model.thread = thread
        if t:
            model.t = t

        return model

    def _process_batch(self, name, batch, force=False):
        if force:
            new_ = {v['word']: v for v in batch}
            existing = []
        else:
            by_word = {v['word']: v for v in batch}

            existing = {
                w: by_word[w]
                for w in self.get_words(
                    name, list(by_word.keys()), exact=True)
            }

            new_ = {v['word']: v for v in batch if v['word'] not in existing}

        if len(new_):
            self.create_vectors(name, new_.values())
        if len(existing):
            self.update_vectors(name, existing.values())

    def commit_file(self, name, file, progress=False, force=False):
        if hasattr(file, 'name'):
            filename = file.name
        else:
            filename = '???'

        self.logger.info('storing vectors from %s for model %s' %
                         (filename, name))
        batch = []

        cnt = 0

        if self.model_exists(name):
            model = self.get_model(name)
        else:
            model = {'name': name, 'num_words': None, 'dim': None}
            self.create_model(**model)

        with open_for_mime_type(file) as f:
            with model_file(f, otype=dict) as fmodel:
                if progress:
                    bar = progressbar.ProgressBar(
                        max_value=fmodel['num_words'])

                if ((fmodel['num_words'] != model['num_words']) or
                    (fmodel['dim'] != model['dim'])):
                    model = self.update_model(
                        name, num_words=fmodel['num_words'], dim=fmodel['dim'])

                for vector in read_model_file(f, otype=dict):
                    batch.append(vector)

                    if len(batch) == 500:
                        self._process_batch(name, batch, force=force)
                        cnt += len(batch)
                        batch = []
                        if progress:
                            bar.update(cnt)

                if len(batch) > 0:
                    self._process_batch(name, batch, force=force)
                    cnt += len(batch)
                    if progress:
                        bar.update(cnt)
                    batch = []

        self.logger.info('%s vectors stored' % cnt)

    def count_vectors_for_model(self, model):
        raise Exception('requires subclass implementation')

    def get_vectors_for_model(self, model):
        raise Exception('requires subclass implementation')

    def count_vectors_for_words(self, model, words):
        raise Exception('requires subclass implementation')

    def get_vectors_for_words(self, model, words):
        raise Exception('requires subclass implementation')
