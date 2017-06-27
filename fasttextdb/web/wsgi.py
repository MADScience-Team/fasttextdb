import os

from .app import app as application
from .pages import *
from .api import *

# Do this to make it easier to run Flask app from command line with
# the "flask" command
app = application

if __name__ == "__main__":
    application.run()
