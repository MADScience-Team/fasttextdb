import json
import bz2
import zlib

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy import Unicode, Text, ForeignKey, LargeBinary
from sqlalchemy import SmallInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import func

from flask_login import UserMixin

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

    def to_dict(self):
        return {
            'id': self.id,
            'owner': self.owner,
            'name': self.name,
            'description': self.description,
            'dim': self.dim,
            'inputFile': self.input_file,
            'outputFile': self.output_file,
            'learningRate': self.learning_rate,
            'learningRateUpdateRateChange':
            self.learning_rate_update_rate_change,
            'windowSize': self.window_size,
            'epoch': self.epoch,
            'minCount': self.min_count,
            'negativesSampled': self.negatives_sampled,
            'wordNgrams': self.word_ngrams,
            'lossFunction': self.loss_function,
            'numBuckets': self.num_buckets,
            'minNgramLen': self.min_ngram_len,
            'maxNgramLen': self.max_ngram_len,
            'numThreads': self.num_threads,
            'samplingThreshold': self.sampling_threshold
        }


class Vector(Base):
    """
    Vector for an individual word. Since vectors for different models can have
    different lengths, let's store the values as a simple packed binary blob
    instead of individual float columns. Plus it's quite a bit faster when
    writing the values to the database, at least with sqlite.
    """
    __tablename__ = 'vector'
    id = Column(Integer, primary_key=True)
    word = Column(Unicode, unique=True)
    packed_values = Column(LargeBinary)
    model_id = Column(Integer, ForeignKey('model.id'), index=True)
    model = relationship("Model")
    encoding_compression = Column(SmallInteger)

    @staticmethod
    def count_vectors_for_model(session, model):
        return list(
            session.query(func.count(Vector.id)).filter(Vector.model_id ==
                                                        model.id))[0][0]

    @staticmethod
    def vectors_for_model(session, model):
        return session.query(Vector).filter(Vector.model_id == model.id)

    @staticmethod
    def count_vectors_for_word(session, word, model=None):
        q = session.query(func.count(Vector.id))

        if model:
            q = q.filter(Vector.model_id == model.id)

        return list(q.filter(Vector.word == word))[0][0]

    @staticmethod
    def vectors_for_word(session, word, model=None):
        q = session.query(Vector)

        if model:
            q = q.filter(Vector.model_id == model.id)

        return q.filter(Vector.word == word)

    @staticmethod
    def count_vectors_for_words(session, words, model=None):
        q = session.query(func.count(Vector.id))

        if model:
            q = q.filter(Vector.model_id == model.id)

        return list(q.filter(Vector.word.in_(words)))[0][0]

    @staticmethod
    def vectors_for_words(session, words, model=None):
        q = session.query(Vector)

        if model:
            q = q.filter(Vector.model_id == model.id)

        return q.filter(Vector.word.in_(words))

    def pack_values(self,
                    values,
                    encoding=JSON_ENCODING,
                    compression=BZ2_COMPRESSION):
        """
        Given a list of floats, this method will encode them as JSON
        and optionally compress them into the packed_values column for
        storage in the database. Returns Vector object itself.
        """
        x = values
        x = json.dumps(x)

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

        if (self.encoding_compression & ENCODING_MASK) == MSGPACK_ENCODING:
            x = msgpack.loads(x)
        else:
            x = json.loads(x)

        return x

    def to_dict(self, include_model=False):
        x = {'id': self.id, 'word': self.word, 'values': self.unpack_values()}

        if include_model:
            x['model'] = self.model.to_dict()
        else:
            x['modelId'] = self.model_id

        return x

    def to_list(self):
        return [self.model_id, self.id, self.word] + self.unpack_values()
