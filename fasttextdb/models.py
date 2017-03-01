import json
import bz2
import zlib
import base64

from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from sqlalchemy import Unicode, Text, ForeignKey, LargeBinary
from sqlalchemy import SmallInteger, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import func

from flask_login import UserMixin

from .util import under_to_camel

__all__ = [
    'User', 'Base', 'Model', 'Vector', 'NO_COMPRESSION', 'ZLIB_COMPRESSION',
    'BZ2_COMPRESSION', 'JSON_ENCODING'
]

COMPRESSION_MASK = 0b00001111
NO_COMPRESSION = 0b11110000
ZLIB_COMPRESSION = 0b00000001
BZ2_COMPRESSION = 0b00000010
ENCODING_MASK = 0b11110000
JSON_ENCODING = 0b00010000

Base = declarative_base()


class User(Base, UserMixin):
    """
    Contains information sufficient to authenticate a user by user ID
    and password
    """
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    password_hash = Column(String)

    def is_authenticated(self):
        if hasattr(self, '_authenticated'):
            return self._authenticated
        else:
            return True

    def set_authenticated(self, authenticated):
        self._authenticated = authenticated

    def get_id(self):
        return self.name


class Model(Base):
    """
    Metadata for a model (set of vectors)
    """
    __tablename__ = 'model'
    id = Column(Integer, primary_key=True)
    owner = Column(String)
    name = Column(String)
    description = Column(Text)
    num_words = Column(Integer)
    dim = Column(Integer)
    input_file = Column(String)
    output_file = Column(String)
    learning_rate = Column(Float)
    learning_rate_update_rate_change = Column(Integer)
    window_size = Column(Integer)
    epoch = Column(Integer)
    min_count = Column(Integer)
    negatives_sampled = Column(Integer)
    word_ngrams = Column(Integer)
    loss_function = Column(String)
    num_buckets = Column(Integer)
    min_ngram_len = Column(Integer)
    max_ngram_len = Column(Integer)
    num_threads = Column(Integer)
    sampling_threshold = Column(Float)

    @staticmethod
    def count_models(session):
        return list(session.query(func.count(Model.id)))[0][0]

    @staticmethod
    def from_dict(data):
        return Model(**data)

    def to_dict(self, camel=False):
        d = {
            'id': self.id,
            'owner': self.owner,
            'name': self.name,
            'description': self.description,
            'dim': self.dim,
            'input_file': self.input_file,
            'output_file': self.output_file,
            'learning_rate': self.learning_rate,
            'learning_rate_update_rate_change':
            self.learning_rate_update_rate_change,
            'window_size': self.window_size,
            'epoch': self.epoch,
            'min_count': self.min_count,
            'negatives_sampled': self.negatives_sampled,
            'word_ngrams': self.word_ngrams,
            'loss_function': self.loss_function,
            'num_buckets': self.num_buckets,
            'min_ngram_len': self.min_ngram_len,
            'max_ngram_len': self.max_ngram_len,
            'num_threads': self.num_threads,
            'sampling_threshold': self.sampling_threshold
        }

        if camel:
            d2 = {}

            for k in d:
                k2 = under_to_camel(k)
                d2[k2] = d[k]

            d = d2

        return d


class Vector(Base):
    """
    Vector for an individual word. Since vectors for different models
    can have different lengths, we'll store the values as a simple
    packed blob of some sort instead of individual float columns. Plus
    it's quite a bit faster when writing the values to the database,
    at least with sqlite. The packed value is encoded as JSON and
    optionally compressed.
    """
    __tablename__ = 'vector'
    id = Column(Integer, primary_key=True)
    word = Column(Unicode)
    packed_values = Column(LargeBinary)
    model_id = Column(Integer, ForeignKey('model.id'), index=True)
    model = relationship("Model")
    encoding_compression = Column(SmallInteger)

    __table_args__ = (UniqueConstraint(
        'model_id', 'word', name='uk_model_word'), )

    @staticmethod
    def count_vectors_for_model(session, model):
        """
        Count the vectors in the database that belong to the specified
        model. Returns the count.
        """
        return list(
            session.query(func.count(Vector.id)).filter(Vector.model_id ==
                                                        model.id))[0][0]

    @staticmethod
    def vectors_for_model(session, model):
        """
        Query for vectors belonging to the specified model. Returns
        the query object, which can be iterated over to get the
        vectors, or further constrained.
        """
        return session.query(Vector).filter(Vector.model_id == model.id)

    @staticmethod
    def count_vectors_for_word(session, word, model=None):
        """
        Count vectors matching an single word and optionally
        belonging to the specified model. Returns the query object,
        which can be iterated over to get the vectors, or further
        constrained.
        """
        q = session.query(func.count(Vector.id))

        if model:
            q = q.filter(Vector.model_id == model.id)

        return list(q.filter(Vector.word == word))[0][0]

    @staticmethod
    def vectors_for_word(session, word, model=None):
        """
        Query for vectors matching an single word and optionally
        belonging to the specified model. Returns the query object,
        which can be iterated over to get the vectors, or further
        constrained.
        """
        q = session.query(Vector)

        if model:
            q = q.filter(Vector.model_id == model.id)

        return q.filter(Vector.word == word)

    @staticmethod
    def count_vectors_for_words(session, words, model=None):
        """
        Count vectors matching any of the specfied words and optionally
        belonging to the specified model. Returns the query object,
        which can be iterated over to get the vectors, or further
        constrained.
        """
        q = session.query(func.count(Vector.id))

        if model:
            q = q.filter(Vector.model_id == model.id)

        return list(
            q.filter(or_(* [Vector.word.like(w) for w in words])))[0][0]

    @staticmethod
    def vectors_for_words(session, words, model=None):
        """
        Query for vectors matching any of the specified words and optionally
        belonging to the specified model. Returns the query object,
        which can be iterated over to get the vectors, or further
        constrained.
        """
        q = session.query(Vector)

        if model:
            q = q.filter(Vector.model_id == model.id)

        return q.filter(or_(* [Vector.word.like(w) for w in words]))

    @staticmethod
    def from_dict(data):
        v = Vector(
            word=data['word'],
            encoding_compression=data['encoding_compression'])

        if 'packed_values' in data:
            v.packed_values = base64.b64decode(data['packed_values'])
        elif 'values' in data:
            v.values = data['values']
            v.pack_values(data['values'])

        if 'model_id' in data:
            v.model_id = data['model_id']
            v.model = Model(id=data['model_id'])
        elif 'model' in data:
            m = Model.from_dict(data['model'])
            v.model_id = m.id
            v.model = m

        return v

    def pack_values(self, values, encoding=None, compression=None):
        """
        Given a list of floats, this method will encode them as JSON
        and optionally compress them into the packed_values column for
        storage in the database. Returns Vector object itself.
        """
        x = values
        x = json.dumps(x)

        if not compression:
            compression = self.encoding_compression & COMPRESSION_MASK

        if (compression & COMPRESSION_MASK) == BZ2_COMPRESSION:
            x = bz2.compress(str.encode(x))
        elif (compression & COMPRESSION_MASK) == ZLIB_COMPRESSION:
            x = zlib.compress(str.encode(x))

        self.packed_values = x
        self.encoding_compression = encoding ^ compression
        return self

    def unpack_values(self):
        """
        unpacks (msgpack.unpackb) the stored float values and returns the list
        """
        x = self.packed_values

        if (self.encoding_compression & COMPRESSION_MASK) == BZ2_COMPRESSION:
            x = bz2.decompress(x)
        elif (self.encoding_compression &
              COMPRESSION_MASK) == ZLIB_COMPRESSION:
            x = zlib.decompress(x)

        x = json.loads(x)

        return x

    def to_dict(self,
                camel=False,
                include_model=False,
                include_model_id=False,
                packed=False):
        """
        Converts the vector to a dict, suitable for encoding to
        JSON. The Model values are under the key 'values'.
        """
        x = {
            'id': self.id,
            'word': self.word,
            'encoding_compression': self.encoding_compression
        }

        if packed:
            x['packed_values'] = base64.b64encode(self.packed_values).decode()
        else:
            x['values'] = self.unpack_values()

        if include_model:
            x['model'] = self.model.to_dict()
        elif include_model_id:
            x['model_id'] = self.model_id

        if camel:
            x2 = {}

            for k in x:
                k2 = under_to_camel(k)
                x2[k2] = x[k]

            x = x2

        return x

    def to_list(self):
        """
        Converts the vector to a list, suitable for encoding as a CSV row.
        """
        return [self.model_id, self.id, self.word] + self.unpack_values()
