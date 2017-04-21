import os
import gzip
import bz2
import json

from tempfile import NamedTemporaryFile, mkstemp
from unittest import TestCase
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fasttextdb import Base, fasttextdb, Model, Vector
from fasttextdb.vectors import *

my_dir = os.path.dirname(__file__)
ftdb_path = os.path.join(my_dir, os.pardir, 'scripts', 'ftdb')
_resource_dir = os.path.join(my_dir, 'resources')


class FtTestBase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def load_vectors(self, url, model, path):
        with self.open_resource(path) as res:
            session = self.get_session(url)
            model = Model(name=model, **self.read_model(res))
            vectors = self.read_vectors(res)

            for word in vectors:
                v = Vector(word=word)
                v.packed_values = pack_values(vectors[word])
                v.model = model
                session.add(v)

            session.commit()

    @contextmanager
    def open_resource(self, path, mode='rt'):
        path = self.get_resource_path(path)

        if path.endswith('.gz'):
            with gzip.open(path, mode) as f:
                yield f
        elif path.endswith('.bz2'):
            with bz2.open(path, mode) as f:
                yield f
        else:
            with open(self.get_resource_path(path), mode) as f:
                yield f

    @contextmanager
    def temp_db(self):
        with NamedTemporaryFile() as db:
            url = 'sqlite:///%s' % db.name
            self.prepare_db(url)
            yield url

    def create_temp_db(self):
        (temp_db_file, temp_db_path) = mkstemp()
        url = 'sqlite:///%s' % temp_db_path
        self.prepare_db(url)
        return temp_db_path, url

    def remove_temp_db(self, path):
        os.remove(path)

    def prepare_db(self, url='sqlite://'):
        engine = create_engine(url)
        Base.metadata.create_all(engine)

    def get_session(self, url):
        engine = create_engine(url)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session()

    def get_resource_path(self, path):
        return os.path.join(_resource_dir, path)

    def read_model(self, file):
        l = file.readline()
        parts = l.split()
        return {'num_words': int(parts[0]), 'dim': int(parts[1])}

    def _vectors(self, file, words=None):
        l = file.readline()

        while l:
            parts = l.split()

            if words is None or parts[0] in words:
                yield parts[0], [float(x) for x in parts[1:]]

            l = file.readline()

    def read_vectors(self, file, words=None):
        return {v[0]: v[1] for v in self._vectors(file, words)}

    def query_model(self, url, model):
        session = self.get_session(url)
        return session.query(Model).get(model).to_dict()

    def query_vectors(self, url, words=None):
        session = self.get_session(url)

        if words is None:
            vectors = session.query(Vector)
        else:
            vectors = session.query(Vector).filter(Vector.word.in_(words))

        return {v.word: unpack_values(v.packed_values) for v in vectors}

    def json_to_model(self, model):
        model = json.loads(model)
        return Model(**model)

    def json_to_vectors(self, vectors):
        vectors = json.loads(vectors)
        return {v['word']: v['values'] for v in vectors}

    def compare_model(self, exp, act, msg):
        for k in exp:
            self.assertTrue(k in act, '%s: %s not in actual model' % (msg, k))
            self.assertEqual(exp[k], act[k],
                             '%s: model mismatch property %s' % (msg, k))

    def compare_vectors(self, exp, act, msg):
        self.assertEqual(len(exp), len(act), msg)

        for k in exp:
            self.assertTrue(k in act, '%s: %s not in actual' % (msg, k))
            self.assertEqual(exp[k], act[k],
                             '%s: %s vector mismatch' % (msg, k))
