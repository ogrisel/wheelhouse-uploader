import sys
import re
from pkg_resources import safe_version
from packaging.version import VERSION_PATTERN

# PEP440 version spec
_version_regex = re.compile('^' + VERSION_PATTERN + '$',
                            re.VERBOSE | re.IGNORECASE)


def parse_filename(filename, project_name=None):
    """Find artifact metadata based on filename

    If a an expected project name is provided, consistency is checked: a
    ValueError is raised in case of violation.

    This metadata is necessary to be able to reupload previously generated
    to PyPI.

    >>> parse_filename('scikit_learn-0.15.2-cp34-none-win32.whl')
    ('scikit_learn', '0.15.2', '3.4', 'bdist_wheel')

    >>> parse_filename('scikit-learn-0.15.1rc.win-amd64-py2.7.exe',
    ...                project_name='scikit-learn')
    ('scikit-learn', '0.15.1rc0', '2.7', 'bdist_wininst')

    >>> parse_filename('scikit_learn-0.15.2.dev-cp34-none-win32.whl',
    ...                project_name='scikit-learn')
    ('scikit_learn', '0.15.2.dev0', '3.4', 'bdist_wheel')

    >>> parse_filename('scikit_learn-0.15.dev0+local3-cp27-none-win32.whl')
    ('scikit_learn', '0.15.dev0+local3', '2.7', 'bdist_wheel')

    >>> parse_filename('scikit-learn-0.15.2.win32-py2.7.exe')
    ('scikit-learn', '0.15.2', '2.7', 'bdist_wininst')

    >>> parse_filename('scikit-learn-0.15.1.tar.gz')
    ('scikit-learn', '0.15.1', '', 'sdist')

    >>> parse_filename('scikit-learn-0.15.1.zip')
    ('scikit-learn', '0.15.1', '', 'sdist')

    >>> parse_filename(
    ...     'scikit_learn-0.15.1-cp34-cp34m-macosx_10_6_intel'
    ...     '.macosx_10_9_intel.macosx_10_9_x86_64.whl')
    ('scikit_learn', '0.15.1', '3.4', 'bdist_wheel')

    """
    if filename.endswith('.whl'):
        return _parse_wheel_filename(filename[:-len('.whl')],
                                     project_name=project_name)
    elif filename.endswith('.exe'):
        return _parse_exe_filename(filename[:-len('.exe')],
                                   project_name=project_name)
    elif filename.endswith('.zip'):
        return _parse_source_filename(filename[:-len('.zip')],
                                      project_name=project_name)
    elif filename.endswith('.tar.gz'):
        return _parse_source_filename(filename[:-len('.tar.gz')],
                                      project_name=project_name)
    else:
        raise ValueError('Invalid filename "%s", unrecognized extension'
                         % filename)


def _parse_wheel_filename(basename, project_name=None):
    components = basename.split('-')
    distname = components[0]
    if (project_name is not None and
            distname != project_name.replace('-', '_')):
        raise ValueError('File %s.whl does not match project name %s'
                         % (basename, project_name))

    if len(components) < 3 or not len(components[2]) >= 4:
        raise ValueError('Invalid wheel filename %s.whl' % basename)
    version = components[1]
    pytag = components[2]

    if pytag == 'py2.py3':
        # special handling of the universal Python version tag:
        pyversion = '.'.join(str(x) for x in sys.version_info[:2])
    elif pytag[:2] == 'cp':
        pyversion = '%s.%s' % (pytag[2], pytag[3])
    else:
        raise ValueError('Invalid Python version tag in filename %s.whl'
                         % basename)
    return (distname, safe_version(version), pyversion, 'bdist_wheel')


def _parse_exe_filename(basename, project_name=None):
    remainder, pyversion = basename.rsplit('-', 1)
    name_and_version, platform = remainder.rsplit('.', 1)
    distname, version = name_and_version.rsplit('-', 1)
    if project_name is not None and distname != project_name:
        raise ValueError('File %s.exe does not match project name %s'
                         % (basename, project_name))
    pyversion = pyversion[2:]
    return (distname, safe_version(version), pyversion, 'bdist_wininst')


def _parse_source_filename(basename, project_name=None):
    distname, version = basename.rsplit('-', 1)
    if project_name is not None and distname != project_name:
        raise ValueError('File %s does not match expected project name %s'
                         % (basename, project_name))
    return (distname, safe_version(version), '', 'sdist')


def is_dev(version):
    """Look for dev flag in PEP440 version number

    >>> is_dev('0.15.dev0+local3')
    True
    >>> is_dev('0.15.dev+local3')
    True
    >>> is_dev('0.15+local3')
    False

    """
    # ignore the local segment of PEP400 version strings
    m = _version_regex.match(version)
    return m is not None and m.groupdict().get('dev') is not None
