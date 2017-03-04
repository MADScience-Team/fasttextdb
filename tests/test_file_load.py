import os
import bz2
import gzip

from unittest import TestCase
from sqlalchemy import create_engine
from fasttextdb import Base, fasttextdb

from .base import FtTestBase


class FileLoadTestCase(FtTestBase):
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

    def check_model_data(self, check_data, model):
        mname = model

        with fasttextdb(
                'sqlite://',
                engine=self.engine,
                Session=self.Session,
                session=self.session) as ftdb:

            model = ftdb.get_model(mname)

            self.assertEqual(model.name, mname, 'check model name %s' % mname)

            self.assertEqual(model.dim, check_data['model']['dim'],
                             'check model dim %s' % mname)
            self.assertEqual(model.num_words, check_data['model']['num_words'],
                             'check model num words %s' % mname)

            cnt = ftdb.count_vectors_for_model(model)
            self.assertEqual(
                len(check_data['vectors']), cnt, '%s check word count' % mname)

            vectors = ftdb.get_vectors_for_model(model)
            vectors = {v.word: v.unpack_values() for v in vectors}
            self.assertEqual(check_data['vectors'], vectors,
                             '%s check vectors' % mname)

    def test_load_bz2_sqlite(self):
        self.load_vectors('test_load.vec.bz2', 'test_load_bz2_sqlite')

        with self.open_resource('test_load.vec.bz2') as res:
            with bz2.open(res, 'rt') as vecfile:
                check_data = self.vect_to_dict(vecfile)
                self.check_model_data(check_data, 'test_load_bz2_sqlite')

    def test_load_gzip_sqlite(self):
        self.load_vectors('test_load.vec.gz', 'test_load_gzip_sqlite')

        with self.open_resource('test_load.vec.gz') as res:
            with gzip.open(res, 'rt') as vecfile:
                check_data = self.vect_to_dict(vecfile)
                self.check_model_data(check_data, 'test_load_gzip_sqlite')
