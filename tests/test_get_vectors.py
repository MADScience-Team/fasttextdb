import os
import bz2
import gzip
import json
import random
import tempfile
import sys

from unittest import TestCase
from sqlalchemy import create_engine
from fasttextdb import Base, fasttextdb, Model, Vector
from subprocess import Popen, PIPE

from .base import FtTestBase, ftdb_path


class GetVectorsTestCase(FtTestBase):
    def random_words(self, words):
        return random.choices(words, k=50)

    def _get_exp_vectors(self, path):
        with self.open_resource(path) as vecfile:
            exp_model = self.read_model(vecfile)
            exp_vectors = self.read_vectors(vecfile)

        words = self.random_words(list(exp_vectors.keys()))

        exp_vectors = {e: exp_vectors[e] for e in exp_vectors if e in words}

        return words, exp_vectors

    def _test_get_vectors(self, model, path):
        with self.temp_db() as url:
            self.load_vectors(url, model, path)

            words, exp_vectors = self._get_exp_vectors(path)

            with fasttextdb(url) as ftdb:
                act_vectors = ftdb.get_vectors_for_words(model, words)
                act_vectors = {v['word']: v['values'] for v in act_vectors}

            self.compare_vectors(exp_vectors, act_vectors,
                                 'get_vectors %s' % model)

    def test_get_vectors_1(self):
        self._test_get_vectors('test_load_bz2_sqlite', 'test_load.vec.bz2')

    def test_get_vectors_2(self):
        self._test_get_vectors('test_load_gz_sqlite', 'test_load.vec.gz')

    def test_get_vectors_from_cli(self):
        model = 'test_load_cli_sqlite'
        path = 'test_load.vec.bz2'

        with self.temp_db() as url:
            self.load_vectors(url, model, path)
            words, exp_vectors = self._get_exp_vectors(path)

            args = [
                sys.executable, ftdb_path, '--url', url, 'findvectors',
                '--words'
            ] + words + ['--model', 'test_load_cli_sqlite']

            popen = Popen(args, stdout=PIPE, stderr=PIPE)
            stdout_data, stderr_data = popen.communicate()
            act_vectors = self.json_to_vectors(stdout_data)

            self.compare_vectors(exp_vectors, act_vectors,
                                 'get_vectors %s' % model)
