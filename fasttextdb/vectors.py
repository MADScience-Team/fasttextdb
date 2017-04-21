import bz2
import json
from base64 import b64encode, b64decode

from contextlib import contextmanager

from sqlalchemy.orm import sessionmaker

from .files import model_file, read_model_file
from .models import *

__all__ = [
    'model_from_file', 'encode_vectors', 'decode_vectors', 'pack_vectors',
    'unpack_vectors', 'pack_values', 'unpack_values'
]


def pack_values(values):
    return bz2.compress(json.dumps(values).encode())


def unpack_values(packed_values):
    return json.loads(bz2.decompress(packed_values).decode())


def encode_vectors(vectors):
    for v in vectors:
        if 'packed_values' in v:
            v['packed_values'] = b64encode(v['packed_values']).decode()
        yield v


def pack_vectors(vectors):
    for v in vectors:
        if 'values' in v:
            v['packed_values'] = pack_values(v['values'])
            del v['values']
        yield v


def decode_vectors(vectors):
    for v in vectors:
        if 'packed_values' in v:
            v['packed_values'] = b64decode(v['packed_values'].encode())
        yield v


def unpack_vectors(vectors):
    for v in vectors:
        if 'packed_values' in v:
            v['values'] = unpack_values(v['packed_values'])
            del v['packed_values']
        yield v


@contextmanager
def model_from_file(file_, **model_info):
    """
    Wraps modeldb.files.model_file to return a tuple of (Model,
    file_); the Model object can be used with the vectors generator
    """
    with model_file(file_) as (num_words, vec_length, file1):
        yield dict(num_words=num_words, dim=vec_length, **model_info), file1
