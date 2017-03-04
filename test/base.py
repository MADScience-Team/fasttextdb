import os

from unittest import TestCase
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fasttextdb import Base, fasttextdb

_dir = os.path.dirname(__file__)
_resource_dir = os.path.join(_dir, 'resources')


class FtTestBase(TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def load_vectors(self, path, model):
        with self.open_resource(path) as res:
            with fasttextdb(
                    'sqlite://',
                    engine=self.engine,
                    Session=self.Session,
                    session=self.session) as ftdb:
                ftdb.commit_file(model, res, False)

    def tearDown(self):
        pass

    @contextmanager
    def open_resource(self, path, mode='rb'):
        with open(os.path.join(_resource_dir, path), mode) as f:
            yield f
