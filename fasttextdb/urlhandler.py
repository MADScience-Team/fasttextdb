from .dbservice import DbService
from .webservice import WebService

from urllib.parse import urlparse


def fasttextdb(url,
               name=None,
               config=None,
               engine=None,
               Session=None,
               session=None):
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
