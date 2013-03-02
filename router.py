import logging
import webapp2

from controllers.blog_controller import BlogController

from google.appengine.ext import ereporter

from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext import blobstore
from google.appengine.api import users

from models.models import Image

ereporter.register_logger()


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        # try:
            upload = self.get_uploads()[0]

            image = Image(author=users.get_current_user().user_id(), blob_key=upload.key())

            image_key = image.put()

            self.redirect('/admin/nameupload/%s' % image_key)


class ViewPhotoHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, photo_key):
        if not blobstore.get(photo_key):
            self.error(404)
        else:
            self.send_blob(photo_key)


application = webapp2.WSGIApplication([

    ('/imagestore/([^/]+)?', ViewPhotoHandler),
    ('/admin/uploaded', UploadHandler),
    ('/.*',           BlogController)

], debug=True)
