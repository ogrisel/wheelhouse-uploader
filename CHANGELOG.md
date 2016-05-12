# CHANGELOG

## 0.9.3 - 2016-06-12

  - Fix support for universal wheel filenames.
    https://github.com/ogrisel/wheelhouse-uploader/issues/16

## 0.9.2 - 2015-12-29

  - Fix index.html update issue: it would not display recently
    uploaded wheels due to the eventually consistent behavior of
    container listing.
    https://github.com/ogrisel/wheelhouse-uploader/issues/15

## 0.9.1 - 2015-12-03

  - More informative error message in case of invalid credentials.

## 0.9.0 - 2015-12-03

  - Add a time stamp to the local version segment of uploaded dev
    wheels to make it possible to keep the 5 most recent uploads
    while making it possible for pip to download the most recent
    dev build at any time.
    https://github.com/ogrisel/wheelhouse-uploader/issues/14

## 0.8.0 - 2015-11-30

  - Delete previous versions of recently uploaded 'dev' packages.
    https://github.com/ogrisel/wheelhouse-uploader/issues/13
