import os
import bz2
import gzip
import tempfile
import sys
import json

from subprocess import Popen, PIPE
from unittest import TestCase
from sqlalchemy import create_engine
from fasttextdb import Base, fasttextdb, main

from .base import FtTestBase, my_dir, ftdb_path


class FileLoadTestCase(FtTestBase):
    def check_model_data(self, check_data, model, actual=None,
                         url='sqlite://'):
        mname = model

        if actual is None:

            with fasttextdb(
                    url,
                    engine=self.engine,
                    Session=self.Session,
                    session=self.session) as ftdb:

                model = ftdb.get_model(mname)

                self.assertEqual(model.name, mname,
                                 'check model name %s' % mname)

                self.assertEqual(model.dim, check_data['model']['dim'],
                                 'check model dim %s' % mname)
                self.assertEqual(model.num_words,
                                 check_data['model']['num_words'],
                                 'check model num words %s' % mname)

                cnt = ftdb.count_vectors_for_model(model)
                self.assertEqual(
                    len(check_data['vectors']), cnt,
                    '%s check word count' % mname)

                vectors = ftdb.get_vectors_for_model(model)
                vectors = {v.word: v.unpack_values() for v in vectors}
                self.assertEqual(check_data['vectors'], vectors,
                                 '%s check vectors' % mname)

        else:
            self.assertEqual(check_data['vectors'], actual,
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

    def test_load_from_cli(self):
        path = self.get_resource_path('test_load.vec.bz2')

        with tempfile.NamedTemporaryFile() as db:
            dbpath = db.name
            url = 'sqlite:///%s' % dbpath
            self.setUp(url)

            args = [
                sys.executable, ftdb_path, '--url', url, 'file', '--input',
                path, '--model', 'test_load_from_cli'
            ]

            popen = Popen(args, stdout=PIPE, stderr=PIPE)
            stdout_data, stderr_data = popen.communicate()

            args = [
                sys.executable, ftdb_path, '--url', url, 'findvectors',
                '--words', '%', '--model', 'test_load_from_cli'
            ]

            popen = Popen(args, stdout=PIPE, stderr=PIPE)
            stdout_data, stderr_data = popen.communicate()
            actual = json.loads(stdout_data)

            with self.open_resource('test_load.vec.bz2') as res:
                with bz2.open(res, 'rt') as vecfile:
                    check_data = self.vect_to_dict(vecfile)
                    actual = {a['word']: a['values'] for a in actual}
                    self.check_model_data(
                        check_data, 'test_load_from_cli', actual=actual)
