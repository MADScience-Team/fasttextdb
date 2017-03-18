import bz2
import gzip

from contextlib import contextmanager
from magic import from_buffer

from .models import *

__all__ = [
    "model_file", "read_model_file", "get_mime_type", "open_for_mime_type"
]


def get_mime_type(file):
    """
    Reads enough of a file to determine its MIME type using the
    python-magic package, thoughtfully seeks the file back to its
    original position
    """
    pos = file.tell()
    file.seek(0)
    mime_type = from_buffer(file.read(1024), mime=True)
    file.seek(pos)
    return mime_type


@contextmanager
def open_for_mime_type(file, mode='rt'):
    """
    Given a file, use its MIME type to determine whether the file is
    compressed. Then, wrap the file in a GzipFile or BZ2File
    decompressor as necessary. This is a contextmanager, use with
    """
    mime_type = get_mime_type(file)

    if mime_type == 'application/x-gzip' or mime_type == 'application/gzip':
        yield gzip.open(file, mode=mode)
    elif mime_type == 'application/x-bzip2':
        yield bz2.open(file, mode=mode)
    else:
        yield file


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


def read_model_file(file_):
    """
    Generator: reads words and vectors from a file (assumes it was opened with
    model_file). Returns tuples of (word, vector), where vector is a list of
    floats.
    """
    l = file_.readline()

    while l:
        parts = l.split()
        yield (parts[0], [float(x) for x in parts[1:]])
        l = file_.readline()
