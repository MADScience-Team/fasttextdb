from contextlib import contextmanager

from sqlalchemy.orm import sessionmaker

from .files import model_file, read_model_file
from .models import *

__all__ = ['commit_file', 'commit_vectors', 'model_from_file']


def _get_session(engine=None, Session=None, session=None):
    if not session:
        if not Session:
            if not engine:
                raise Exception(
                    'Must provide one of engine, Session, or session')
            Session = sessionmaker(bind=engine)
        session = Session()
    return session


def commit_file(file_,
                engine=None,
                Session=None,
                session=None,
                commit_interval=100,
                encoding=JSON_ENCODING,
                compression=BZ2_COMPRESSION,
                model=None,
                **model_info):
    """
    Processes a file(-like object), extracts Vectors, and commits them
    to the database. Yields the vectors as it proceeds, to allow for
    progress monitoring
    """
    with model_from_file(file_, **model_info) as (m, file1):
        for vector in commit_vectors(
                vectors(
                    read_model_file(file1),
                    model or m,
                    encoding=encoding,
                    compression=compression),
                engine=engine,
                Session=Session,
                session=session,
                commit_interval=commit_interval):
            yield vector


def commit_vectors(source,
                   engine=None,
                   Session=None,
                   session=None,
                   commit_interval=100):
    """
    Takes a source of vectors and adds them to the database,
    committing transactions after the specified interval (set
    commit_interval to None to disable)
    """
    session = _get_session(engine, Session, session)

    if commit_interval:
        i = 0

        for vector in source:
            session.add(vector)
            i += 1

            if i == commit_interval:
                session.commit()
                i = 0

            yield vector
    else:
        for vector in source:
            session.add(vector)
            yield vector


@contextmanager
def model_from_file(file_, **model_info):
    """
    Wraps modeldb.files.model_file to return a tuple of (Model,
    file_); the Model object can be used with the vectors generator
    """
    with model_file(file_) as (num_words, vec_length, file1):
        yield Model(num_words=num_words, dim=vec_length, **model_info), file1


def vectors(source,
            model=None,
            encoding=JSON_ENCODING,
            compression=BZ2_COMPRESSION):
    """
    Given a model and a source of (word, values) tuples (see
    modeldb.files.read_model_file), this will generate Vectors for storage
    to a database.
    """
    for (word, vector) in source:
        v = Vector(model=model, word=word)
        v.pack_values(vector, encoding=encoding, compression=compression)
        yield v
