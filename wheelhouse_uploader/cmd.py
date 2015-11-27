"""Custom distutils to automate commands for PyPI deployments

The 'fetch_artifacts' command download the artifacts from the matching project
name and version from public HTML repositories to the dist folder.

The 'upload_all' command scans the content of the `dist` folder for any
previously generated artifacts that match the current project version number
and upload them all to PyPI at once.

"""
import os
try:
    from configparser import ConfigParser, NoSectionError, NoOptionError
except ImportError:
    from ConfigParser import ConfigParser, NoSectionError, NoOptionError
from distutils.cmd import Command
from distutils.command.upload import upload
from distutils.errors import DistutilsOptionError
from pkg_resources import safe_version

from wheelhouse_uploader.utils import parse_filename
from wheelhouse_uploader.fetch import download_artifacts

__all__ = ['fetch_artifacts', 'upload_all']


SETUP_FILE = 'setup.cfg'
SECTION = 'wheelhouse_uploader'
KEY = 'artifact_indexes'


class fetch_artifacts(Command):

    user_options = []

    def initialize_options(self):
        config = ConfigParser()
        try:
            config.read(SETUP_FILE)
            artifact_indexes = config.get(SECTION, KEY)
            lines = [l.strip() for l in artifact_indexes.strip().split('\n')]
            self.index_urls = [l for l in lines if l and not l.startswith('#')]
        except (IOError, KeyError, NoOptionError, NoSectionError):
            raise DistutilsOptionError(
                'Missing url of artifact index configured with key "%s" of '
                'section "%s" in file "%s"' % (KEY, SECTION, SETUP_FILE))

    def finalize_options(self):
        pass

    def run(self):
        metadata = self.distribution.metadata
        project_name = metadata.get_name()
        version = metadata.get_version()
        for index_url in self.index_urls:
            download_artifacts(index_url, 'dist', project_name,
                               version=version, max_workers=4)


class upload_all(upload):

    def run(self):
        metadata = self.distribution.metadata
        project_name = metadata.get_name()
        version = safe_version(metadata.get_version())
        print("Collecting artifacts for %s==%s in 'dist' folder:" %
              (project_name, version))
        dist_files = []
        for filename in os.listdir('dist'):
            try:
                _, file_version, pyversion, command = parse_filename(
                    filename, project_name=project_name)
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
