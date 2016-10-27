"""
    Views to export data
"""
import endpoints
from protorpc import message_types
from google.appengine.api import users

from django.http import (
    HttpResponseBadRequest, HttpResponse
)
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View
from greenday_core.constants import EventKind

from greenday_core.models import Project, ProjectTag, VideoTag, TimedVideoComment
from greenday_core.utils import UnicodeWriter
from greenday_core.kml_utils import KmlCreator
from greenday_core import eventbus

from .auth_utils import auth_user

from greenday_api.api import (
    BaseAPI,
    greenday_api,
    greenday_method,
    auth_required,
    add_order_to_repeated
)

class BaseExportView(View):
    """
        Generic view to export data
    """
    fields = None

    @csrf_exempt
    def dispatch(self, request, **kwargs):
        """
            Override disptach to validate export format and set user.

            While generally not good practice, we set CSRF as exempt
            because no POST requests handled by this view modify any
            server side data.
        """
        self.user = users.get_current_user()
        self.format = request.POST.get('format', 'csv').lower()
        eventbus.publish_appevent(
            kind=EventKind.USEREXPORTEDVIDEOS,
            object_id=request.user.pk,
            project_id=kwargs['project_id'],
            user=request.user,
            meta=self.format
        )

        if self.format not in ('csv', 'kml'):
            return HttpResponseBadRequest("Format not valid")

        return super(BaseExportView, self).dispatch(request, **kwargs)

    def post(self, request, **kwargs):
        """
            Generic POST handler which picks the export process.

            We would prefer to use a GET HTTP request here, as we aren't
            modifying any data server side. However to avoid exceeding the
            URL limit imposed by App Engine we use POST to workaround this
            and send video IDs in the payload.
        """
        if self.format == 'csv':
            return self.get_csv_response()

        if self.format == 'kml':
            return self.get_kml_response()

    def create_response(self, content_type):
        """
            Helper method to create a response object with the correct headers
        """
        response = HttpResponse(content_type=content_type)
        file_name = self.request.POST.get('name') or self.get_file_name()

        if "." not in file_name:
            file_name += "." + self.format
        response['Content-Disposition'] = 'attachment; filename="%s"' % file_name
        return response

    def get_csv_response(self):
        """
            Gets the export data and creates a CSV response
        """
        response = self.create_response('text/csv')

        writer = UnicodeWriter(response)
        writer.writerow(self.fields)

        writer.writerows(self.get_rows())
        return response

    def get_kml_response(self):
        """
            Gets the export data and creates a KML response
        """
        response = self.create_response('application/vnd.google-earth.kml+xml')

        kml_creator = KmlCreator()

        clean_name = self.request.POST.get('clean_name')
        if clean_name:
            kml_creator.write_name(clean_name)

        for obj in self.get_data():
            self.write_kml(obj, kml_creator)

        kml_creator.write(response)

        return response

    def get_rows(self):
        """
            Cleans and yields rows to be suitable for output to CSV or other text format
        """
        data = self.get_data()

        for obj in data:
            row = []
            for field_name in self.fields:
                value = self.get_field_value(field_name, obj)
                if value is None:
                    value = ''
                row.append(unicode(value))

            yield row

    def get_file_name(self):
        """
            Gets the export file name
        """
        raise NotImplementedError

    def get_data(self):
        """
            Gets the data to export
        """
        raise NotImplementedError

    def get_field_value(self, field_name, obj):
        """
            Gets the value of `field_name` from `obj`. Can be overriden to clean values.
        """
        return getattr(obj, field_name)

    def write_kml(self, row, kml_creator):
        """
            Write a row of KML with a line of data
        """
        raise NotImplementedError

class VideoExportView(BaseExportView, BaseAPI):
    """
        Export video objects
    """
    fields = (
        "id",
        "youtube_id",
        "name",
        "channel_id",
        "channel_name",
        "playlist_id",
        "playlist_name",
        "duration",
        "latitude",
        "longitude",
        "notes",
        "publish_date",
        "recorded_date",
        "favourited",
        "created",
        "modified",
        "tag_count",
        "watch_count",
        "tags",
        "comments"
    )

    def post(self, request, **kwargs):
        """
            Override post() to verify vids are passed
        """
        vids = filter(None, request.POST.get('vids', '').split(','))
        self.vids = map(int, vids)
        if not self.vids:
            return HttpResponseBadRequest("No video ids")
        setattr(request, 'kwargs', {})

        return super(VideoExportView, self).post(request, **kwargs)

    def get_data(self):
        """
            Gets the video data
        """
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])

        if (not self.request.user.is_superuser and
                not project.is_assigned(self.request.user)):
            raise PermissionDenied

        videos = (
            project.videos
            .select_related("youtube_video")
            .prefetch_related("videocollectionvideos")
            .in_bulk(self.vids)
        )

        video_tags = VideoTag.objects.select_related(
            'project_tag__global_tag').filter(video_id__in=videos.keys())
        for video in videos.values():
            video.tag_list = []

        for vt in video_tags:
            videos[vt.video_id].tag_list.append(vt.project_tag.global_tag.name)

        return [videos[vid] for vid in self.vids if vid in videos]

    def get_field_value(self, field_name, obj):
        """
            Retrieves the flat video data from the ORM object
        """
        if field_name in (
                "name",
                "channel_name",
                "playlist_id",
                "playlist_name",
                "duration",
                "notes",
                "publish_date",):
            return getattr(obj.youtube_video, field_name)

        if field_name in ("latitude", "longitude",):
            if not obj.location_overridden:
                return getattr(obj.youtube_video, field_name)

        if field_name == "recorded_date":
            if not obj.recorded_date_overridden:
                return getattr(obj.youtube_video, field_name)

        if field_name == "tag_count":
            return obj.tag_instance_count

        if field_name == "tags":
            return u', '.join(u'"{}"'.format(tag) for tag in obj.tag_list)

        if field_name == "channel_id":
            return obj.channel_url

        if field_name == "youtube_id":
            return obj.youtube_url

        if field_name == "comments":
            all_comments = []
            root_comments= TimedVideoComment.get_root_comments_for(
                obj, prefetch_replies=True
            )
            for comment in root_comments:
                all_comments.append(comment)
                all_comments.extend(comment._reply_cache)
            return u', '.join(u'"{}"'.format(
                comment.text) for comment in all_comments)

        return super(VideoExportView, self).get_field_value(field_name, obj)

    def get_file_name(self):
        """
            Returns the default filename for the export
        """
        return "greenday-videos-{0}".format(
                timezone.now().strftime("%Y%m%d%H%M%S"))

    def write_kml(self, row, kml_creator):
        """
            Writes a KML row
        """
        lat, lon = row.get_latitude(), row.get_longitude()
        if lat is not None and lon is not None:
            kml_creator.write_placemark(
                row.youtube_video.name,
                row.youtube_video.notes,
                lat,
                lon)

video_export_view = auth_user(VideoExportView.as_view())


class ProjectTagExportView(BaseExportView):
    """
        Gets all tags on a project
    """
    fields = (
        'id',
        'name',
        'description',
        'image_url',
        'created',
        'modified',
        'instance_count',
        'parent_id'
    )

    def get_data(self):
        """
            Gets tag data
        """
        project = get_object_or_404(Project, pk=self.kwargs['project_id'])

        if (not self.request.user.is_superuser and
                not project.is_assigned(self.request.user)):
            raise PermissionDenied

        return (
            ProjectTag.get_tree()
            .filter(project=project)
            .select_related('global_tag')
            .with_taginstance_sum()
        )

    def get_field_value(self, field_name, obj):
        """
            Returns the value refered to by `field_name` in `obj`
        """
        if field_name in (
                'id',
                'name',
                'description',
                'image_url',):
            return getattr(obj.global_tag, field_name)

        if field_name == "instance_count":
            return obj.taginstance_sum

        if field_name == "parent_id":
            parent = obj.get_parent()
            return parent.global_tag_id if parent else None

        return super(
            ProjectTagExportView, self).get_field_value(field_name, obj)

    def get_file_name(self):
        """
            Gets a default filename for the export
        """
        return "greenday-project-{0}-tags-{1}".format(
                self.kwargs['project_id'],
                timezone.now().strftime("%Y%m%d%H%M%S"))


project_tag_export_view = auth_user(ProjectTagExportView.as_view())
