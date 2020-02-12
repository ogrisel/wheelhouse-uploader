try:
    from urllib.request import urlopen
    from urllib.parse import urlparse
except ImportError:
    # Python 2 compat
    from urllib2 import urlopen
    from urlparse import urlparse
import re
import os
import shutil
from pkg_resources import safe_version
from concurrent.futures import ThreadPoolExecutor, as_completed
from wheelhouse_uploader.utils import parse_filename

link_pattern = re.compile(r'\bhref="([^"]+)"')


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


def _parse_html(index_url, folder, project_name, version=None):
    # TODO: use correct encoding
    html_content = urlopen(index_url).read().decode('utf-8')
    artifacts = []
    found_versions = set()
    for match in re.finditer(link_pattern, html_content):
        link = match.group(1)
        if link.startswith("/"):
            parsed_index_url = urlparse(index_url)
            url = "%s://%s%s" % (parsed_index_url.scheme,
                                 parsed_index_url.netloc,
                                 link)
        elif index_url.endswith('/'):
            url = index_url + link
        elif index_url.endswith('.html'):
            url = index_url.rsplit('/', 1)[0] + '/' + link
        else:
            url = index_url + '/' + link
        if '#' in link:
            # TODO: parse digest info to detect any file content corruption
            link, _ = link.split('#', 1)
        if '/' in link:
            _, filename = link.rsplit('/', 1)
        else:
            filename = link
        try:
            _, file_version, _, _ = parse_filename(filename,
                                                   project_name=project_name)
        except ValueError:
            # not a supported artifact
            continue

        if version is not None and file_version != version:
            found_versions.add(file_version)
            continue

        artifacts.append((url, os.path.join(folder, filename)))
    return artifacts, list(sorted(found_versions))


def download_artifacts(index_url, folder, project_name, version=None,
                       max_workers=4):
    if version is not None:
        version = safe_version(version)
    artifacts, found_versions = _parse_html(index_url, folder, project_name,
                                            version=version)
    if not artifacts:
        print('Could not find any matching artifact for project "%s" on %s'
              % (project_name, index_url))
        if version is not None:
            print("Requested version: %s" % version)
            print("Available versions: %s" % ", ".join(sorted(found_versions)))
        return

    print('Found %d artifacts to download from %s'
          % (len(artifacts), index_url))
    if not os.path.exists(folder):
        os.makedirs(folder)
    with ThreadPoolExecutor(max_workers=max_workers) as e:
        # Dispatch the file download in threads
        futures = [e.submit(download, url_, filepath)
                   for url_, filepath in artifacts]
        for future in as_completed(futures):
            # We don't expect any returned results be we want to raise
            # an exception early in case if problem
            future.result()
