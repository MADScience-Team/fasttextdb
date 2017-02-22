import requests

from argparse import FileType
from fasttextdb import get_parser, load_config, FasttextApi, open_for_mime_type, model_from_file, vectors, read_file

parser = get_parser('upload a vectors file to the web API')

parser.add_argument('--upload', help='path to vectors file for uploading')
parser.add_argument('--model-name', help='model name')
parser.add_argument('--model-id', help='model ID')
parser.add_argument('--json', action='store_true', help='send vectors as JSON')

args = parser.parse_args()
config = load_config(args=args)
api = FasttextApi(config=config)

with open(args.upload, 'rb') as file:
    if args.json:
        file = open_for_mime_type(file)

        with model_from_file(file) as (m, file1):
            buff = []

            for word, values in read_file(file1):
                buff.append({'word': word, 'values': values})

                if len(buff) >= 1000:
                    print(api.create_vectors(
                        buff, id=args.model_id, name=args.model_name))
                    buff = []

            if len(buff) > 0:
                print(api.create_vectors(
                    buff, id=args.model_id, name=args.model_name))
    else:
        if args.model_name:
            print(api.upload_file(file, name=args.model_name))
        else:
            print(api.upload_file(file, id=args.model_id))
