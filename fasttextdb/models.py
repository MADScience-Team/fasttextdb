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


class User(Base):
    """
    Contains information sufficient to authenticate a user by user ID
    and password
    """
    __tablename__ = 'user'
    username = Column(String, primary_key=True)
    password_hash = Column(String)

    def to_dict(self):
        return {'username': self.username, 'password_hash': self.password_hash}


#class Namespace(Base):
#    __tablename__ = 'namespace'
#    name = Column(String, primary_key=True)
#    description = Column(Text)


class Model(Base):
    """
    Metadata for a model (set of vectors)
    """
    __tablename__ = 'model'
    owner = Column(String)
    name = Column(String, primary_key=True)
    description = Column(Text)
    num_words = Column(Integer)
    dim = Column(Integer)
    input_file = Column(String)
    output = Column(String)
    lr = Column(Float)
    lr_update_rate = Column(Integer)
    ws = Column(Integer)
    epoch = Column(Integer)
    min_count = Column(Integer)
    neg = Column(Integer)
    word_ngrams = Column(Integer)
    loss = Column(String)
    bucket = Column(Integer)
    minn = Column(Integer)
    maxn = Column(Integer)
    thread = Column(Integer)
    t = Column(Float)

    @staticmethod
    def count_models(session):
        return list(session.query(func.count(Model.name)))[0][0]

    @staticmethod
    def from_dict(data):
        return Model(**data)

    def to_dict(self, camel=False):
        d = {
            'owner': self.owner,
            'name': self.name,
            'description': self.description,
            'num_words': self.num_words,
            'dim': self.dim,
            'input_file': self.input_file,
            'output': self.output,
            'lr': self.lr,
            'lr_update_rate': self.lr_update_rate,
            'ws': self.ws,
            'epoch': self.epoch,
            'min_count': self.min_count,
            'neg': self.neg,
            'word_ngrams': self.word_ngrams,
            'loss': self.loss,
            'bucket': self.bucket,
            'minn': self.minn,
            'maxn': self.maxn,
            'thread': self.thread,
            't': self.t
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
    model_name = Column(String, ForeignKey('model.name'), index=True)
    model = relationship("Model")
    encoding_compression = Column(SmallInteger)

    __table_args__ = (UniqueConstraint(
        'model_name', 'word', name='uk_model_word'), )

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
            if not self.encoding_compression:
                compression = BZ2_COMPRESSION
            else:
                compression = self.encoding_compression & COMPRESSION_MASK

        if not encoding:
            if not self.encoding_compression:
                encoding = JSON_ENCODING
            else:
                encoding = self.encoding_compression & ENCODING_MASK

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
                include_model_name=False,
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
        elif include_model_name:
            x['model_name'] = self.model_name

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
        return [self.model_name, self.id, self.word] + self.unpack_values()
