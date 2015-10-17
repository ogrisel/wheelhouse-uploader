wheelhouse-uploader
===================

Upload/download wheels to/from cloud storage using Apache Libcloud. Helps
package maintainers build wheels for their packages and upload them to PyPI.

The cloud storage containers are typically populated by Continuous Integration
servers that generate and test binary packages on various platforms (Windows
and OSX for several versions and architectures for Python). At release time
the project maintainer can collect all the generated package for a specific
version of the project and upload them all at once to PyPI.


## Installation

~~~bash
pip install wheelhouse-uploader
~~~

## Usage

The canonical use case is:

1. Continuous Integration (CI) workers build and test the project packages for
   various platforms and versions of Python, for instance using the commands:

   ~~~bash
   pip install wheel
   python setup.py bdist_wheel
   ~~~

2. CI workers use `wheelhouse-uploader` to upload the generated artifacts
   to one or more cloud storage containers (e.g. one container per platform,
   or one for the master branch and the other for release tags):

   ~~~bash
   python -m wheelhouse_uploader upload container_name
   ~~~

3. The project maintainer uses the `wheelhouse-uploader` distutils extensions
   to fetch all the generated build artifacts for a specific version number to
   its local `dist` folder and upload them all at once to PyPI when
   making a release.

   ~~~bash
   python setup.py sdist fetch_artifacts upload_all
   ~~~


### Uploading artifact to a cloud storage container

Use the following command:

~~~bash
python -m wheelhouse_uploader upload \
    --username=mycloudaccountid --secret=xxx \
    --local-folder=dist/ my_wheelhouse
~~~

or:

~~~bash
export WHEELHOUSE_UPLOADER_USERNAME=mycloudaccountid
export WHEELHOUSE_UPLOADER_SECRET=xxx
python -m wheelhouse_uploader upload --local-folder dist/ my_wheelhouse
~~~

When used in a CI setup such as http://travis-ci.org or http://appveyor.com,
the environment variables are typically configured in the CI configuration
files such as `.travis.yml` or `appveyor.yml`. The secret API key is typically
encrypted and exposed with a `secure:` prefix in those files.

The files in the `dist/` folder will be uploaded to a container named
`my_wheelhouse` on the `CLOUDFILES` (Rackspace) cloud storage provider.

You can pass a custom `--provider` param to select the cloud storage from
the list of [supported providers](
https://libcloud.readthedocs.org/en/latest/storage/supported_providers.html).

Assuming the container will be published as a static website using the cloud
provider CDN options, the `upload` command also maintains an `index.html` file
with links to all the files previously uploaded to the container.

It is recommended to configure the container CDN cache TTL to a shorter than
usual duration such as 15 minutes to be able to quickly perform a release once
all artifacts have been uploaded by the CI servers.


### Fetching artifacts manually

The following command downloads items that have been previously published to a
web page with an index with HTML links to the project files:

~~~bash
python -m wheelhouse_uploader fetch \
    --version=X.Y.Z --local-folder=dist/ \
    project-name http://wheelhouse.example.org/
~~~

### Uploading previously archived artifacts to PyPI (deprecated)

**DEPRECATION NOTICE**: while the following still works, you are advised
to use the alternative tool: [twine](https://pypi.python.org/pypi/twine)
that makes it easy to script uploads of packages to PyPI without messing
around with distutils and `setup.py`.

Ensure that the `setup.py` file of the project registers the
`wheelhouse-uploader` distutils extensions:

~~~python
cmdclass = {}

try:
    # Used by the release manager of the project to add support for:
    # python setup.py sdist fetch_artifacts upload_all
    import wheelhouse_uploader.cmd
    cmdclass.update(vars(wheelhouse_uploader.cmd))
except ImportError:
    pass
...

setup(
    ...
    cmdclass=cmdclass,
)
~~~

Put the URL of the public artifact repositories populated by the CI workers
in the `setup.cfg` file of the project:

~~~ini
[wheelhouse_uploader]
artifact_indexes=
    http://wheelhouse.site1.org/
    http://wheelhouse.site2.org/
~~~

Fetch all the artifacts matching the current version of the project as
configured in the local `setup.py` file and upload them all to PyPI:

~~~bash
python setup.py fetch_artifacts upload_all
~~~

Note: this will reuse PyPI credentials stored in `$HOME/.pypirc` if
`python setup.py register` or `upload` were called previously.


### TODO

- test on as many cloud storage providers as possible (please send an email to
  olivier.grisel@ensta.org if you can make it work on a non-Rackspace provider),
- check that CDN activation works everywhere (it's failing on Rackspace
  currently: need to investigate) otherwise the workaround is to enable CDN
  manually in the management web UI,
- make it possible to fetch private artifacts using the cloud storage protocol
  instead of HTML index pages.
