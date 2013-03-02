from google.appengine.api import users
from google.appengine.api import images
from google.appengine.ext import blobstore

from models.utils import Utils
from models.models import Image
from models.models import Group
from models.models import Content
from models.models import ContentVersion
from models.user import User


class RouteAdmin():
    """ The none api based admin router """

    def __init__(self, req, conf):
        self._req = req
        self._conf = conf

        
    def get(self, par):

        # Important app.yaml enforces that to get here you must be a google app admin
        if self._is_admin():
            routes = [
                {"r": "/admin/nameupload/(.*)",       "f": self._get_name_upload},
                {"r": "/admin/upload",                "f": self._get_upload},
                {"r": "/admin/(.*)",                  "f": self._get_default},
                {"r": "/admin",                       "f": self._get_root},
            ]
                
            if self._req.route(routes):
                return True
        else:
            self._req.respond_unauth()
            return True

        return False


    def post(self, par):

        # Important app.yaml enforces that to get here you must be a google app admin
        if self._is_admin():
            routes = [
                {"r": "/admin/nameupload/(.*)",       "f": self._post_name_upload},     # name the uploaded image
                {"r": "/admin/newcontent",            "f": self._post_new_content},     # new content
                {"r": "/admin/newgroup",              "f": self._post_new_group},     
            ]
                
            if self._req.route(routes):
                return True
        else:
            self._req.respond_unauth()
            return True

        return False

    
    def _get_name_upload(self, par):

        image = Image.get(par[0])
        image.serving_url = images.get_serving_url(image.blob_key, 640)
        image.put()

        self._respond(["nameupload"], image)

    
    def _get_upload(self, par):
        upload_url = blobstore.create_upload_url('/admin/uploaded')   # this goes to the upload handler
        
        self._respond(["upload"], None, {"upload_url": upload_url})


    def _get_default(self, par):

        obj = {}
        obj['images'] = Image.all().order("-date").fetch(20)
        obj['groups'] = Group.all()

        self._respond(par, obj)

    
    def _get_root(self, par):
        return self._req.redirect(path="/blog")

    
    def _post_name_upload(self, par):
    
        image = Image.get(par[0])
        image.title = self._req.par('image_title')
        image.tag = self._req.par('image_tags')
        image.put()

        self._req.redirect(path='/admin/nameupload/' + str(image.key()))


    def _post_new_content(self, par):
        
        user = User(self._req.sesh())
        person = user.get_sesh_person()

        ut = Utils()
        key = ut.cleanUserName(self._req.par('cid'))

        # create the content record, by unique key - !important - replaces existing key - warn user?
        content = Content(key_name=key)
         
        content.status = 'draft'
        content.author = person
        groupname = self._req.par('cgroup')
        content.group = Group.get_by_key_name(groupname)

        # create a new version
        contentver = ContentVersion()
        
        # some defaults
        contentver.title = self._req.par('ctitle')
        contentver.content = '<p>Placeholder for the body of your Article</p>' 
        contentver.summary = '<p>Placeholder for the article summary</p>' 
        
        # have to put to get a reference
        contentver.put()

        # upate versions on this content
        content.current = contentver
        content.editing = contentver
        content.put()

        # link to my parent - in fact shouldnt I have used parents (but then sharding wont be an issue for a few, even 100's of, articles)
        contentver.mycontent = content
        contentver.put()

        # and redirect to the new content
        return self._req.redirect(path=self._conf.BLOG + '/' + groupname + '/' + key)


    def _post_new_group(self, par):

        ut = Utils()
        key = ut.cleanUserName(self._req.par('cid'))
        group = Group(key_name=key)
        group.title = self._req.par('ctitle')
        group.put()

        return self._req.redirect(path=self._conf.BLOG + '/' + key)


    def _respond(self, par, obj={}, opt={}):
        opt['return_url'] = self._req.sesh().return_url()
        self._req.draw(path='admin/admin-' + par[0], obj=obj, opt=opt)


    def _is_admin(self):
        """ check for admin rights of this user 
            1. in the current session object
            2. then in the curretn google user
            
        """
        
        # if already authed as an admin - then must have the person record already so carry on
        if self._req.sesh().can_edit():
            return True
        
        # not currently an admin and hit an admin url so check or get gae admin user
        google_user = users.get_current_user()
        
        # no google user then revert to normal redirect back to blog
        if not google_user: 
            return False

        # if we got here then we must have good google admin but no exisstng admin session    
        
        # make sure this google admin is given an authenticated admin session
        self._req.sesh().set_authenticated(google_user.user_id(), 'admin', google_user.email())
        
        # create user
        user = User(self._req.sesh())
        user.create_new_user(google_user.user_id(), 'admin', google_user.email())

        return True
        
        