import logging
import cloudstorage as gcs
from google.appengine.ext import blobstore, db
from google.appengine.api import images

from django.conf import settings


class UploadedImage(db.Model):
    """
        Datastore model to represent an image in Montage
    """
    gcs_file_path = db.StringProperty(required=True)
    serving_url = db.StringProperty()
    uploaded_for_type = db.StringProperty(required=True)
    uploaded_for_id = db.IntegerProperty()


class ImageManager(object):
    """
        Provides functionality to upload, retrieve and purge images in GCS
    """
    def __init__(self, model_type):
        """
            Creates the manager
        """
        self.model_type = model_type
        self.gcs_bucket = self.get_gcs_bucket()

    def get_gcs_bucket(self):
        return "gd-{0}-images".format(self.model_type)

    def write_image_to_gcs(
            self, img, filename, buffer_size=8*256*1024, model_id=None):
        """
            Write an image to GCS and return the blobkey and
            serving url

            img: img bytes as string or stream
        """
        gcs_file_path = self.get_gcs_file_path(filename)
        logging.info(gcs_file_path)

        with gcs.open(
                filename=gcs_file_path,
                mode='w',
                content_type='image/jpg') as f:
            if isinstance(img, basestring):
                f.write(img)
            else:
                buf = img.read(buffer_size)
                while buf:
                    f.write(buf)

                    if len(buf) == buffer_size:
                        buf = img.read(buffer_size)
                    else:
                        buf = None

        # Blobstore API requires extra /gs to distinguish against blobstore
        # files.
        blobstore_filename = '/gs' + gcs_file_path

        blob_key = blobstore.create_gs_key(blobstore_filename)

        # Strip the http: from the beginning to make the url protocol-less
        image_url = images.get_serving_url(blob_key)[5:]

        ds_image = UploadedImage(
            gcs_file_path=gcs_file_path,
            serving_url=image_url,
            uploaded_for_type=self.model_type,
            model_id=model_id)
        ds_image.put()
        return blob_key, image_url

    def get_gcs_file_path(self, filename):
        """
            Gets the full GCS path of the file
        """
        return "/{bucket}/{bucket_folder}/{name}".format(
            bucket=settings.GCS_BUCKET,
            bucket_folder=self.gcs_bucket,
            name=filename)

    def update_linked_image_for_model(self, serving_url, model_id):
        """
            Gets the image's object in the datastore using its serving_url
            and adds the ID to it

            If the model already has an image linked. Remove it.
        """
        image_q = UploadedImage.all()
        image_q.filter("uploaded_for_type =", self.model_type)
        image_q.filter("uploaded_for_id =", model_id)

        for existing_image in image_q:
            if existing_image.serving_url == serving_url:
                continue

            try:
                gcs.delete(existing_image.gcs_file_path)
            except Exception as e:
                logging.exception(e)
            existing_image.delete()

        if serving_url:
            serving_image_q = UploadedImage.all()
            serving_image_q.filter("serving_url =", serving_url)
            image = serving_image_q.get()
            if image:
                image.uploaded_for_id = model_id
                image.put()

            return bool(image)


    def delete_linked_image_for_model(self, model_id):
        """
            Deletes the image linked to the model
        """
        image_q = UploadedImage.all()
        image_q.filter("uploaded_for_type =", self.model_type)
        image_q.filter("uploaded_for_id =", model_id)

        for existing_image in image_q:
            try:
                gcs.delete(existing_image.gcs_file_path)
            except Exception as e:
                logging.exception(e)
            existing_image.delete()
