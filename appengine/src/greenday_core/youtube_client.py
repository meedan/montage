"""
    Defines YouTubeClient and some methods to update the YouTube data
    stored in the Montage database
"""
import logging
from collections import defaultdict

from django.conf import settings

import isodate
from apiclient import discovery
import deferred_manager

from greenday_core.models import YouTubeVideo, Video

from .task_helpers import auto_view
from .indexers import index_all


class YouTubeClient(object):
    """
        Provides functionality to get video data from YouTube in order to
        update the Montage
        :class:`greenday_core.models.video.YouTubeVideo <greenday_core.models.video.YouTubeVideo>`
        objects
    """
    def __init__(self, *args, **kwargs):
        """
            Create the client and builds the discovery client
        """
        super(YouTubeClient, self).__init__(*args, **kwargs)
        self.api_key = settings.OAUTH_SETTINGS['api_key']
        self.client = self.get_discovery_client()

    def get_discovery_client(self):
        """
            Builds a discovery API client for the YouTube Data API V3
        """
        return discovery.build(
            'youtube', 'v3', developerKey=self.api_key)

    def get_video_data(self, youtube_ids):
        """
            Gets YT videos and maps to a dict with the same field names as the
            YouTubeVideo table
        """
        assert len(youtube_ids) <= 50,\
        "can request a maximum of 50 youtube videos"

        resp = self.client.videos().list(
            id=",".join(youtube_ids),
            part='snippet,contentDetails,recordingDetails'
        ).execute()

        raw_videos = resp.get("items", [])

        yt_videos = {}
        channel_map = defaultdict(list)

        for video in raw_videos:
            yt_id = video['id']

            recorded_date = lat = lon = None
            if 'recordingDetails' in video:
                raw_rec_date = video['recordingDetails'].get('recordingDate')
                if raw_rec_date:
                    recorded_date = isodate.parse_datetime(raw_rec_date)

                loc = video['recordingDetails'].get('location')
                if loc:
                    try:
                        lat = float(loc.get('latitude'))
                        lon = float(loc.get('longitude'))
                    except TypeError:
                        pass

            channel_id = video['snippet']['channelId']

            if channel_id:
                channel_map[channel_id].append(yt_id)

            yt_videos[yt_id] = {
                'name': video['snippet']['title'],
                'latitude': lat,
                'longitude': lon,
                'notes': video['snippet']['description'],
                'publish_date': isodate.parse_datetime(
                        video['snippet']['publishedAt']),
                'recorded_date': recorded_date,
                'channel_id': channel_id,
                'channel_name': video['snippet']['channelTitle'],
                'duration': int(isodate.parse_duration(
                    video['contentDetails']['duration']).total_seconds())
            }

        return yt_videos

    def update_videos(self, youtube_videos):
        """
            Updates the data on giving YouTubeVideo objects
        """
        video_data = self.get_video_data([v.youtube_id for v in youtube_videos])

        for yt_video in youtube_videos:
            data = video_data.get(yt_video.youtube_id)
            if not data:
                yt_video.set_as_missing()
            else:
                for k, v in data.items():
                    setattr(yt_video, k, v)

        return youtube_videos

    def update_or_create_videos(self, youtube_ids):
        """
            Takes a list of youtube IDs and yields saved
            YouTubeVideo instances
        """
        video_data = self.get_video_data(youtube_ids)

        yt_videos = []
        for yt_id, data in video_data.items():
            yt_video, created = YouTubeVideo.objects.update_or_create(
                    youtube_id=yt_id, defaults=data)
            yt_videos.append(yt_video)

        return yt_videos


@auto_view
def update_videos(video_ids):
    """
        Updates the given YouTubeVideo objects with fresh YouTube data
    """
    logging.info("Updating YouTubeVideo IDs %s", ",".join(map(str, video_ids)))

    yt_videos = YouTubeVideo.objects.in_bulk(video_ids)

    client = YouTubeClient()
    client.update_videos(yt_videos.values())

    for yt_video in yt_videos.values():
        yt_video.save()


@auto_view
def update_all_videos():
    """
        Updates all videos with YouTube data
    """
    batch_size = 50

    qs = (
        YouTubeVideo.objects
        .order_by('modified')
        .values_list('pk', flat=True)
    )

    start = 0
    video_ids = ()
    while len(video_ids) == batch_size or start == 0:
        video_ids = list(qs[start:start+batch_size])
        deferred_manager.defer(
            update_videos,
            video_ids,
            _queue='update-youtube-video-data')

        if settings.SEARCH_INDEXING:
            project_video_ids = list(
                Video.objects.filter(
                    youtube_video_id__in=video_ids).values_list('pk', flat=True)
            )

            deferred_manager.defer(
                index_all,
                model_type="Video",
                object_ids=project_video_ids,
                _queue='search-indexing')

        start += batch_size

