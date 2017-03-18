import argparse
import logging
import sys
import json

from sqlalchemy import create_engine

from .models import *
from .files import *
from .vectors import *
from .config import *
from .service import *
from .urlhandler import *


def get_parser(description):
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('--config-path', help='path to YAML config file')

    parser.add_argument('--secret', help='secret key for sessions')

    parser.add_argument('--url', help='url for local/remote FastTextDB')

    parser.add_argument(
        '--debug', action='store_true', help='enable debug features')

    parser.add_argument(
        '--progress', action='store_true', help='show progress of transfers')
    parser.add_argument(
        '--camel',
        action='store_true',
        help='retrieve JSON keys as camel case')
    parser.add_argument(
        '-o',
        help="file to write JSON output to",
        type=argparse.FileType("wb"),
        default=sys.stdout)

    subparsers = parser.add_subparsers(help='sub-command help')

    initialize_parser = subparsers.add_parser(
        'initialize', help='initialize FastTextDB (local only)')
    initialize_parser.set_defaults(func=initialize_subcommand)

    file_parser = subparsers.add_parser(
        'file', help='commit files to FastTextDB')
    file_parser.set_defaults(func=file_subcommand)

    file_parser.add_argument(
        '--input', help='input file to commit', type=argparse.FileType('rb'))

    file_parser.add_argument(
        '--model',
        help='model ID or name (if not specified will try to guess based on the file header)'
    )

    update_parser = subparsers.add_parser(
        'update', help='update model parameters')
    update_parser.set_defaults(func=update_model)
    update_parser.add_argument(
        '--model', help="model ID or name will be created if it doesn't exist")
    update_parser.add_argument('--owner', help="owner (username)")
    update_parser.add_argument('--name', help="model name")
    update_parser.add_argument('--description', help="model description")
    update_parser.add_argument(
        '--num-words', help="number of words in model", type=int)
    update_parser.add_argument(
        '--dim',
        help="number of dimensions (size of vector, e.g 100)",
        type=int)
    update_parser.add_argument('--input-file', help="input file name")
    update_parser.add_argument('--output', help="output file name")
    update_parser.add_argument(
        '--lr', help="learning rate, e.g. 0.05", type=float)
    update_parser.add_argument(
        '--lr-update-rate', help="change in learning rate, e.g. 100", type=int)
    update_parser.add_argument(
        '--ws', help="context window size, e.g. 5", type=int)
    update_parser.add_argument(
        '--epoch', help="number of epochs, e.g. 5", type=int)
    update_parser.add_argument(
        '--min-count', help="min number of word occurrences, e.g. 5", type=int)
    update_parser.add_argument(
        '--neg', help="number of negatives sampled, e.g. 5", type=int)
    update_parser.add_argument(
        '--ngrams', help="max word ngram length, e.g. 1", type=int)
    update_parser.add_argument(
        '--loss', help="loss function", choices=('ns', 'hs', 'softmax'))
    update_parser.add_argument(
        '--bucket', help="# buckets, e.g. 2000000", type=int)
    update_parser.add_argument(
        '--minn', help="min character ngram length, e.g. 3", type=int)
    update_parser.add_argument(
        '--maxn', help="max character ngram length, e.g. 6", type=int)
    update_parser.add_argument(
        '--thread', help="number of threads, e.g. 12", type=int)
    update_parser.add_argument(
        '-t', help="sampling threshold, e.g. 0.0001", type=float)

    find_model_parser = subparsers.add_parser(
        'findmodels', help='find models matching specified parameters')
    find_model_parser.set_defaults(func=find_model)
    find_model_parser.add_argument(
        '--model', help="model ID or name will be created if it doesn't exist")
    find_model_parser.add_argument('--owner', help="owner (username)")
    find_model_parser.add_argument('--name', help="model name")
    find_model_parser.add_argument('--description', help="model description")
    find_model_parser.add_argument(
        '--num-words', help="number of words in model", type=int, nargs='+')
    find_model_parser.add_argument(
        '--dim',
        help="number of dimensions (size of vector, e.g 100)",
        type=int,
        nargs='+')
    find_model_parser.add_argument('--input-file', help="input file name")
    find_model_parser.add_argument('--output', help="output file name")
    find_model_parser.add_argument(
        '--lr', help="learning rate, e.g. 0.05", type=float, nargs='+')
    find_model_parser.add_argument(
        '--lr-update-rate',
        help="change in learning rate, e.g. 100",
        type=int,
        nargs='+')
    find_model_parser.add_argument(
        '--ws', help="context window size, e.g. 5", type=int, nargs='+')
    find_model_parser.add_argument(
        '--epoch', help="number of epochs, e.g. 5", type=int, nargs='+')
    find_model_parser.add_argument(
        '--min-count',
        help="min number of word occurrences, e.g. 5",
        type=int,
        nargs='+')
    find_model_parser.add_argument(
        '--neg',
        help="number of negatives sampled, e.g. 5",
        type=int,
        nargs='+')
    find_model_parser.add_argument(
        '--ngrams', help="max word ngram length, e.g. 1", type=int, nargs='+')
    find_model_parser.add_argument(
        '--loss',
        help="loss function",
        choices=('ns', 'hs', 'softmax'),
        nargs='+')
    find_model_parser.add_argument(
        '--bucket', help="# buckets, e.g. 2000000", type=int, nargs='+')
    find_model_parser.add_argument(
        '--minn',
        help="min character ngram length, e.g. 3",
        type=int,
        nargs='+')
    find_model_parser.add_argument(
        '--maxn',
        help="max character ngram length, e.g. 6",
        type=int,
        nargs='+')
    find_model_parser.add_argument(
        '--thread', help="number of threads, e.g. 12", type=int, nargs='+')
    find_model_parser.add_argument(
        '-t', help="sampling threshold, e.g. 0.0001", type=float, nargs='+')

    find_vectors_parser = subparsers.add_parser(
        'findvectors', help='find vectors matching specified parameters')
    find_vectors_parser.set_defaults(func=find_vectors)
    find_vectors_parser.add_argument('--model', help="model ID or name")
    find_vectors_parser.add_argument(
        '--words',
        help="matching words to retrieve (% is wildcard)",
        nargs='+')
    find_vectors_parser.add_argument(
        '--packed',
        help="retrieve values as packed binary blob",
        action='store_true')
    find_vectors_parser.add_argument(
        '--include-model',
        help="include model info with vectors",
        action='store_true')
    find_vectors_parser.add_argument(
        '--include-model-id',
        help="include model ID with vectors",
        action='store_true')

    return parser


def initialize_subcommand(args):
    config = load_config(args=args)
    engine = create_engine(config['url'])
    logger = logging.getLogger('fasttextdb.initialize')
    logger.info('initializing database')
    Base.metadata.create_all(engine)
    logger.info('initialization complete')


def file_subcommand(args):
    config = load_config(args=args)
    logger = logging.getLogger('fasttextdb.file')
    logger.info('connecting to database')
    with fasttextdb(config['url'], config=config) as ftdb:
        ftdb.commit_file(args.model, args.input, config['progress'])


def update_model(args):
    config = load_config(args=args)
    logger = logging.getLogger('fasttextdb.model')
    logger.info('connecting to database')

    with fasttextdb(config['url'], config=config) as ftdb:
        model = ftdb.update_model(
            args.model,
            owner=args.owner,
            name=args.name,
            description=args.description,
            num_words=args.num_words,
            dim=args.dim,
            input_file=args.input_file,
            output=args.output,
            lr=args.lr,
            lr_update_rate=args.lr_update_rate,
            ws=args.ws,
            epoch=args.epoch,
            min_count=args.min_count,
            neg=args.neg,
            word_ngrams=args.ngrams,
            loss=args.loss,
            bucket=args.bucket,
            minn=args.minn,
            maxn=args.maxn,
            thread=args.thread,
            t=args.t)

        model = model.to_dict()

        for k in model:
            logger.info('updated model %s: %s' % (k, model[k]))


def find_model(args):
    config = load_config(args=args)
    logger = logging.getLogger('fasttextdb.model')
    logger.info('connecting to database %s' % config['url'])

    with fasttextdb(config['url'], config=config) as ftdb:
        models = ftdb.find_models(
            owner=args.owner,
            name=args.name,
            description=args.description,
            num_words=args.num_words,
            dim=args.dim,
            input_file=args.input_file,
            output=args.output,
            lr=args.lr,
            lr_update_rate=args.lr_update_rate,
            ws=args.ws,
            epoch=args.epoch,
            min_count=args.min_count,
            neg=args.neg,
            word_ngrams=args.ngrams,
            loss=args.loss,
            bucket=args.bucket,
            minn=args.minn,
            maxn=args.maxn,
            thread=args.thread,
            t=args.t)

        models = [m.to_dict() for m in models]
        logger.info('%s model(s) found' % len(models))
        args.o.write(json.dumps(models, indent=3))


def find_vectors(args):
    config = load_config(args=args)
    logger = logging.getLogger('fasttextdb.vectors')
    logger.info('connecting to database %s' % config['url'])

    with fasttextdb(config['url'], config=config) as ftdb:
        vectors = ftdb.get_vectors_for_words(args.model, args.words)

        vectors = [
            v.to_dict(
                camel=args.camel,
                include_model=args.include_model,
                include_model_id=args.include_model_id,
                packed=args.packed) for v in vectors
        ]

        logger.info('%s vector(s) found' % len(vectors))

        if args.o in [sys.stdout, sys.stderr]:
            x = json.dumps(vectors, indent=3)
        else:
            x = json.dumps(vectors, indent=3).encode()
            logger.info('writing output to %s' % args.output.name)

        args.o.write(x)


def main(args=None):
    parser = get_parser('access and manipulate FastTextDB instances')

    if args is None:
        args = parser.parse_args()
    else:
        args = parser.parse_args(args)

    if hasattr(args, 'func'):
        args.func(args)


if __name__ == '__main__':
    main()
