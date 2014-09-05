try:
    from urllib.request import urlopen
except ImportError:
    # Python 2 compat
    from urllib2 import urlopen
import re
import os
import sys
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

link_pattern = re.compile(r'\bhref="([^"]+)"')


def parse_filename(project_name, filename):
    """Find artifact metadata based on expected project name and filename

    This is necessary to be able to reupload previously generated to PyPI.

    >>> parse_filename('scikit-learn',
    ...                'scikit_learn-0.15.2-cp34-none-win32.whl')
    ('0.15.2', '3.4', 'bdist_wheel')

    >>> parse_filename('scikit-learn',
    ...                'scikit-learn-0.15.1-rc.win-amd64-py2.7.exe')
    ('0.15.1-rc', '2.7', 'bdist_wininst')

    >>> parse_filename('scikit-learn',
    ...               'scikit-learn-0.15.2.win32-py2.7.exe')
    ('0.15.2', '2.7', 'bdist_wininst')

    >>> parse_filename('scikit-learn', 'scikit-learn-0.15.1.tar.gz')
    ('0.15.1', '', 'sdist')

    >>> parse_filename('scikit-learn', 'scikit-learn-0.15.1.zip')
    ('0.15.1', '', 'sdist')

    >>> parse_filename('scikit-learn',
    ...     'scikit_learn-0.15.1-cp34-cp34m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.whl')
    ('0.15.1', '3.4', 'bdist_wheel')

    """
    if filename.endswith('.whl'):
        return _parse_wheel_filename(project_name, filename[:-len('.whl')])
    elif filename.endswith('.exe'):
        return _parse_exe_filename(project_name, filename[:-len('.exe')])
    elif filename.endswith('.zip'):
        return _parse_source_filename(project_name, filename[:-len('.zip')])
    elif filename.endswith('.tar.gz'):
        return _parse_source_filename(project_name, filename[:-len('.tar.gz')])
    else:
        raise ValueError('Invalid filename "%s", unrecognized extension'
                         % filename)

def _parse_wheel_filename(project_name, basename):
    components = basename.split('-')
    if not components[0] == project_name.replace('-', '_'):
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
    return (version, pyversion, 'bdist_wheel')


def _parse_exe_filename(project_name, basename):
    if not basename.startswith(project_name):
        raise ValueError('File %s.exe does not match project name %s'
                         % (basename, project_name))
    metadata_block = basename[len(project_name) + 1:]
    metadata_block, pyversion = metadata_block.rsplit('-', 1)
    pyversion = pyversion[2:]
    version, platform = metadata_block.rsplit('.', 1)
    return (version, pyversion, 'bdist_wininst')


def _parse_source_filename(project_name, basename):
    if not basename.startswith(project_name):
        raise ValueError('File %s.tar.gz does not match project name %s'
                         % (basename, project_name))
    version = basename[len(project_name) + 1:]
    return (version, '', 'sdist')


def download(url, filepath, buffer_size=int(1e6), overwrite=False):
    if not overwrite and os.path.exists(filepath):
        print('%s already exists' % filepath)
        return
    print('downloading %s' % url)
    tmp_filepath = filepath + '.part'
    with open(tmp_filepath, 'wb') as f:
        remote = urlopen(url)
        try:
            data = remote.read(buffer_size)
            while data:
                f.write(data)
                data = remote.read(buffer_size)
        finally:
            if hasattr(remote, 'close'):
                remote.close()
    # download was successful: rename to the final name:
    if os.path.exists(filepath):
        os.unlink(filepath)
    shutil.move(tmp_filepath, filepath)


def download_artifacts(index_url, folder, project_name, version=None,
                       max_workers=4):
    # TODO: use correct encoding
    html_index = urlopen(index_url).read().decode('utf-8')
    artifacts = []
    for match in re.finditer(link_pattern, html_index):
        link = match.group(1)
        if index_url.endswith('/'):
            url = index_url + link
        elif index_url.endswith('.html'):
            url = index_url.rsplit('/', 1)[0] + '/' + link
        else:
            url = index_url + '/' + link
        if '/' in link:
            _, filename = link.rsplit('/', 1)
        else:
            filename = link
        try:
            file_version, _, _ = parse_filename(project_name, filename)
        except ValueError as e:
            # not a supported artifact
            continue

        if version and file_version != version:
            continue

        artifacts.append((url, os.path.join(folder, filename)))
    if not artifacts:
        print('could not find any matching artifact on %s' % index_url)
        return

    print('found %d artifacts to download to %s' % (len(artifacts), folder))
    if not os.path.exists(folder):
        os.makedirs(folder)
    with ThreadPoolExecutor(max_workers=max_workers) as e:
        # Dispatch the file download in threads
        futures = [e.submit(download, url, filepath)
                   for url, filepath in artifacts]
        for future in as_completed(futures):
            # We don't expect any returned results be we want to raise
            # an exception early in case if problem
            future.result()
