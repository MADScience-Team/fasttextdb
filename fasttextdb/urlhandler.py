from .dbservice import DbService
from .webservice import WebService

from urllib.parse import urlparse


def fasttextdb(url,
               name=None,
               config=None,
               engine=None,
               Session=None,
               session=None):
    """
    Provides the correct type of service based on URL. The name is
    used in logging messages. config is passed as is to the service;
    if no config is provided the library will attempt to load one
    using the default path. The parameters engine, Session and session
    are passed to DbService if the URL specifies a local instance. If
    'http://' or 'https://' schemes are used, a WebService is
    returned. Both types are valid context managers, and should be
    used in a 'with' block. Examples:

    with fasttextdb('http://localhost:8888') as ftdb:
       pass

    with fasttextdb('sqlite://fasttext.db') as ftdb:
       pass

    """
    x = urlparse(url)

    if x.scheme == 'http' or x.scheme == 'https':
        return WebService(url, name=name, config=config)
    else:
        return DbService(
            url,
            name=name,
            config=config,
            engine=engine,
            Session=Session,
            session=session)
