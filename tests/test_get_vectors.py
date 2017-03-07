import os
import bz2
import gzip
import random

from unittest import TestCase
from sqlalchemy import create_engine
from fasttextdb import Base, fasttextdb

from .base import FtTestBase


class GetVectorsTestCase(FtTestBase):
    def setUp(self):
        super().setUp()
        self.load_vectors('test_load.vec.bz2', 'test_load_bz2_sqlite')
        self.load_vectors('test_load.vec.gz', 'test_load_gzip_sqlite')
        self.check_data = {}

        with self.open_resource('test_load.vec.bz2') as res:
            with bz2.open(res, 'rt') as vecfile:
                self.check_data['test_load_bz2_sqlite'] = self.vect_to_dict(
                    vecfile)

        with self.open_resource('test_load.vec.gz') as res:
            with gzip.open(res, 'rt') as vecfile:
                self.check_data['test_load_gzip_sqlite'] = self.vect_to_dict(
                    vecfile)

    def check_vectors(self, model):
        with fasttextdb(
                'sqlite://',
                engine=self.engine,
                Session=self.Session,
                session=self.session) as ftdb:

            words = random.choices(
                list(self.check_data[model]['vectors'].keys()), k=50)

            vectors = ftdb.get_vectors_for_words(model, words)

            exp = {w: self.check_data[model]['vectors'][w] for w in words}

            act = {v.word: v.unpack_values() for v in vectors}

            self.assertEqual(exp, act, 'checked vectors for %s' % model)

    def test_get_vectors_1(self):
        self.check_vectors('test_load_bz2_sqlite')

    def test_get_vectors_2(self):
        self.check_vectors('test_load_gzip_sqlite')
