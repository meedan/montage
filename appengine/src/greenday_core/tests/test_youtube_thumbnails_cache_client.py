"""
    Tests for :mod:`greenday_core.youtube_thumbnails_cache <greenday_core.youtube_thumbnails_cache>`
"""
from greenday_core.tests.base import AppengineTestBed
from greenday_core.youtube_thumbnails_cache import YTThumbnailsCache


class YTThumbnailClientTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.youtube_thumbnails_cache.YTThumbnailsCache <greenday_core.youtube_thumbnails_cache.YTThumbnailsCache>`
    """
    def test_remove_all_cached_thumbnail_images(self):
        """
            :func:`greenday_core.youtube_thumbnails_cache.YTThumbnailsCache.remove_all_cached_thumbnail_images <greenday_core.youtube_thumbnails_cache.YTThumbnailsCache.remove_all_cached_thumbnail_images>`
            should remove all cached thumbnail images for a video
        """
        yt_cache = YTThumbnailsCache('ytid')

        keys = [yt_cache.create_key(time) for time in (42, 1024)]
        for key in keys:
            yt_cache.cache_thumbnail('dummy content', key)

        for key in keys:
            self.assertTrue(yt_cache.fetch_cached_thumbnail(key))

        yt_cache.remove_all_cached_thumbnail_images()

        for key in keys:
            self.assertFalse(yt_cache.fetch_cached_thumbnail(key))
