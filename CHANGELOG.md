# CHANGELOG

## 0.10.3 - 2020-08-04

  - Fix support for PyPy tags:
    https://github.com/ogrisel/wheelhouse-uploader/pull/37

  - Make it possible to fetch sdist:
    https://github.com/ogrisel/wheelhouse-uploader/pull/36

## 0.10.2 - 2020-02-12

  - Support absolute artifacts URLs.

## 0.10.1 - 2018-07-03

  - Pinning apache-liblcoud==2.2.1 dependency to workaround
    2.3.0 installation problems under Windows.

## 0.10.0 - 2018-07-03

  - Upgrade dependency to latest apache-libcloud
  - Use temporary files for upload and downloads to workaround
    a bug with Python 3.7.

## 0.9.7 - 2018-07-02

  - Add explicit dependency on certifi to resolve SSL
    verification issues on appveyor.
    https://github.com/ogrisel/wheelhouse-uploader/issues/26

## 0.9.5 - 2017-04-26

  - Pin dependency apache-libcloud==1.1.0 to workaround
    regression introduced by version 2.0.0:
    https://github.com/ogrisel/wheelhouse-uploader/issues/22

## 0.9.4 - 2017-02-13

  - Fix bad link markup in HTML index by Joe Rickerby
    https://github.com/ogrisel/wheelhouse-uploader/issues/19

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
