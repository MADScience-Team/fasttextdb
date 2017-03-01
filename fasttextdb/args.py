import argparse
import logging

from sqlalchemy import create_engine

from .config import load_config
from .models import Base
from .service import *


def get_parser(description):
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('--config-path', help='path to YAML config file')

    parser.add_argument('--secret', help='secret key for sessions')

    parser.add_argument('--url', help='url for local/remote FastTextDB')

    parser.add_argument(
        '--debug', action='store_true', help='enable debug features')

    parser.add_argument(
        '--progress', action='store_true', help='show progress of transfers')

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
    update_parser.add_argument('--output-file', help="output file name")
    update_parser.add_argument(
        '--learning-rate', help="learning rate, e.g. 0.05", type=float)
    update_parser.add_argument(
        '--learning-rate-update-rate-change',
        help="change in learning rate, e.g. 100",
        type=int)
    update_parser.add_argument(
        '--window-size', help="context window size, e.g. 5", type=int)
    update_parser.add_argument(
        '--epoch', help="number of epochs, e.g. 5", type=int)
    update_parser.add_argument(
        '--min-count', help="min number of word occurrences, e.g. 5", type=int)
    update_parser.add_argument(
        '--negatives', help="number of negatives sampled, e.g. 5", type=int)
    update_parser.add_argument(
        '--ngrams', help="max word ngram length, e.g. 1", type=int)
    update_parser.add_argument(
        '--loss-function',
        help="loss function",
        choices=('ns', 'hs', 'softmax'))
    update_parser.add_argument(
        '--buckets', help="# buckets, e.g. 2000000", type=int)
    update_parser.add_argument(
        '--min-ngram', help="min character ngram length, e.g. 3", type=int)
    update_parser.add_argument(
        '--max-ngram', help="max character ngram length, e.g. 6", type=int)
    update_parser.add_argument(
        '--threads', help="number of threads, e.g. 12", type=int)
    update_parser.add_argument(
        '--threshold', help="sampling threshold, e.g. 0.0001", type=float)

    return parser


def initialize_subcommand(args):
    config = load_config(args=args)
    engine = create_engine(config['url'])
    logger = logging.getLogger('fasttextdb.initialize')
    logger.info('initializing database')
    Base.metadata.create_all(engine)


def file_subcommand(args):
    config = load_config(args=args)
    logger = logging.getLogger('fasttextdb.file')
    logger.info('connecting to database')
    with fasttextdb(config['url'], config) as ftdb:
        ftdb.commit_file(args.model, args.input, config['progress'])


def update_model(args):
    config = load_config(args=args)
    logger = logging.getLogger('fasttextdb.model')
    logger.info('connecting to database')

    with fasttextdb(config['url'], config) as ftdb:
        model = ftdb.update_model(
            args.model,
            owner=args.owner,
            name=args.name,
            description=args.description,
            num_words=args.num_words,
            dim=args.dim,
            input_file=args.input_file,
            output_file=args.output_file,
            learning_rate=args.learning_rate,
            learning_rate_update_rate_change=args.
            learning_rate_update_rate_change,
            window_size=args.window_size,
            epoch=args.epoch,
            min_count=args.min_count,
            negatives_sampled=args.negatives,
            word_ngrams=args.ngrams,
            loss_function=args.loss_function,
            num_buckets=args.buckets,
            min_ngram_len=args.min_ngram,
            max_ngram_len=args.max_ngram,
            num_threads=args.threads,
            sampling_threshold=args.threshold)

        model = model.to_dict()

        for k in model:
            logger.info('updated model %s: %s' % (k, model[k]))
