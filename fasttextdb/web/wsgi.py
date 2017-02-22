import os

from .app import app as application
from .pages import *
from .api import *

if __name__ == "__main__":
    application.run()
