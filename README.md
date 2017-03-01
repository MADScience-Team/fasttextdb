# Description

# Installation

This package uses setuptools to install. Simply run:

```
python setup.py install
```

or

```
pip install .
```

from the checkout directory.

If you wish to use `virtualenv`, you can do:

```
virtualenv venv
venv/bin/pip install -r requirements.txt
venv/bin/pip install .
```

# Command-line access

Once installed, use the `ftdb` script to access a database by its URL,
either local or remote. Legal schemes are `http` and `https` (remote)
and any database scheme supported by the SQLAlchemy package, for
example `sqlite`. Here are some example URLs:

```
ftdb --url http://localhost:8888
ftdb --url sqlite:///myfastext.db
```

Run `ftdb -h` to get a full list of subcommands and options.
