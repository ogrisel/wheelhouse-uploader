wheelhouse-updloader
===================

Script to help maintain a wheelhouse folder on a cloud storage.

Installation:

    pip install wheelhouse-uploader

Usage:

    python -m wheelhouse_uploader \
        --provider=CLOUDFILES_US \
        --username=mycloudaccountid \
        --secret=xxx \
        --local-folder dist/ \
        my_wheelhouse

or:

    export WHEELHOUSE_UPLOADER_USERNAME=mycloudaccountid
    export WHEELHOUSE_UPLOADER_SECRET=xxx
    python -m wheelhouse_uploader --local-folder dist/ my_wheelhouse


The files in the `dist/` folder will be uploaded to a container named
`my_wheelhouse` on the `CLOUDFILES_US` (Rackspace) cloud storage provider.

See the [Apache Libcloud documentation](
https://libcloud.readthedocs.org/en/latest/storage/supported_providers.html)
for the complete list of supported providers.
