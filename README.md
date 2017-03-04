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

* ./fasttextdb.yml
* ./config.yml
* ~/.fasttextdb.yml
* /etc/fasttextdb/config.yml
* /etc/fasttextdb.yml

For a server instance, the `url` configuration key determines the
local database where the web application will store its data.

Many of the configuration keys have a corresponding command line
argument that can be used to override the configuration value.
