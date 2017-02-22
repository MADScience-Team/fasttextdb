from contextlib import contextmanager
from magic import from_buffer
from bz2 import BZ2File
from gzip import GzipFile

from .models import *

__all__ = ["model_file", "read_file", "get_mime_type", "open_for_mime_type"]


def get_mime_type(file):
    mime_type = from_buffer(file.read(1024), mime=True)
    file.seek(0)
    return mime_type


def open_for_mime_type(file):
    mime_type = get_mime_type(file)

    if mime_type == 'application/x-gzip' or mime_type == 'application/gzip':
        f = GzipFile(fileobj=file)
    elif mime_type == 'application/x-bzip2':
        f = BZ2File(filename=file)
    else:
        f = file

    return f


@contextmanager
def model_file(file_):
    """
    Context: prepare to process vectors from a file-like object. Returns tuple
    of (number_words, vector_length, file_pointer) after reading the first line
    for the number of words plus length of vectors.
    """
    l = file_.readline()
    parts = l.split()
    yield (int(parts[0]), int(parts[1]), file_)


def read_file(file_):
    """
    Generator: reads words and vectors from a file (assumes it was opened with
    model_file). Returns tuples of (word, vector), where vector is a list of
    floats.
    """
    l = file_.readline().decode('utf-8')

    while l:
        parts = l.split()
        yield (parts[0], [float(x) for x in parts[1:]])
        l = file_.readline().decode('utf-8')


def read_vectors(file_, model=None):
    """
    Generates vectors by reading a file
    """
    l = file_.readline()

    while l:
        parts = l.split()
        m = Vector(word=parts[0], model=model)

        for i, x in enumerate(parts[1:]):
            setattr(m, 'value%s' % i, float(x))

        yield m
        l = file_.readline()
