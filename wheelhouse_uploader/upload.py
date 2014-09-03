from __future__ import division
import subprocess
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from libcloud.storage.types import Provider, ContainerDoesNotExistError
from libcloud.storage.providers import get_driver
from libcloud.storage.types import ContainerDoesNotExistError


class Uploader(object):

    def __init__(self, options):
        self.options = options

    def make_driver(self):
        provider = getattr(Provider, self.options.provider_name)
        return get_driver(provider)(self.options.username, self.options.secret)

    def upload(self, local_folder, container_name):
        # check that the container is reachable
        driver = self.make_driver()
        try:
            driver.get_container(container_name)
        except ContainerDoesNotExistError:
            driver.create_container(container_name)

        filepaths = []
        for filename in os.listdir(local_folder):
            if filename.startswith('.'):
                continue
            filepath = os.path.join(local_folder, filename)
            if os.path.isdir(filepath):
                continue
            # TODO: use a threadpool
            filepaths.append(filepath)

        with ThreadPoolExecutor(max_workers=self.options.max_workers) as e:
            # Dispatch the file uploads in threads
            futures = [e.submit(self.upload_file, filepath, container_name)
                       for filepath in filepaths]
            for future in as_completed(futures):
                # We don't expect any returned results be we ant to raise
                # an exception in case if problem
                future.result()

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
