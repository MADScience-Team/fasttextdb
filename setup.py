import os
import os.path
from setuptools import setup

setup(
    name="fasttextdb",
    version="0.0.2",
    author="Jason Veiga",
    author_email="jasonveiga@me.com",
    description="Python package, scripts and webapp for managing FastText model data",
    scripts=['scripts/ftdb'],
    license="?",
    install_requires=[
        'flask', 'sqlalchemy', 'six', 'pyyaml', 'requests', 'progressbar2',
        'passlib', 'python-magic'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.4',
    ],
    keywords="FastText model database",
    url="http://packages.python.org/an_example_pypi_project",
    packages=['fasttextdb'])
