import argparse
import sys
import os
from libcloud.common.types import InvalidCredsError
import libcloud.security
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
    parser.add_argument('--provider-name', default='CLOUDFILES',
                        help='Apache Libcloud cloud storage provider')
    parser.add_argument('--max-workers', type=int, default=4,
                        help='maximum number of concurrent uploads')
    parser.add_argument('--no-ssl-check', default=False, action="store_true",
                        help='Disable SSL certificate validation')
    parser.add_argument('--no-enable-cdn', default=False, action="store_true",
                        help='Do not publish the container on CDN')
    parser.add_argument('--no-update-index', default=False, action="store_true",
                        help='Build an index.html file')
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

    if options.no_ssl_check:
        # This is needed when the host OS such as Windows does not make
        # make available a CA cert bundle in a standard location.
        libcloud.security.VERIFY_SSL_CERT = False

    try:
        uploader = Uploader(options.username, options.secret,
                            options.provider_name,
                            update_index=not options.no_update_index,
                            max_workers=options.max_workers)
        uploader.upload(options.local_folder, options.container_name)

        if not options.no_enable_cdn:
            try:
                url = uploader.get_container_cdn_url(options.container_name)
                print('Wheelhouse successfully published at:')
                print(url)
            except Exception as e:
                print("Failed to enable CDN: %s %s" % (type(e).__name__, e))
    except InvalidCredsError:
        print("Invalid credentials")
        sys.exit(1)
