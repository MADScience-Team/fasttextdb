from sqlalchemy import create_engine, literal
from sqlalchemy.orm import sessionmaker

from .models import *
from .service import FasttextService, inject_model


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

    def close(self):
        super().open()
        if self.session and self.session.is_active:
            self.session.commit()
        if self.session:
            self.session.close()

    def _commit(self):
        if self.auto_commit:
            self.session.commit()

    @inject_model(True)
    def create_vectors(self, model, vectors):
        for vector in vectors:
            vector.model = model
            self.session.add(vector)

        self._commit()
        self.logger.info('created %s vectors for model %s' %
                         (len(vectors), model.name))
        return vectors

    @inject_model(resolve=False)
    def model_exists(self, model):
        if model.id:
            q = self.session.query(Model).filter(Model.id == model.id)
        elif model.name:
            q = self.session.query(Model).filter(Model.name == model.name)
        else:
            return False

        return self.session.query(literal(True)).filter(q.exists()).scalar()

    @inject_model(resolve=False)
    def get_model(self, model):
        if model and model.id:
            return session.query(Model).get(model.id)
        elif model and model.name:
            models = list(
                self.session.query(Model).filter(Model.name == model.name))

            if len(models):
                return models[0]
            else:
                return None
        else:
            return None

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

    @inject_model(True)
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

        model = super().update_model(
            model,
            owner=owner,
            name=name,
            description=description,
            num_words=num_words,
            dim=dim,
            input_file=input_file,
            output=output,
            lr=lr,
            lr_update_rate=lr_update_rate,
            ws=ws,
            epoch=epoch,
            min_count=min_count,
            neg=neg,
            word_ngrams=word_ngrams,
            loss=loss,
            bucket=bucket,
            minn=minn,
            maxn=maxn,
            thread=thread,
            t=t)

        self._commit()
        return model

    @inject_model()
    def count_vectors_for_model(self, model):
        return Vector.count_vectors_for_model(self.session, model=model)

    @inject_model()
    def get_vectors_for_model(self, model):
        return Vector.vectors_for_model(self.session, model=model)

    @inject_model()
    def count_vectors_for_words(self, model, words):
        return Vector.count_vectors_for_words(self.session, words, model=model)

    @inject_model()
    def get_vectors_for_words(self, model, words):
        return Vector.vectors_for_words(self.session, words, model=model)
