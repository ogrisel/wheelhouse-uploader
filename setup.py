#! /usr/bin/env python
# Authors: Olivier Grisel <olivier.grisel@ensta.org>
#          MinRK
# LICENSE: MIT
from setuptools import setup

try:
    # For dogfooding only
    import wheelhouse_uploader.cmd
    cmdclass = vars(wheelhouse_uploader.cmd)
except ImportError:
    cmdclass = {}


setup(
    name="wheelhouse-uploader",
    version="0.10.3",
    description="Upload wheels to any cloud storage supported by Libcloud",
    maintainer="Olivier Grisel",
    maintainer_email="olivier.grisel@ensta.org",
    license="MIT",
    url='http://github.com/ogrisel/wheelhouse-uploader',
    packages=[
        'wheelhouse_uploader',
    ],
    setup_requires=['setuptools-markdown'],
    install_requires=[
        "setuptools>=0.9",  # required for PEP 440 version parsing
        "packaging",
        "certifi",
        'futures; python_version == "2.7"',
        # https://github.com/ogrisel/wheelhouse-uploader/issues/29
        "apache-libcloud==2.2.1",
    ],
    long_description_markdown_filename='README.md',
    classifiers=[
        'License :: OSI Approved',
        'Programming Language :: Python',
        'Topic :: Software Development',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    cmdclass=cmdclass,
)
