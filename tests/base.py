import os

from unittest import TestCase
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fasttextdb import Base, fasttextdb

my_dir = os.path.dirname(__file__)
ftdb_path = os.path.join(my_dir, os.pardir, 'scripts', 'ftdb')
_resource_dir = os.path.join(my_dir, 'resources')


class FtTestBase(TestCase):
    def setUp(self, url=None):
        if url is None:
            url = 'sqlite://'

        self.engine = create_engine(url)
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
        with open(self.get_resource_path(path), mode) as f:
            yield f

    def get_resource_path(self, path):
        return os.path.join(_resource_dir, path)

    def vect_to_dict(self, file):
        dat = {'model': {}, 'vectors': {}}
        l = file.readline()
        parts = l.split()
        dat['model']['num_words'] = int(parts[0])
        dat['model']['dim'] = int(parts[1])
        l = file.readline()

        while l:
            parts = l.split()
            dat['vectors'][parts[0]] = [float(x) for x in parts[1:]]
            l = file.readline()

        return dat
