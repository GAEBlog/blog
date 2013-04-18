import json
import logging
import datetime

from google.appengine.api import images

from models.user import User
from models.models import Image
from models.models import Content
from models.models import ContentVersion
from models.search import BlogSearch
from models.models import clone_entity


class RouteApi():
    """ the api router, our routes are split into those needing editor rights or not """

    def __init__(self, req, conf):
        self._req = req
        self._conf = conf


    def post(self):

        logging.debug(self._req.body())
        self._pl = json.loads(self._req.body())

        routes = [            
            {"r": self._conf.BLOG + "/fb_session(.*)",             "f": self._post_fb_session}
        ]

        editor_routes = [
            {"r": self._conf.BLOG + "/raptor-save(.*)",            "f": self._post_raptor_save},
            {"r": self._conf.BLOG + "/update-images(.*)",          "f": self._post_update_images},
            {"r": self._conf.BLOG + "/summary-save(.*)",           "f": self._post_summary_save},
            {"r": self._conf.BLOG + "/createdate(.*)",             "f": self._post_createdate},
            {"r": self._conf.BLOG + "/newversion(.*)",             "f": self._post_new_version},
            {"r": self._conf.BLOG + "/changeedit(.*)",             "f": self._post_change_edit},
            {"r": self._conf.BLOG + "/changecurrent(.*)",          "f": self._post_change_current},
            {"r": self._conf.BLOG + "/changestatus(.*)",           "f": self._post_change_status}
        ]

        # route the editor requests
        if self._req.route(routes):
            return True

        # route the editor requests
        if self._req.sesh().can_edit():
            if self._req.route(editor_routes):
                return True
            else:
                self._req.respond_unauth()
        
        return False
    

    def get_session(self, par):
        obj = {
            "authenticated": self._req.sesh().authorised(),
            "user_name": self._req.sesh().user_name()
        }
        self._req.draw(path="", obj=obj)

    
    def _update_search_index(self, parcontent):
        search = BlogSearch()

        search.insert_document(search.create_document(
                        parcontent.key().name(),
                        parcontent.sortdate,
                        parcontent.author.displayname,   
                        parcontent.current.content,
                        parcontent.current.title,
                        parcontent.group.title
                    ))


    def _post_raptor_save(self, par):

        search = BlogSearch()

        for cid, cc in self._pl.items():
            logging.debug(cid)
            parcontent = Content.get_by_key_name(cid)
            content = parcontent.editing
        
            for eid, e in cc.items():
                ee = e.strip()
                logging.debug(eid)
                logging.debug(ee)
        
                if eid == 'ed_title':
                    content.title = ee
                if eid == 'ed_banner':

                    if ee =="":
                        content.banner = None
                    else:
                        content.banner = ee
                if eid == 'ed_content':
                    content.content = ee
                    if content.summary == "<p>Placeholder for the article summary</p>":             # still the default
                        paras = ee.split('<p>');
                        if len(paras) > 2:
                            content.summary = '<p>' + paras[1] + '<p>' + paras[2]
                        elif len(paras) > 1:
                            content.summary = '<p>' + paras[1]
                
                content.put()

                # add the update if published to search index
                if parcontent.status == 'published':
                    self._update_search_index(parcontent)

        # respond with a good code
        self._req.draw_code()


    def _post_update_images(self, par):
        
        key = self._pl['key']
        which = self._pl['which']
        url = self._pl['url']
        parcontent = Content.get_by_key_name(key)
        content = parcontent.editing
        
        if which == "mainimage":
            image = Image.get_by_id(int(url))
            
            content.mainimage = image
            content.imagepath = None   # so reset the path    

            if content.thumb == None:
                content.thumb = images.get_serving_url(image.blob_key, 150)

        elif which == "thumb":
            content.thumb = url

        elif which == "reset_thumb":
            image = content.mainimage
            if image:
                content.thumb = images.get_serving_url(image.blob_key, 150) 

        elif which == "main_url":
            content.imagepath = url   # so reset the path    

        elif which == "thumb_url":
            content.thumb = url   # so reset the path    
            
        content.put()

        # respond with a good code
        self._req.draw_code()


    def _post_summary_save(self, par):

        for cid, cc in self._pl.items():
            logging.debug(cid)
            for eid, ee in cc.items():
                parcontent = Content.get_by_key_name(eid)
                content = parcontent.editing
                if cid == 'ed_summary':
                    content.summary = ee
                
                content.put()

        # respond with a good code
        self._req.draw_code()


    # this is an api post
    def _post_createdate(self, par):
        
        content = Content.get_by_key_name(self._pl['id'])
        logging.debug(self._pl['createdate'])
        content.sortdate =  datetime.datetime.strptime(self._pl['createdate'], '%m/%d/%Y')
        content.put()
        
        #  send back the new formatted date
        obj = {
            "createdate": content.sortdate.strftime('%e %b %Y')
        }
        
        self._req.draw_code(obj=obj)


    def _post_new_version(self, par):
        
        key = self._pl['id']
        content = Content.get_by_key_name(key)

        new = clone_entity(content.current)
        new.before_put()
        new.put()
        
        content.editing = new
        content.put()

        # respond with a good code
        self._req.draw_code()


    def _post_change_edit(self, par):
        
        key = self._pl['id']
        ver = int(self._pl['verid'])

        content = Content.get_by_key_name(key)
        contentver = ContentVersion.get_by_id(ver)

        content.editing = contentver
        content.put()

        # respond with a good code
        self._req.draw_code()


    def _post_change_current(self, par):
    
        key = self._pl['id']
        ver = int(self._pl['verid'])

        content = Content.get_by_key_name(key)
        contentver = ContentVersion.get_by_id(ver)

        content.current = contentver
        content.put()

        # respond with a good code
        self._req.draw_code()

    
    def _post_change_status(self, par):

        status = self._pl['stat']

        key = self._pl['id']
        content = Content.get_by_key_name(key)
        content.status = status
        content.put()

        if status == 'published':
            self._update_search_index(content)

        # respond with a good code
        self._req.draw_code()

    
    def _post_fb_session(self, par):
        """ the client sent us a notification after the FB js authentication ocured """
                
        # so take not that an authentication occured
        user = User(self._req.sesh())
        user.auth_event('fb', self._pl)

        obj = {
            "authenticated": self._req.sesh().authorised(),
            "user_name": self._req.sesh().user_name()
        }

        # respond with a good code
        self._req.draw_code(obj=obj)

