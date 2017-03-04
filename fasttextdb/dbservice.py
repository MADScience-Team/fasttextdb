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

    @inject_model(True)
    def create_vectors(self, model, vectors):
        for vector in vectors:
            vector.model = model
            self.session.add(vector)

        self.session.commit()
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

    def _eq_or_range(self, type_, col, param, q):
        if type(param) == type_:
            return q.filter(col == param)
        else:
            try:
                if len(param) > 1:
                    if len(param) == 2:
                        return q.filter(col.between(*param))
                    else:
                        return q.filter(col == param[0])
            except:
                # Guess this wasn't an iterable?
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

        if not session:
            session = self.open()

        q = session.query(Model)
        q = self._like(Model.owner, owner, q)
        q = self._like(Model.name, name, q)
        q = self._like(Model.description, description, q)
        q = self._eq_or_range(int, Model.num_words, num_words, q)
        q = self._eq_or_range(int, Model.dim, dim, q)
        q = self._like(Model.input_file, input_file, q)
        q = self._like(Model.output_file, output_file, q)
        q = self._eq_or_range(float, Model.learning_rate, learning_rate, q)
        q = self._eq_or_range(int, Model.learning_rate_update_rate_change,
                              learning_rate_update_rate_change, q)
        q = self._eq_or_range(int, Model.window_size, window_size, q)
        q = self._eq_or_range(int, Model.epoch, epoch, q)
        q = self._eq_or_range(int, Model.min_count, min_count, q)
        q = self._eq_or_range(int, Model.negatives_sampled, negatives_sampled,
                              q)
        q = self._eq_or_range(int, Model.word_ngrams, word_ngrams, q)

        q = self._like(Model.loss_function, loss_function, q)

        q = self._eq_or_range(int, Model.num_buckets, num_buckets, q)
        q = self._eq_or_range(int, Model.min_ngram_len, min_ngram_len, q)
        q = self._eq_or_range(int, Model.max_ngram_len, max_ngram_len, q)
        q = self._eq_or_range(int, Model.num_threads, num_threads, q)
        q = self._eq_or_range(float, Model.sampling_threshold,
                              sampling_threshold, q)

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
                     sampling_threshold=None):

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
        if output_file:
            model.output_file = output_file
        if learning_rate:
            model.learning_rate = learning_rate
        if learning_rate_update_rate_change:
            model.learning_rate_update_rate_change = learning_rate_update_rate_change
        if window_size:
            model.window_size = window_size
        if epoch:
            model.epoch = epoch
        if min_count:
            model.min_count = min_count
        if negatives_sampled:
            model.negatives_sampled = negatives_sampled
        if word_ngrams:
            model.word_ngrams = word_ngrams
        if loss_function:
            model.loss_function = loss_function
        if num_buckets:
            model.num_buckets = num_buckets
        if min_ngram_len:
            model.min_ngram_len = min_ngram_len
        if max_ngram_len:
            model.max_ngram_len = max_ngram_len
        if num_threads:
            model.num_threads = num_threads
        if sampling_threshold:
            model.sampling_threshold = sampling_threshold

        self.session.commit()
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
