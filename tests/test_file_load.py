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
    def _test_load_sqlite(self, model, path):
        with self.temp_db() as url:
            with fasttextdb(url) as ftdb, self.open_resource(path) as vecfile:
                ftdb.commit_file(model, vecfile)

            with self.open_resource(path) as vecfile:
                exp_model = self.read_model(vecfile)
                exp_vectors = self.read_vectors(vecfile)

            act_model = self.query_model(url, model)
            act_vectors = self.query_vectors(url)
            self.compare_model(exp_model, act_model, '%s model' % model)
            self.compare_model(exp_vectors, act_vectors, '%s vectors' % model)

    def test_load_bz2_sqlite(self):
        self._test_load_sqlite('test_load_bz2_sqlite', 'test_load.vec.bz2')

    def test_load_gzip_sqlite(self):
        self._test_load_sqlite('test_load_gz_sqlite', 'test_load.vec.gz')

    def test_load_cli_sqlite(self):
        model = 'test_load_cli_sqlite'
        path = 'test_load.vec.bz2'

        with self.temp_db() as url, self.open_resource(path) as vecfile:
            args = [
                sys.executable, ftdb_path, '--url', url, 'file', '--input',
                self.get_resource_path(path), '--model', model
            ]

            popen = Popen(args, stdout=PIPE, stderr=PIPE)
            stdout_data, stderr_data = popen.communicate()

            with self.open_resource(path) as vecfile:
                exp_model = self.read_model(vecfile)
                exp_vectors = self.read_vectors(vecfile)

            act_model = self.query_model(url, model)
            act_vectors = self.query_vectors(url)
            #            self.compare_model(exp_model, act_model, '%s model' % model)
            self.compare_model(exp_vectors, act_vectors, '%s vectors' % model)
