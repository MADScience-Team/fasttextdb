from sqlalchemy import Column, Integer, String, Float, UniqueConstraint
from sqlalchemy import Unicode, Text, ForeignKey, LargeBinary
from sqlalchemy import SmallInteger, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import func

from .util import under_to_camel
from .vectors import *

__all__ = ['User', 'Base', 'Model', 'Vector']

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

    __table_args__ = (UniqueConstraint(
        'model_name', 'word', name='uk_model_word'), )

    def to_dict(self,
                camel=False,
                include_model=False,
                include_model_name=False,
                packed=False):
        """
        Converts the vector to a dict, suitable for encoding to
        JSON. The Model values are under the key 'values'.
        """
        x = {'id': self.id, 'word': self.word}

        if packed:
            x['packed_values'] = self.packed_values
        else:
            x['values'] = list(unpack_values(self.packed_values))

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
        return [self.model_name, self.word] + unpack_values(self.packed_values)
