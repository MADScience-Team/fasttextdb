import requests
import yaml

from flask_testing import LiveServerTestCase
from subprocess import Popen, PIPE
from unittest import TestCase
from sqlalchemy import create_engine
from fasttextdb import Base, fasttextdb, main, Model
from fasttextdb.web import api
from fasttextdb.web.app import app, config, run_app
from urllib.parse import urlparse, urlunsplit, urlencode

from .base import FtTestBase, my_dir, ftdb_path


class WebApiTestCase(LiveServerTestCase, FtTestBase):
    def create_app(self):
        self.path, self.url = self.create_temp_db()

        # Load models from YAML file
        with self.open_resource('models.yml') as mfile:
            self.mdat = yaml.load(mfile)
            self.models = {m['name']: m for m in self.mdat['models']}
            session = self.get_session(self.url)

            for m in self.mdat['models']:
                session.add(Model(**m))

            session.commit()

        config['url'] = self.url
        app.config['TESTING'] = True

        config['users'] = {
            'testuser1': {
                'username': 'testuser1',
                'password_hash':
                '$5$rounds=535000$IkNqfgzAuCxI2RHW$v1OxN5O7GJxGmPbmFF62D4/kaDZcq3qDhY081KbqzyD'
            }
        }

        return app

    def get_web_url(self):
        x = urlparse(self.get_server_url())
        return '%s://%s:%s@%s:%s' % (x.scheme, 'testuser1', 'password',
                                     x.hostname, x.port)

    def test_get_model(self):
        with fasttextdb(self.get_web_url()) as ftdb:
            m = ftdb.get_model('model_1')
            self.assertEqual(m['name'], 'model_1')
