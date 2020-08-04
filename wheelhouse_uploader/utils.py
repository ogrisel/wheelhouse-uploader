import sys
import re
from datetime import datetime
from pkg_resources import safe_version, parse_version
from packaging.version import VERSION_PATTERN

# PEP440 version spec
_version_regex = re.compile('^' + VERSION_PATTERN + '$',
                            re.VERBOSE | re.IGNORECASE)

_stamp_regex = re.compile(r'(\d{14})(_\w+)?')


def _wheel_escape(component):
    return re.sub("[^\w\d.]+", "_", component, re.UNICODE)


def parse_filename(filename, project_name=None, return_tags=False):
    """Find artifact metadata based on filename

    If a an expected project name is provided, consistency is checked: a
    ValueError is raised in case of violation.

    This metadata is necessary to be able to reupload previously generated
    to PyPI.

    >>> parse_filename('project-1.0-py2.py3-none-any.whl')
    ...                                                   # doctest: +ELLIPSIS
    ('project', '1.0', ..., 'bdist_wheel')

    >>> parse_filename('scikit_learn-0.15.2-cp34-none-win32.whl')
    ('scikit_learn', '0.15.2', '3.4', 'bdist_wheel')

    >>> parse_filename('scikit-learn-0.15.1rc.win-amd64-py2.7.exe',
    ...                project_name='scikit-learn')
    ('scikit_learn', '0.15.1rc0', '2.7', 'bdist_wininst')

    >>> parse_filename('scikit_learn-0.15.2.dev-cp34-none-win32.whl',
    ...                project_name='scikit-learn')
    ('scikit_learn', '0.15.2.dev0', '3.4', 'bdist_wheel')

    >>> parse_filename('scikit_learn-0.15.dev0+local3-cp27-none-win32.whl')
    ('scikit_learn', '0.15.dev0+local3', '2.7', 'bdist_wheel')

    >>> tags = parse_filename('project-0.1-cp27-none-win32.whl',
    ...                       return_tags=True)[-1]
    >>> tags['python']
    'cp27'
    >>> tags['abi']
    'none'
    >>> tags['platform']
    'win32'

    >>> parse_filename('scikit-learn-0.15.2.win32-py2.7.exe')
    ('scikit_learn', '0.15.2', '2.7', 'bdist_wininst')

    >>> parse_filename('scikit-learn-0.15.1.tar.gz')
    ('scikit_learn', '0.15.1', '', 'sdist')

    >>> parse_filename('scikit-learn-0.15.1.zip')
    ('scikit_learn', '0.15.1', '', 'sdist')

    >>> parse_filename('scikit-learn-0.15.1.zip', return_tags=True)
    ('scikit_learn', '0.15.1', '', 'sdist', {})

    >>> parse_filename(
    ...     'scikit_learn-0.15.1-cp34-cp34m-macosx_10_6_intel'
    ...     '.macosx_10_9_intel.macosx_10_9_x86_64.whl')
    ('scikit_learn', '0.15.1', '3.4', 'bdist_wheel')

    >>> parse_filename('sklearn_template-0.0.3-py2-none-any.whl')
    ('sklearn_template', '0.0.3', '2', 'bdist_wheel')

    >>> parse_filename('sklearn_template-0.0.3-py3-none-any.whl')
    ('sklearn_template', '0.0.3', '3', 'bdist_wheel')

    >>> parse_filename('sklearn-template-0.0.3.win32.exe') # doctest: +ELLIPSIS
    ('sklearn_template', '0.0.3', ..., 'bdist_wininst')

    >>> parse_filename('sklearn-template-0.0.3.win-amd64.exe')
    ... # doctest: +ELLIPSIS
    ('sklearn_template', '0.0.3', ..., 'bdist_wininst')
    """
    if filename.endswith('.whl'):
        return _parse_wheel_filename(filename[:-len('.whl')],
                                     project_name=project_name,
                                     return_tags=return_tags)
    elif filename.endswith('.exe'):
        return _parse_exe_filename(filename[:-len('.exe')],
                                   project_name=project_name,
                                   return_tags=return_tags)
    elif filename.endswith('.zip'):
        return _parse_source_filename(filename[:-len('.zip')],
                                      project_name=project_name,
                                      return_tags=return_tags)
    elif filename.endswith('.tar.gz'):
        return _parse_source_filename(filename[:-len('.tar.gz')],
                                      project_name=project_name,
                                      return_tags=return_tags)
    else:
        raise ValueError('Invalid filename "%s", unrecognized extension'
                         % filename)


def _parse_wheel_filename(basename, project_name=None, return_tags=False):
    components = basename.split('-')
    distname = components[0]
    if (project_name is not None and
            distname != _wheel_escape(project_name)):
        raise ValueError('File %s.whl does not match project name %s'
                         % (basename, project_name))

    if len(components) < 3 or not len(components[2]) >= 3:
        raise ValueError('Invalid wheel filename %s.whl' % basename)
    version = components[1]
    pytag = components[2]
    abitag = components[3]
    platformtag = components[4]

    if pytag == 'py2.py3':
        # special handling of the universal Python version tag:
        pyversion = '.'.join(str(x) for x in sys.version_info[:2])
    elif pytag[:2] == 'py' and len(pytag) == 3:
        pyversion = '%s' % pytag[2]
    elif pytag[:2] in ['pp', 'py'] and len(pytag) == 4:
        pyversion = '%s.%s' % (pytag[2], pytag[3])
    elif pytag[:2] == 'cp':
        pyversion = '%s.%s' % (pytag[2], pytag[3])
    else:
        raise ValueError('Invalid or unsupported Python version tag in '
                         'filename %s.whl' % basename)
    if return_tags:
        tags = {
            'python': pytag,
            'abi': abitag,
            'platform': platformtag,
        }
        return (distname, safe_version(version), pyversion, 'bdist_wheel',
                tags)
    else:
        return (distname, safe_version(version), pyversion, 'bdist_wheel')


def _parse_exe_filename(basename, project_name=None, return_tags=True):
    remainder, pythontag = basename.rsplit('-', 1)
    if not pythontag.startswith('py'):
        # There was no python tag with this file, therefore it must be
        # python version independent
        pythontag = 'py' + '.'.join(str(x) for x in sys.version_info[:2])
        remainder = basename
    name_and_version, platform = remainder.rsplit('.', 1)
    distname, version = name_and_version.rsplit('-', 1)
    distname = _wheel_escape(distname)
    if project_name is not None and distname != _wheel_escape(project_name):
        raise ValueError('File %s.exe does not match project name %s'
                         % (basename, project_name))
    pyversion = pythontag[2:]
    if return_tags:
        tags = {
            'python': pythontag.replace('.', ''),
            'platform': _wheel_escape(platform),
        }
        return (distname, safe_version(version), pyversion, 'bdist_wininst',
                tags)
    return (distname, safe_version(version), pyversion, 'bdist_wininst')


def _parse_source_filename(basename, project_name=None, return_tags=True):
    distname, version = basename.rsplit('-', 1)
    distname = _wheel_escape(distname)
    if project_name is not None and distname != _wheel_escape(project_name):
        raise ValueError('File %s does not match expected project name %s'
                         % (basename, project_name))
    if return_tags:
        return (distname, safe_version(version), '', 'sdist', {})
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


def matching_dev_filenames(reference_filename, existing_filenames):
    """Filter filenames for matching dev packages.

    Return filenames for dev packages with matching package names, package
    type, python version and platform information.

    Sort them by version number (higer versions first).

    >>> matching_dev_filenames(
    ...     "package-1.0.dev0+001_local1-cp34-none-win32.whl",
    ...     [
    ...         "package-1.0.dev0+000_local1-cp34-none-win32.whl",
    ...         "package-1.1.dev+local1-cp34-none-win32.whl",
    ...         "package-1.0.dev0+001_local1-cp34-none-win32.whl",
    ...         "package-0.9-cp34-none-win32.whl",
    ...         "package-1.0.dev+local1-cp34-none-win_amd64.whl",
    ...         "other_package-1.0.dev+local0-cp34-none-win32.whl",
    ...         "package-1.0.dev+local0-cp33-none-win32.whl",
    ...         "package-1.0.dev+local1-cp34-none-win32.whl",
    ...     ])                                # doctest: +NORMALIZE_WHITESPACE
    ['package-1.1.dev+local1-cp34-none-win32.whl',
     'package-1.0.dev0+001_local1-cp34-none-win32.whl',
     'package-1.0.dev0+000_local1-cp34-none-win32.whl',
     'package-1.0.dev+local1-cp34-none-win32.whl']

    If the reference filename is not a dev version, an empty list is returned.

    >>> matching_dev_filenames("package-1.0+local1-cp34-none-win32.whl", [
    ...     "package-1.0.dev+local1-cp34-none-win32.whl",
    ...     "package-0.9+local1-cp34-none-win32.whl",
    ... ])
    []

    >>> matching_dev_filenames("package-1.0.invalid", [
    ...     "package-1.0.dev+local1-cp34-none-win32.whl",
    ...     "package-0.9+local1-cp34-none-win32.whl",
    ... ])
    []

    """
    try:
        distname, version, _, disttype, tags = parse_filename(
            reference_filename, return_tags=True)
    except ValueError:
        # Invalid filemame: no dev match
        return []

    if not is_dev(version):
        return []

    reference_key = (distname, disttype, tags)
    matching = []
    for filename in existing_filenames:
        try:
            distname, version, _, disttype, tags = parse_filename(
                filename, return_tags=True)
        except ValueError:
            # Invalid filemame: no dev match
            continue
        if not is_dev(version):
            continue
        candidate_key = (distname, disttype, tags)
        if reference_key == candidate_key:
            matching.append((version, filename))
    matching.sort(key=lambda x: parse_version(x[0]), reverse=True)
    return [filename for _, filename in matching]


def has_stamp(version):
    """Check that the local segment looks like a timestamp

    >>> has_stamp('0.1.dev0+20151214030042')
    True
    >>> has_stamp('0.1.dev0+20151214030042_deadbeef')
    True
    >>> has_stamp('0.1.dev0+deadbeef')
    False
    >>> has_stamp('0.1.dev0')
    False

    """
    v = parse_version(version)
    if v.local is None:
        return False
    return _stamp_regex.match(v.local) is not None


def local_stamp(version):
    """Prefix the local segment with a UTC timestamp

    The goal is to make sure that the lexical order of the dev versions
    is matching the CI build ordering.

    >>> 'deadbeef' < 'cafebabe'
    False

    >>> v1 = local_stamp('0.1.dev0+deadbeef')
    >>> v1                                                # doctest: +ELLIPSIS
    '0.1.dev0+..._deadbeef'

    >>> import time
    >>> time.sleep(1)  # local_stamp has a second-level resolution
    >>> v2 = local_stamp('0.1.dev0+cafebabe')
    >>> v2                                                # doctest: +ELLIPSIS
    '0.1.dev0+..._cafebabe'
    >>> parse_version(v1) < parse_version(v2)
    True

    This also works even if the original version does not have a local
    segment:

    >>> v3 = local_stamp('0.1.dev0')
    >>> parse_version(v1) < parse_version(v3)
    True

    """
    v = parse_version(version)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    if v.local is not None:
        return "%s+%s_%s" % (v.public, timestamp, v.local)
    else:
        return "%s+%s" % (v.public, timestamp)


def stamp_dev_wheel(filename):
    """Rename a filename to add a timestamp only if this is a dev package

    >>> stamp_dev_wheel('proj-0.1.dev0-py2.py3-none-any.whl')
    ...                                                   # doctest: +ELLIPSIS
    (True, 'proj-0.1.dev0+...-py2.py3-none-any.whl')

    Do no stamp release packages, only dev packages:

    >>> stamp_dev_wheel('proj-0.1-py2.py3-none-any.whl')
    (False, 'proj-0.1-py2.py3-none-any.whl')

    Do not restamp a package that has already been stamped:

    >>> stamp_dev_wheel('proj-0.1.dev0+20151214030042-py2.py3-none-any.whl')
    (False, 'proj-0.1.dev0+20151214030042-py2.py3-none-any.whl')

    Non-dev non-wheel files should be left unaffected:

    >>> stamp_dev_wheel('scikit-learn-0.15.1rc.win-amd64-py2.7.exe')
    (False, 'scikit-learn-0.15.1rc.win-amd64-py2.7.exe')

    """
    distname, version, _, disttype, tags = parse_filename(
        filename, return_tags=True)
    if not is_dev(version):
        # Do no stamp release packages, only dev packages
        return False, filename

    if disttype != 'bdist_wheel':
        raise ValueError("%s only dev wheel file can be stamped for upload"
                         % filename)

    if has_stamp(version):
        # Package has already been stamped, do nothing
        return False, filename
    else:
        version = local_stamp(version)
    return True, "%s-%s-%s-%s-%s.whl" % (distname, version, tags['python'],
                                         tags['abi'], tags['platform'])
