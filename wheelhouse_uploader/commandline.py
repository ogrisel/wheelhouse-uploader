import argparse
import sys
import os
from libcloud.common.types import InvalidCredsError
import libcloud.security
from wheelhouse_uploader.upload import Uploader
from wheelhouse_uploader.fetch import download_artifacts


def parse_args():
    parser = argparse.ArgumentParser(
        description='Manage Python build artifacts',
    )
    subparsers = parser.add_subparsers(
        title='Commands',
    )

    # Options for the upload sub command:
    upload = subparsers.add_parser(
        'upload', help='Attach a local folder to a Nuxeo server.',
    )
    upload.set_defaults(command='upload')

    upload.add_argument('container_name', help='name of the target container')
    upload.add_argument('--local-folder', default='dist',
                        help='path to the folder to upload')
    upload.add_argument('--username',
                        help='account name for the cloud storage')
    upload.add_argument('--secret',
                        help='secret API key for the cloud storage')
    upload.add_argument('--provider-name', default='CLOUDFILES',
                        help='Apache Libcloud cloud storage provider')
    upload.add_argument('--region', default='ord',
                        help='Apache Libcloud cloud storage provider region')
    upload.add_argument('--max-workers', type=int, default=4,
                        help='maximum number of concurrent uploads')
    upload.add_argument('--no-ssl-check', default=False,
                        action="store_true",
                        help='disable SSL certificate validation')
    upload.add_argument('--no-enable-cdn', default=False,
                        action="store_true",
                        help='do not publish the container on CDN')
    upload.add_argument('--no-update-index', default=False,
                        action="store_true",
                        help='build an index.html file')
    upload.add_argument('--upload-pull-request', default=False,
                        action="store_true",
                        help='upload even if it is a pull request')

    # Options for the fetch sub command:
    fetch = subparsers.add_parser(
        'fetch', help='Collect build artifacts from an HTML page.',
    )
    fetch.set_defaults(command='fetch')
    fetch.add_argument('project_name', help='name of the project')
    fetch.add_argument('url', help='url of the HTML index page.')
    fetch.add_argument('--version', help='version of the artifact to collect')
    fetch.add_argument('--local-folder', default='dist',
                       help='path to the folder to store fetched items')
    return parser.parse_args()


def check_upload_credentions(options):
    if not options.username:
        options.username = os.environ.get('WHEELHOUSE_UPLOADER_USERNAME')
    if not options.username:
        print("Username required: pass the --username option or set the "
              "WHEELHOUSE_UPLOADER_USERNAME environment variable")
        sys.exit(1)

    if not options.secret:
        options.secret = os.environ.get('WHEELHOUSE_UPLOADER_SECRET')

    if not options.secret:
        # It is often useful to run travis / appveyor jobs on a specific
        # developer account that does not have the secret key configured.
        # wheelhouse-uploader should not cause such builds to fail, instead
        # it would just skip the upload.
        print("WARNING: secret API key missing: skipping package upload")
        sys.exit(0)


def handle_upload(options):
    check_upload_credentions(options)

    if (not options.upload_pull_request and
        (os.environ.get('APPVEYOR_PULL_REQUEST_NUMBER')
         or os.environ.get('TRAVIS_PULL_REQUEST', 'false') != 'false'
         )):
        print('Skipping upload of packages for pull request.')
        print('Use --upload-pull-request to force upload even on pull '
              'requests.')
        sys.exit(0)

    if options.no_ssl_check:
        # This is needed when the host OS such as Windows does not make
        # make available a CA cert bundle in a standard location.
        libcloud.security.VERIFY_SSL_CERT = False

    try:
        uploader = Uploader(options.username, options.secret,
                            options.provider_name,
                            region=options.region,
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
        print("Invalid credentials for user '%s'" % options.username)
        sys.exit(1)


def main():
    options = parse_args()
    if options.command == 'upload':
        return handle_upload(options)
    elif options.command == 'fetch':
        download_artifacts(options.url, options.local_folder,
                           project_name=options.project_name,
                           version=options.version)
