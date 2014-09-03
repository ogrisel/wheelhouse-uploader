import argparse
import sys
import os
from libcloud.common.types import InvalidCredsError
from wheelhouse_uploader.upload import Uploader

def parse_args():
    parser = argparse.ArgumentParser(description='Upload wheel packages.')
    parser.add_argument('container_name',
                        help='name of the target container')
    parser.add_argument('--local-folder', default='.',
                        help='path to the folder to upload')
    parser.add_argument('--username',
                        help='account name for the cloud storage')
    parser.add_argument('--secret',
                        help='secret API key for the cloud storage')
    parser.add_argument('--provider-name', default='CLOUDFILES_US',
                        help='Apache Libcloud cloud storage provider')
    parser.add_argument('--max-workers', type=int, default=4,
                        help='maximum number of concurrent uploads')
    options = parser.parse_args()
    if not options.username:
        options.username = os.environ.get('WHEELHOUSE_UPLOADER_USERNAME')
    if not options.secret:
        options.secret = os.environ.get('WHEELHOUSE_UPLOADER_SECRET')
    return options


def main():
    options = parse_args()
    if not options.username:
        print("username required")
        sys.exit(1)
    if not options.secret:
        print("secret API key required")
        sys.exit(1)

    try:
        uploader = Uploader(options)
        uploader.upload(options.local_folder, options.container_name)
    except InvalidCredsError:
        print("Invalid credentials")
        sys.exit(1)
