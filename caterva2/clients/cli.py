###############################################################################
# Caterva2 - On demand access to remote Blosc2 data repositories
#
# Copyright (c) 2023 The Blosc Developers <blosc@blosc.org>
# https://www.blosc.org
# License: GNU Affero General Public License v3.0
# See LICENSE.txt for details about copyright and rights to use.
###############################################################################

import json
import pathlib
import re

# Requirements
import httpx
import rich
import tqdm

# Project
from caterva2 import api_utils
from caterva2.clients import cli_utils


def handle_errors(func):
    def wrapper(*args):
        try:
            func(*args)
        except httpx.HTTPStatusError as error:
            response = error.response
            try:
                error = response.json()['detail']
            except json.decoder.JSONDecodeError:
                error = response.text
            print('Error:', error)

    return wrapper

def dataset_with_slice(dataset):
    match = re.match('(.*)\\[(.*)]', dataset)
    if match is None:
        params = {}
    else:
        dataset, slice = match.groups()
        params = {'slice': slice}

    return pathlib.Path(dataset), params

def url_with_slice(url, slice):
    if slice is not None:
        return f'{url}?slice={args.slice}'
    return url

def chunk_dl_progress(it):
    return tqdm.tqdm(it, desc='Downloading', unit='chunk')

@handle_errors
def cmd_roots(args):
    data = api_utils.get(f'http://{args.host}/api/roots')
    if args.json:
        print(json.dumps(data))
        return

    for name, root in data.items():
        if root['subscribed'] is True:
            print(f'{name} (subscribed)')
        else:
            print(name)

@handle_errors
def cmd_subscribe(args):
    data = api_utils.post(f'http://{args.host}/api/subscribe/{args.root}')
    if args.json:
        print(json.dumps(data))
        return

    print(data)

@handle_errors
def cmd_list(args):
    data = api_utils.get(f'http://{args.host}/api/list/{args.root}')
    if args.json:
        print(json.dumps(data))
        return

    for item in data:
        print(f'{args.root}/{item}')

@handle_errors
def cmd_url(args):
    data = api_utils.get(f'http://{args.host}/api/url/{args.root}')
    if args.json:
        print(json.dumps(data))
        return

    for url in data:
        print(url)

@handle_errors
def cmd_info(args):
    # Get
    dataset, params = args.dataset
    data = api_utils.get(f'http://{args.host}/api/info/{dataset}', params=params)

    # Print
    if args.json:
        print(json.dumps(data))
        return

    rich.print(data)


@handle_errors
def cmd_show(args):
    dataset, params = args.dataset
    data = api_utils.download(args.host, dataset, params)
                              # TODO: support tqdm again
                              # progress=chunk_dl_progress)

    # Display
    if isinstance(data, bytes):
        try:
            print(data.decode())
        except UnicodeDecodeError:
            print('Binary data')
    else:
        print(data)

@handle_errors
def cmd_download(args):
    dataset, params = args.dataset
    params['download'] = True
    path = api_utils.download(args.host, dataset, params)
                              # TODO: support tqdm again
                              # progress=chunk_dl_progress)

    print(f'Dataset saved to {path}')


if __name__ == '__main__':
    parser = cli_utils.get_parser()
    parser.add_argument('--host', default='localhost:8002')
    subparsers = parser.add_subparsers(required=True)

    # roots
    help = 'List all the available roots in a broker.'
    subparser = subparsers.add_parser('roots', help=help)
    subparser.add_argument('--json', action='store_true')
    subparser.set_defaults(func=cmd_roots)

    # subscribe
    help = 'Request access to the datasets in a root.'
    subparser = subparsers.add_parser('subscribe', help=help)
    subparser.add_argument('--json', action='store_true')
    subparser.add_argument('root')
    subparser.set_defaults(func=cmd_subscribe)

    # list
    help = 'List all the available datasets in a root. Needs to be subscribed to the root.'
    subparser = subparsers.add_parser('list', help=help)
    subparser.add_argument('--json', action='store_true')
    subparser.add_argument('root')
    subparser.set_defaults(func=cmd_list)

    # url
    help = 'URL for the rest API that serves the root.'
    subparser = subparsers.add_parser('url', help=help)
    subparser.add_argument('--json', action='store_true')
    subparser.add_argument('root')
    subparser.set_defaults(func=cmd_url)

    # info
    help = 'Get metadata about a dataset.'
    subparser = subparsers.add_parser('info', help=help)
    subparser.add_argument('--json', action='store_true')
    subparser.add_argument('dataset', type=dataset_with_slice)
    subparser.set_defaults(func=cmd_info)

    # show
    help = 'Display a dataset'
    subparser = subparsers.add_parser('show', help=help)
    subparser.add_argument('--json', action='store_true')
    subparser.add_argument('dataset', type=dataset_with_slice)
    subparser.set_defaults(func=cmd_show)

    # download
    help = 'Download a dataset and save it in the local system'
    subparser = subparsers.add_parser('download', help=help)
    subparser.add_argument('--json', action='store_true')
    subparser.add_argument('dataset', type=dataset_with_slice)
    subparser.add_argument('output_dir', nargs='?', default='.', type=pathlib.Path)
    subparser.set_defaults(func=cmd_download)

    # Go
    args = cli_utils.run_parser(parser)
    args.func(args)
