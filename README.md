<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->

**Table of Contents**

- [Description](#description)
- [Requirements](#requirements)
- [Makefile](#makefile)
- [Installation](#installation)
- [Command-line access](#command-line-access)
    - [Database Initialization](#database-initialization)
- [Configuration Files](#configuration-files)

<!-- markdown-toc end -->

# Description

# Requirements

**Currently this project requires Python 3**, but I do hope to
eventually back-port it to Python 2. One dependency is in the Python 3
version of the bzip package, which allows for the use of a file stream
as input, rather than requiring a path to the file.

This project has several dependencies on several Python libraries,
listed in `requirements.txt`. Notable ones include:

- SQLAlchemy
- Flask
- Flask-Login
- passlib
- python-magic
- PyYAML
- requests
- progressbar2

# Makefile

A Makefile is available to help with certain operations, including
grabbing NPM dependencies, running tests and cleanup. Variables are
available for customization, including:

- `PYTHON`: path to `python` executable
- `VIRTUALENV`: path to `virtualenv` executable
- `VENV_DIR`: path to a Python virtual environment (`venv` by default)
- `PIP`: path to `pip` executable
- `NPM`: path to `npm` executable

The following rules are available:

- `all`: (default rule) builds the project
- `test`: runs Python tests
- `install`: installs the package using pip
- `virtualenv`: creates a Python virtual environment suitable for 
running this package
- `clean`: removes compiled Python, cache directories

# Installation

This package uses setuptools to install. Simply run:

```
python setup.py install
```

or

```
pip install .
```

or possibly

```
make install
```

from the checkout directory.

If you wish to use `virtualenv`, you can do:

```
virtualenv venv
venv/bin/pip install -r requirements.txt
venv/bin/pip install .
```

or

```
make virtualenv
make install PIP=venv/bin/pip
```

# Command-line access

Once installed, use the `ftdb` script to access a database by its URL,
either local or remote. Legal schemes are `http` and `https` (remote)
and any database scheme supported by the SQLAlchemy package, for
example `sqlite`. Here are some example URLs:

```
ftdb --url http://localhost:8888
ftdb --url sqlite:///fasttext.db
```

Run `ftdb -h` to get a full list of subcommands and options.

## Database Initialization

Run `ftdb initialize` to create a database with the required
schema. Use the `--url` switch to specify the database connection
string. Only databse URLs are supported for initialize, not `http` or
`https` schemes.

```
ftdb --url sqlite:///fasttext.db initialize
```

# Configuration Files

This packages will attempt to load a YAML configuration file by
looking in the following locations (in order):

* `./fasttextdb.yml`
* `./config.yml`
* `~/.fasttextdb.yml`
* `/etc/fasttextdb/config.yml`
* `/etc/fasttextdb.yml`

For a server instance, the `url` configuration key determines the
local database where the web application will store its data.

Many of the configuration keys have a corresponding command line
argument that can be used to override the configuration value.
