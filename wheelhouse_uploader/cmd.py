"""Custom distutils to automate commands for PyPI deployments

The 'fetch_artifacts' command download the artifacts from the matching project
name and version from public HTML repositories to the dist folder.

The 'upload_all' command


Register the wheelhouse_uploader distutils extensions in your setup.py:

    import wheelhouse_uploader.cmd
    cmdclass = vars(wheelhouse_uploader.cmd)
    ...

    setup(
        ...
        cmdclass=cmdclss
    )

Add to setup.cfg:


    [wheelhouse_uploader]
    artifacts_indexes=http://site1.org/
          http://site2.com/wheelhouse.html

Collect the uploads from all the remote artifacts sites and upload them all
to the PyPI release matching the project version of the local setup.py file:

    python setup.py fetch_artifacts upload_all

"""
import os
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser
from distutils.core import Command
from distutils.command.upload import upload

from wheelhouse_uploader.fetch import parse_filename
from wheelhouse_uploader.fetch import fetch_artifacts

__all__ = ['fetch_artifacts', 'upload_all']


class fetch_artifacts(Command):

    def initialize_options(self):
        config = ConfigParser().read('setup.cfg')
        artifact_indexes = config.get('wheelhouse_uploader',
                                      'artifacts_indexes', '')
        self.index_urls = artifact_indexes.strip().split()

    def run(self):
        metadata = self.distribution.metadata
        project_name = metadata.get_name()
        version = metadata.get_version()
        for index_url in self.index_urls:
            fetch_artifacts(index_url, 'dist', project_name, version=version,
                            max_workers=4)


class upload_all(upload):

    def run(self):
        metadata = self.distribution.metadata
        project_name = metadata.get_name()
        version = metadata.get_version()
        print("Collecting artifacts for %s==%s in 'dist' folder:" %
              (project_name, version))
        dist_files = []
        for filename in os.listdir('dist'):
            try:
                file_version, pyversion, command = parse_filename(
                    project_name, filename)
                if file_version != version:
                    continue
            except ValueError:
                continue
            filepath = os.path.join('dist', filename)
            dist_files.append((command, pyversion, filepath))

        if not dist_files:
            raise DistutilsOptionError(
                "No file collected from the 'dist' folder")

        for command, pyversion, filepath in dist_files:
            self.upload_file(command, pyversion, filepath)
