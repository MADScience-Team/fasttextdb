from functools import wraps
from sqlalchemy import create_engine, literal, func, or_, asc, desc
from sqlalchemy.orm import sessionmaker

from .models import *
from .service import FasttextService, inject_model


def to_dict(func):
    @wraps(func)
    def convert(*args, **kwargs):
        m = func(*args, **kwargs)

        if m is None:
            return None
        else:
            return m.to_dict()

    return convert


def to_dicts(func):
    @wraps(func)
    def convert(*args, **kwargs):
        items = func(*args, **kwargs)

        if items is None:
            return None
        else:
            return [i.to_dict() for i in items]

    return convert


class DbService(FasttextService):
    def __init__(self,
                 url,
                 name=None,
                 config=None,
                 engine=None,
                 Session=None,
                 session=None):
        super().__init__(url, name=name, config=config)
        self.engine = engine
        self.Session = Session
        self.session = session
        self.auto_commit = True

    def open(self):
        super().open()
        if not self.session:
            if not self.Session:
                if not self.engine:
                    self.engine = create_engine(self.url)

                self.Session = sessionmaker(bind=self.engine)

            self.session = self.Session()
        return self.session

    def close(self, error=None):
        super().open()
        if self.session and self.session.is_active:
            if error:
                self.session.rollback()
            else:
                self.session.commit()
        if self.session:
            self.session.close()
            self.session = None

    def _commit(self):
        if self.auto_commit:
            self.session.commit()

    def _parse_sort(self, sorts):
        for sort in sorts:
            parts = sort.split('~')
            if len(parts) > 1:
                if parts[1] == 'desc':
                    yield parts[0], desc
                else:
                    yield parts[0], asc
            else:
                yield parts[0], asc

    def _apply_limit_offset(self, query, sort, page, page_size):
        if sort is not None and len(sort):
            query = query.order_by(
                * [s[1](s[0]) for s in self._parse_sort(sort)])

        if page_size is not None:
            query = query.limit(page_size)

        if page is not None:
            query = query.offset(page * page_size)

        print('sort %s' % sort)
        print('query %s' % query)

        return query

    @to_dict
    def get_user(self, username):
        return self.session.query(User).get(username)

    @inject_model(True)
    def create_vectors(self, model, vectors):
        for vector in vectors:
            vector.model = model
            self.session.add(vector)

        self._commit()
        self.logger.info('created %s vectors for model %s' %
                         (len(vectors), model.name))
        return vectors

    def model_exists(self, name):
        return self.session.query(func.count(Model.name)).filter(
            Model.name == name)[0][0] > 0

    @to_dict
    def get_model(self, name):
        return self.session.query(Model).get(name)

    def create_model(self, **kwargs):
        model = Model(**kwargs)
        self.session.add(model)
        self._commit()
        return model

    def _eq_or_range(self, type_, col, param, q):
        if type(param) == type_:
            return q.filter(col == param)
        else:
            try:
                if len(param) > 0:
                    if len(param) == 2:
                        return q.filter(col.between(*param))
                    else:
                        return q.filter(col == param[0])
            except:
                # Guess this wasn't an iterable?
                return q

    def _eq_or_in(self, type_, col, param, q):
        if type(param) == type_:
            return q.filter(col == param)
        elif param:
            return q.filter(col.in_(param))
        else:
            return q

    def _like(self, col, param, q):
        if param:
            return q.filter(col.like(param))
        else:
            return q

    @to_dicts
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

        q = self.session.query(Model)
        q = self._like(Model.owner, owner, q)
        q = self._like(Model.name, name, q)
        q = self._like(Model.description, description, q)
        q = self._eq_or_range(int, Model.num_words, num_words, q)
        q = self._eq_or_range(int, Model.dim, dim, q)
        q = self._like(Model.input_file, input_file, q)
        q = self._like(Model.output, output, q)
        q = self._eq_or_range(float, Model.lr, lr, q)
        q = self._eq_or_range(int, Model.lr_update_rate, lr_update_rate, q)
        q = self._eq_or_range(int, Model.ws, ws, q)
        q = self._eq_or_range(int, Model.epoch, epoch, q)
        q = self._eq_or_range(int, Model.min_count, min_count, q)
        q = self._eq_or_range(int, Model.neg, neg, q)
        q = self._eq_or_range(int, Model.word_ngrams, word_ngrams, q)

        q = self._eq_or_in(str, Model.loss, loss, q)

        q = self._eq_or_range(int, Model.bucket, bucket, q)
        q = self._eq_or_range(int, Model.minn, minn, q)
        q = self._eq_or_range(int, Model.maxn, maxn, q)
        q = self._eq_or_range(int, Model.thread, thread, q)
        q = self._eq_or_range(float, Model.t, t, q)

        return q

    @to_dict
    def update_model(self, name, **kwargs):
        model = self.session.query(Model).get(name)

        if model is None:
            return None

        for k in kwargs:
            if hasattr(model, k):
                setattr(model, k, kwargs[k])

        self._commit()
        return model

    def count_vectors_for_model(self, name):
        return self.session.query(func.count(Vector.id)).filter(
            Vector.model_name == name)[0][0]

    @to_dicts
    def get_vectors_for_model(self, name, sort=None, page=None,
                              page_size=None):
        if sort is None or not len(sort):
            sort = ['word']
        q = self.session.query(Vector).filter(Vector.model_name == name)
        q = self._apply_limit_offset(q, sort, page, page_size)
        return q

    def count_vectors_for_words(self, name, words):
        return self.session.query(func.count(Vector.id)).filter(
            Vector.model_name == name).filter(
                or_(* [Vector.word.like(w) for w in words]))[0][0]

    @to_dicts
    def get_vectors_for_words(self,
                              name,
                              words,
                              sort=None,
                              page=None,
                              page_size=None):
        if sort is None or not len(sort):
            sort = ['word']
        q = self.session.query(Vector).filter(
            Vector.model_name == name).filter(
                or_(* [Vector.word.like(w) for w in words]))
        q = self._apply_limit_offset(q, sort, page, page_size)
        return q
