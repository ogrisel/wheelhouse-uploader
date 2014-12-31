from __future__ import division
import os
import json
from hashlib import sha256
from time import sleep
from io import StringIO
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed

from libcloud.common.types import InvalidCredsError
from libcloud.storage.providers import get_driver
from libcloud.storage.types import Provider
from libcloud.storage.types import ContainerDoesNotExistError
from libcloud.storage.types import ObjectDoesNotExistError


class Uploader(object):

    index_filename = "index.html"

    metadata_filename = 'metadata.json'

    def __init__(self, username, secret, provider_name, region, update_index=True,
                 max_workers=4):
        self.username = username
        self.secret = secret
        self.provider_name = provider_name
        self.region = region
        self.max_workers = max_workers
        self.update_index = update_index

    def make_driver(self):
        provider = getattr(Provider, self.provider_name)
        return get_driver(provider)(self.username, self.secret,
                                    region=self.region)

    def upload(self, local_folder, container, retry_on_error=3):
        """Wrapper to make upload more robust to random server errors"""
        try:
            self._upload(local_folder, container)
        except InvalidCredsError:
            raise
        except Exception:
            if retry_on_error <= 0:
                raise
            # can be caused by any network or server side failure
            sleep(1)
            self.upload(local_folder, container,
                        retry_on_error=retry_on_error - 1)

    def _upload(self, local_folder, container_name):
        # check that the container is reachable
        driver = self.make_driver()
        try:
            container = driver.get_container(container_name)
        except ContainerDoesNotExistError:
            container = driver.create_container(container_name)

        try:
            metadata_obj = container.get_object(self.metadata_filename)
            content = StringIO()
            for bytes_ in metadata_obj.as_stream():
                content.write(bytes_.decode('utf-8'))
            content.seek(0)
            metadata = json.load(content)
        except ObjectDoesNotExistError:
            metadata = {}

        filepaths, local_metadata = self._scan_local_files(local_folder)

        with ThreadPoolExecutor(max_workers=self.max_workers) as e:
            # Dispatch the file uploads in threads
            futures = [e.submit(self.upload_file, filepath_, container_name)
                       for filepath_ in filepaths]
            for future in as_completed(futures):
                # We don't expect any returned results be we want to raise
                # an exception early in case if problem
                future.result()

        print('Uploading %s' % self.metadata_filename)
        metadata.update(local_metadata)
        metadata_json_bytes = BytesIO(json.dumps(metadata).encode('utf-8'))
        driver.upload_object_via_stream(iterator=metadata_json_bytes,
                                        container=container,
                                        object_name=self.metadata_filename)

        if self.update_index:
            # TODO use a mako template instead
            objects = driver.list_container_objects(container)
            print('Updating index.html with %d links' % len(objects))
            payload = StringIO()
            payload.write(u'<html><body><p>\n')
            for object_ in objects:
                if not object_.name.endswith(('.json', '.html')):
                    object_metadata = metadata.get(object_.name, {})
                    digest = object_metadata.get('sha256')
                    if digest is not None:
                        payload.write(
                            u'<li><a href="%s#sha256=%s">%s<a></li>\n'
                            % (object_.name, digest, object_.name))
                    else:
                        payload.write(u'<li><a href="%s">%s<a></li>\n'
                                      % (object_.name, object_.name))
            payload.write(u'</p></body></html>\n')
            payload.seek(0)
            driver.upload_object_via_stream(iterator=payload,
                                            container=container,
                                            object_name=self.index_filename)

    def _scan_local_files(self, local_folder):
        """Collect file informations on the folder to upload."""
        filepaths = []
        local_metadata = {}

        for filename in os.listdir(local_folder):
            if filename.startswith('.'):
                continue
            filepath = os.path.join(local_folder, filename)
            if os.path.isdir(filepath):
                continue
            # TODO: use a threadpool
            filepaths.append(filepath)
            content = open(filepath, 'rb').read()
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
        with open(filepath, 'rb') as byte_stream:
            driver.upload_object_via_stream(iterator=byte_stream,
                                            container=container,
                                            object_name=filename)

    def get_container_cdn_url(self, container_name):
        driver = self.make_driver()
        container = driver.get_container(container_name)
        if hasattr(driver, 'ex_enable_static_website'):
            driver.ex_enable_static_website(container,
                                            index_file=self.index_filename)
        driver.enable_container_cdn(container)
        return driver.get_container_cdn_url(container)
