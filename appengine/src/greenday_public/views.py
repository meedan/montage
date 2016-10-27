"""
    Views served by the public app
"""
import os
import string
import random
import logging

from django.views.generic.base import TemplateView, View
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse, HttpResponse

from greenday_core.youtube_thumbnails_cache import YTThumbnailsCache
from greenday_core.image_manager import ImageManager

from .auth_utils import auth_user


# Base views
class MasterView(TemplateView):
    """ Serves the Montage app """

    def get_context_data(self, *args, **kwargs):
        context = super(MasterView, self).get_context_data(*args, **kwargs)
        context['DEBUG'] = settings.TEMPLATE_DEBUG
        context['STATIC_URL'] = settings.STATIC_URL
        context['ANALYTICS_ID'] = settings.ANALYTICS_ID
        context['ENV'] = settings.ENVIRONMENT
        context['HOST_URL'] = self.request.get_host()
        context['OAUTH_SETTINGS'] = settings.OAUTH_SETTINGS
        context['CHANNELS_API_BASE'] = settings.CHANNELS_API_BASE
        context['API_BASE'] = settings.API_BASE
        return context


index_view = MasterView.as_view(template_name='index.html')


class Error404View(MasterView):
    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context, status=404)


err_404_view = auth_user(Error404View.as_view(template_name='index.html'))


class ImageUploadView(View):
    """
        Handles image uploads for project and tag images
    """
    def post(self, request):
        """
            Upload handler
        """
        name = self.get_file_name(request)

        image_type = request.GET.get('type')
        assert image_type in ('project', 'tag',)

        manager = ImageManager(image_type)

        try:
            _, image_url = manager.write_image_to_gcs(
                request,
                name,
                model_id=request.GET.get('id'))
        except Exception as e:
            logging.error(e)
            return JsonResponse({
                "message": unicode(e)
            }, status=500)

        return JsonResponse({
            "url": image_url
        })

    def get_file_name(self, request):
        """
            Gets a random file name for the image
        """
        ext = os.path.splitext(request.GET.get('name'))[1]
        name = ''.join(random.choice(
            string.ascii_lowercase + string.digits) for _ in range(64))

        return name + ext

image_upload_view = auth_user(csrf_exempt(ImageUploadView.as_view()))


class YTThumbnailView(View):
    """
        Serves and caches video thumbnails from YouTube
    """
    max_fetch_retries = 5
    gcs_bucket = 'gd-yt-thumbs'

    @cache_control(public=True, max_age=60**2*24)
    def get(self, request):
        """
            Gets the thumbnail image
        """
        yt_id = request.GET.get('id')
        at_milliseconds = request.GET.get('ats')

        yt_thumb_cache = YTThumbnailsCache(yt_id)
        image_content, success = yt_thumb_cache.fetch(at_milliseconds)

        return HttpResponse(
            image_content,
            content_type="image/jpeg",
            status=200 if success else 404)


yt_thumbnail_view = YTThumbnailView.as_view()
