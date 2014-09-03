wheelhouse-uploader
===================

Script to help maintain a wheelhouse folder on a cloud storage such as
Amazon S3, Rackspace Cloud Files, Google Storage or Azure Storage.

Installation:

    pip install wheelhouse-uploader

Usage:

    python -m wheelhouse_uploader --username=mycloudaccountid --secret=xxx \
        --local-folder=dist/ my_wheelhouse

or:

    export WHEELHOUSE_UPLOADER_USERNAME=mycloudaccountid
    export WHEELHOUSE_UPLOADER_SECRET=xxx
    python -m wheelhouse_uploader --local-folder dist/ my_wheelhouse


The files in the `dist/` folder will be uploaded to a container named
`my_wheelhouse` on the `CLOUDFILES` (Rackspace) cloud storage provider.

You can pass a custom `--provider` param to select the cloud storage from
the list of [supported providers](
https://libcloud.readthedocs.org/en/latest/storage/supported_providers.html).
