import argparse


def get_parser(description):
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('--config-path', help='path to YAML config file')

    parser.add_argument('--secret', help='secret key for sessions')

    parser.add_argument(
        '--host', help='hostname for requests/web service listener')

    parser.add_argument(
        '--port', help='port for requests/web service listener')

    parser.add_argument(
        '--debug', action='store_true', help='enable debug features')

    parser.add_argument('--username', help='username for API')

    parser.add_argument('--password', help='password for API')

    return parser
