#!/bin/sh

if [ "$1" == "" ] ; then
    venv=$(realpath ./venv)
else
    venv=$(realpath $1)
fi

${venv}/bin/uwsgi \
    --virtualenv $venv \
    --module modeldb.wsgi \
    --py-autoreload 1 \
    --http-socket 127.0.0.1:8888
