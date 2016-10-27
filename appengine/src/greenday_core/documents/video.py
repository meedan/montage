"""
    Search API document for Video
"""
from google.appengine.api import search as search_api

from django.utils import timezone
from django.db.models import Count
from search import indexes, fields
from search.indexers import startswith

from ..models import TimedVideoComment


class VideoDocument(indexes.DocumentModel):
    """
        Appengine Search API document for Video
        model.
    """
    id = fields.AtomField()
    name = fields.TextField()
    notes = fields.TextField()
    project_id = fields.AtomField()
    channel_id = fields.AtomField()
    channel_name = fields.AtomField()
    publish_date = fields.DateField()
    recorded_date = fields.DateField()
    tag_ids = fields.TextField()
    collection_ids = fields.TextField()
    n_grams = fields.TextField()
    youtube_id = fields.AtomField()
    duration = fields.IntegerField()
    location = fields.GeoField()
    has_location = fields.AtomField()
    all_comment_text = fields.TextField()

    private_to_project_ids = fields.TextField()

    @classmethod
    def from_instance(cls, video):
        values = {
            'name': video.youtube_video.name,
            'notes': video.youtube_video.notes,
            'doc_id': str(video.pk),
            'channel_id': unicode(video.youtube_video.channel_id),
            'project_id': unicode(video.project_id),
            'id': unicode(video.id),
            'youtube_id': unicode(video.youtube_video.youtube_id),
            'channel_name': unicode(video.youtube_video.channel_name),
            'duration': int(video.youtube_video.duration)
        }

        if video.location_overridden:
            latitude = video.latitude
            longitude = video.longitude
        else:
            latitude = video.youtube_video.latitude
            longitude = video.youtube_video.longitude

        has_location = latitude is not None and longitude is not None
        values['has_location'] = str(int(has_location))

        if has_location:
            values['location'] = search_api.GeoPoint(
                latitude, longitude)
        else:
            values['location'] = search_api.GeoPoint(
                0.0, 0.0)

        if video.youtube_video.publish_date:
            values['publish_date'] = timezone.make_naive(
                video.youtube_video.publish_date, timezone.utc)

        if video.recorded_date_overridden:
            recorded_date = video.recorded_date
        else:
            recorded_date = video.youtube_video.recorded_date

        if recorded_date:
            values['recorded_date'] = timezone.make_naive(
                recorded_date, timezone.utc)

        values['tag_ids'] = " ".join(
            map(
                str,
                video.videotags
                .annotate(num_instances=Count('tag_instances'))
                .filter(num_instances__gt=0)
                .values_list('project_tag_id', flat=True)
            )
        )

        values['collection_ids'] = " ".join(
            map(str, video.collections.all().values_list('id', flat=True))
        )

        values['all_comment_text'] = " ".join(
            TimedVideoComment.objects
            .filter(tagged_object_id=video.pk)
            .values_list('text', flat=True)
        )

        if video.project.is_private:
            values['private_to_project_ids'] = unicode(video.project_id)

        values['n_grams'] = cls.make_ngrams(video.youtube_video.name)
        return cls(**values)

    @classmethod
    def make_ngrams(cls, string):
        """
            Class method to generate ngrams based on the passed string
        """
        return " ".join(ngram for ngram in startswith(string[:100]))
