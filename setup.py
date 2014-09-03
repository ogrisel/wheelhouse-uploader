#! /usr/bin/env python
# Authors: Olivier Grisel <olivier.grisel@ensta.org>
#          MinRK
# LICENSE: MIT
try:
    # To add support for python setup.py develop and
    # install_requires
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="wheelhouse-uploader",
    version="0.1-dev",
    description="Upload wheels to any cloud storage supported by Libcloud",
    maintainer="Olivier Grisel",
    maintainer_email="olivier.grisel@ensta.org",
    license="MIT",
    url='http://github.com/ogrisel/wheelhouse-updater',
    packages=[
        'wheelhouse_uploader',
    ],
    install_requires=[
        "futures",
        "apache-libcloud",
    ],
    classifiers=[
        'License :: OSI Approved',
        'Programming Language :: Python',
        'Topic :: Software Development',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
        'Development Status :: 3 - Alpha',
    ],
)
