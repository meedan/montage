"""
    Defines a class to handle the caching of YouTube thumbnail images
"""
import logging
import cloudstorage as gcs
from cloudstorage import storage_api, api_utils
from google.appengine.api import urlfetch
from google.appengine.ext import blobstore

from django.conf import settings


class YTThumbnailsCache(object):
    """
        Class to handle the fetching and caching of YouTube thumbnail images
    """
    max_fetch_retries = 8
    gcs_bucket = 'gd-yt-thumbs'
    gcs_format = '/{gcs_bucket}/{bucket_folder}/{yt_id}/'

    def __init__(self, youtube_id):
        """
            Create the cache object
        """
        self.youtube_id = youtube_id

    def fetch(self, at_milliseconds):
        """
            Tries to fetch the thumbnail from the cache.

            If it is not there, tries to retrieve it from YouTube
            and caches the result if successful

            Returns:
            either the thumbnail or the default thumbnail image
            whether the thumbnail fetch was successful or not
        """
        cached_key = self.create_key(at_milliseconds)

        image_content = self.fetch_cached_thumbnail(cached_key)

        if not image_content:
            image_content, found = self.fetch_thumbnail_from_youtube(
                at_milliseconds)

            if found:
                self.cache_thumbnail(image_content, cached_key)
        else:
            found = True

        return image_content, found

    def fetch_thumbnail_from_youtube(self, at_milliseconds):
        """
            Retrieves the YT thumbnail.

            Returns the raw image content with the
        """
        url = \
        "http://img.youtube.com/vd?id={yt_id}&ats={at_milliseconds}".format(
            yt_id=self.youtube_id, at_milliseconds=at_milliseconds)

        retries = 0
        content = None
        found = False
        while retries <= self.max_fetch_retries:
            result = urlfetch.fetch(url, deadline=50)
            if result.status_code in (200, 404,):
                content = result.content

            if result.status_code == 200:
                found = True
                break
            else:
                retries += 1

        return content, found

    def remove_all_cached_thumbnail_images(self):
        """
            Removes all cached thumbnail images from GCS for this YT video
        """
        gcs_folder = self.gcs_format.format(
            gcs_bucket=settings.GCS_BUCKET,
            bucket_folder=self.gcs_bucket,
            yt_id=self.youtube_id
        )
        api = storage_api._get_storage_api(None)

        futures = {}
        for file_stat in gcs.listbucket(gcs_folder, delimiter="/"):
            filename = api_utils._quote_filename(file_stat.filename)
            futures[file_stat.filename] = api.delete_object_async(filename)

        for filename, future in futures.items():
            status, resp_headers, content = future.get_result()
            if status != 204:
                logging.error(
                    "Could not delete thumbnail {0}: {1}", filename, content)
            else:
                logging.info("Deleted thumbnail file {0}:", filename)

    def create_key(self, at_milliseconds):
        key_format = self.gcs_format + "ytthumb-{yt_id}-{at_milliseconds}"
        return key_format.format(
            gcs_bucket=settings.GCS_BUCKET,
            bucket_folder=self.gcs_bucket,
            yt_id=self.youtube_id,
            at_milliseconds=at_milliseconds)

    @classmethod
    def fetch_cached_thumbnail(cls, cached_key):
        blob_info = blobstore.get(
            blobstore.create_gs_key("/gs{0}".format(cached_key)))

        if blob_info:
            with blob_info.open() as f_blob:
                return f_blob.read()

    @classmethod
    def cache_thumbnail(cls, image_content, cached_key):
        with gcs.open(cached_key, 'w') as f:
            f.write(image_content)

        return blobstore.create_gs_key("/gs{0}".format(cached_key))
