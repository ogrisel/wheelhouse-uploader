from __future__ import division
import os
import json
from hashlib import sha256
from time import sleep
from io import StringIO
from traceback import print_exc
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

from libcloud.common.types import InvalidCredsError
from libcloud.storage.providers import get_driver
from libcloud.storage.types import Provider
from libcloud.storage.types import ContainerDoesNotExistError
from libcloud.storage.types import ObjectDoesNotExistError

from wheelhouse_uploader.utils import matching_dev_filenames, stamp_dev_wheel


class Uploader(object):

    index_filename = "index.html"

    metadata_filename = 'metadata.json'

    def __init__(self, username, secret, provider_name, region,
                 update_index=True, max_workers=4,
                 delete_previous_dev_packages=True):
        self.username = username
        self.secret = secret
        self.provider_name = provider_name
        self.region = region
        self.max_workers = max_workers
        self.update_index = update_index
        self.delete_previous_dev_packages = delete_previous_dev_packages

    def make_driver(self):
        provider = getattr(Provider, self.provider_name)
        return get_driver(provider)(self.username, self.secret,
                                    region=self.region)

    def upload(self, local_folder, container, retry_on_error=3):
        """Wrapper to make upload more robust to random server errors"""
        try:
            return self._try_upload_once(local_folder, container)
        except InvalidCredsError:
            raise
        except Exception as e:
            if retry_on_error <= 0:
                raise
            # can be caused by any network or server side failure
            print(e)
            print_exc()
            sleep(1)
            self.upload(local_folder, container,
                        retry_on_error=retry_on_error - 1)

    def _try_upload_once(self, local_folder, container_name):
        # check that the container is reachable
        driver = self.make_driver()
        try:
            container = driver.get_container(container_name)
        except ContainerDoesNotExistError:
            container = driver.create_container(container_name)

        filepaths, local_metadata = self._scan_local_files(local_folder)

        self._upload_files(filepaths, container_name)
        recently_uploaded = [os.path.basename(path) for path in filepaths]

        # Refresh metadata
        metadata = self._update_metadata_file(
            driver, container, local_metadata,
            recently_uploaded=recently_uploaded)
        if self.update_index:
            self._update_index(driver, container, metadata,
                               recently_uploaded=recently_uploaded)

    def _upload_files(self, filepaths, container_name):
        print("About to upload %d files" % len(filepaths))
        with ThreadPoolExecutor(max_workers=self.max_workers) as e:
            # Dispatch the file uploads in threads
            futures = [e.submit(self.upload_file, filepath_, container_name)
                       for filepath_ in filepaths]
            for future in as_completed(futures):
                # We don't expect any returned results be we want to raise
                # an exception early in case if problem
                future.result()

    def _upload_bytes(self, payload, container, object_name):
        tempdir = tempfile.mkdtemp()
        tempfilepath = os.path.join(
            tempdir, '_tmp_wheelhouse_uploader_upload_' + object_name)
        try:
            with open(tempfilepath, 'wb') as f:
                f.write(payload)
            container.upload_object(file_path=tempfilepath,
                                    object_name=object_name)
        finally:
            try:
                shutil.rmtree(tempdir)
            except OSError:
                # Ignore permission errors on temporary directories
                print("WARNING: failed to delete", tempdir)

    def _download_bytes(self, container, object_name, missing=None):
        tempdir = tempfile.mkdtemp()
        tempfilepath = os.path.join(
            tempdir, '_tmp_wheelhouse_uploader_download_' + object_name)
        try:
            container.get_object(object_name).download(tempfilepath)
            with open(tempfilepath, 'rb') as f:
                return f.read()
        except ObjectDoesNotExistError:
            return missing
        finally:
            try:
                shutil.rmtree(tempdir)
            except OSError:
                # Ignore permission errors on temporary directories
                print("WARNING: faile to delete", tempdir)

    def _update_metadata_file(self, driver, container, local_metadata,
                              recently_uploaded=()):
        data = self._download_bytes(container, self.metadata_filename)
        if data is None:
            metadata = {}
        else:
            metadata = json.loads(data.decode('utf-8'))
        metadata.update(local_metadata)

        # Garbage collect metadata for deleted files
        filenames = set(self._get_package_filenames(driver, container))

        # Make sure that the recently uploaded files are included: the
        # eventual consistency semantics of the container listing might hidden
        # them temporarily.
        filenames.union(recently_uploaded)

        keys = list(sorted(metadata.keys()))
        for key in keys:
            if key not in filenames:
                del metadata[key]

        print('Uploading %s with %d entries'
              % (self.metadata_filename, len(metadata)))

        self._upload_bytes(json.dumps(metadata).encode('utf-8'),
                           container, self.metadata_filename)
        return metadata

    def _get_package_filenames(self, driver, container,
                               ignore_list=('.json', '.html')):
        package_filenames = []
        objects = driver.list_container_objects(container)
        for object_ in objects:
            if not object_.name.endswith(ignore_list):
                package_filenames.append(object_.name)
        return package_filenames

    def _update_index(self, driver, container, metadata, recently_uploaded=()):
        # TODO use a mako template instead
        package_filenames = self._get_package_filenames(driver, container)

        # Make sure that the recently uploaded files are included: the
        # eventual consistency semantics of the container listing might hidden
        # them temporarily.
        package_filenames = set(package_filenames).union(recently_uploaded)
        package_filenames = sorted(package_filenames)

        print('Updating index.html with %d links' % len(package_filenames))
        payload = StringIO()
        payload.write(u'<html><body><p>\n')
        for filename in package_filenames:
            object_metadata = metadata.get(filename, {})
            digest = object_metadata.get('sha256')
            if digest is not None:
                payload.write(
                    u'<li><a href="%s#sha256=%s">%s</a></li>\n'
                    % (filename, digest, filename))
            else:
                payload.write(u'<li><a href="%s">%s</a></li>\n'
                              % (filename, filename))
        payload.write(u'</p></body></html>\n')
        payload.seek(0)
        self._upload_bytes(payload.getvalue().encode('utf-8'),
                           container, self.index_filename)

    def _scan_local_files(self, local_folder):
        """Collect file informations on the folder to upload.

        Dev wheel files will automatically get renamed to add an upload time
        stamp in the process.

        """
        filepaths = []
        local_metadata = {}

        for filename in sorted(os.listdir(local_folder)):
            if filename.startswith('.'):
                continue
            filepath = os.path.join(local_folder, filename)
            if os.path.isdir(filepath):
                continue

            try:
                should_rename, new_filename = stamp_dev_wheel(filename)
                new_filepath = os.path.join(local_folder, new_filename)
                if should_rename:
                    print("Renaming dev wheel to add an upload timestamp: %s"
                          % new_filename)
                    os.rename(filepath, new_filepath)
                    filepath, filename = new_filepath, new_filename
            except ValueError as e:
                print("Skipping %s: %s" % (filename, e))
                continue
            # TODO: use a threadpool
            filepaths.append(filepath)
            with open(filepath, 'rb') as f:
                content = f.read()
            local_metadata[filename] = dict(
                sha256=sha256(content).hexdigest(),
                size=len(content),
            )
        return filepaths, local_metadata

    def upload_file(self, filepath, container_name):
        # drivers are not thread safe, hence we create one per upload task
        # to make it possible to use a thread pool executor
        driver = self.make_driver()
        filename = os.path.basename(filepath)
        container = driver.get_container(container_name)

        size_mb = os.stat(filepath).st_size / 1e6
        print("Uploading %s [%0.3f MB]" % (filepath, size_mb))
        driver.upload_object(file_path=filepath,
                             container=container,
                             object_name=filename)

        if self.delete_previous_dev_packages:
            existing_filenames = self._get_package_filenames(driver, container)
            if filename not in existing_filenames:
                # Eventual consistency listing might cause the just uploaded
                # file not be missing. Ensure this is never the case.
                existing_filenames.append(filename)
            previous_dev_filenames = matching_dev_filenames(filename,
                                                            existing_filenames)

            # Only keep the last 5 dev builds
            for filename in previous_dev_filenames[5:]:
                print("Deleting old dev package %s" % filename)
                try:
                    obj = container.get_object(filename)
                    driver.delete_object(obj)
                except ObjectDoesNotExistError:
                    pass

    def get_container_cdn_url(self, container_name):
        driver = self.make_driver()
        container = driver.get_container(container_name)
        if hasattr(driver, 'ex_enable_static_website'):
            driver.ex_enable_static_website(container,
                                            index_file=self.index_filename)
        driver.enable_container_cdn(container)
        return driver.get_container_cdn_url(container)
