import os
import bz2
import gzip
import json
import random
import tempfile
import sys
import yaml

from unittest import TestCase
from sqlalchemy import create_engine
from fasttextdb import Base, fasttextdb, Model, Vector
from subprocess import Popen, PIPE

from .base import FtTestBase, ftdb_path


class QueryModelsTestCase(FtTestBase):
    def setUp(self):
        self.path, self.url = self.create_temp_db()

        # Load models from YAML file
        with self.open_resource('models.yml') as mfile:
            self.mdat = yaml.load(mfile)
            self.models = {m['name']: m for m in self.mdat['models']}
            session = self.get_session(self.url)

            for m in self.mdat['models']:
                session.add(Model(**m))

            session.commit()

    def tearDown(self):
        self.remove_temp_db(self.path)

    def check(self, prefix, exp_models, act_models):
        self.assertEqual(
            len(act_models), len(exp_models), '%s num models' % prefix)

        for m in exp_models:
            self.assertEqual(
                len(act_models[m]),
                len(exp_models[m]), '%s num model keys %s' % (prefix, m))
            for k in exp_models[m]:
                self.assertEqual(act_models[m][k], exp_models[m][k],
                                 '%s returned model %s %s' % (prefix, m, k))

    def test_api_model_query(self):
        with fasttextdb(self.url) as ftdb:
            for q in self.mdat['queries']:
                query = self.mdat['queries'][q]['query']
                exp_models = self.mdat['queries'][q]['expected'] or []
                exp_models = {m: self.models[m] for m in exp_models}
                act_models = list(ftdb.find_models(**query))
                act_models = {m.name: m.to_dict() for m in act_models}
                self.check('api', exp_models, act_models)

    def test_cli_model_query(self):
        for q in self.mdat['queries']:
            query = self.mdat['queries'][q]['query']
            exp_models = self.mdat['queries'][q]['expected'] or []
            exp_models = {m: self.models[m] for m in exp_models}

            args = [sys.executable, ftdb_path, '--url', self.url, 'findmodels']

            for k in query:
                if len(k) == 1:
                    args.append('-%s' % k)
                else:
                    args.append('--%s' % k)

                if type(query[k]) is list:
                    for x in query[k]:
                        args.append('%s' % x)
                else:
                    args.append('%s' % query[k])

            popen = Popen(args, stdout=PIPE, stderr=PIPE)
            stdout_data, stderr_data = popen.communicate()

            try:
                self.assertEqual(popen.returncode, 0, 'returns status 0')
            except:
                for l in stderr_data.decode('utf-8').split('\n'):
                    print('stderr: %s' % l)
                raise

            act_models = json.loads(stdout_data)
            act_models = {m['name']: m for m in act_models}
            self.check('cli', exp_models, act_models)
