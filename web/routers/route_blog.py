import re
import json
import time
import logging
import datetime

import email.utils as emailutils

from google.appengine.api import memcache
from google.appengine.ext import blobstore

from widgets import Widgets
from models.utils import Utils
from models.models import Image
from models.models import Group
from models.emails import Emails
from models.models import Content
from models.models import ContentVersion
from models.search import BlogSearch


class RouteBlog():

    def __init__(self, req, conf):
        self._req = req
        self._conf = conf
        self._obj = {}

        if self._req.ext() == 'xml':
            self._PAGESIZE = self._conf.RSS_PAGE
        else:
            self._PAGESIZE = self._conf.BLOG_PAGE

        
    def get(self, par):

        # all blog and static pages are cacheable
        if self._check_get_from_cache():
            return True

        self.widgets = Widgets(self, self._conf)

        # get the groups
        self._obj['groups'] = Group.all()

        routes = [
            # {"r": self._conf.BLOG + "/widget/(.*)",  "f": self._get_widget},
            {"r": "/rssfeed(.*)",                      "f": self._force_rss},
            {"r": self._conf.BLOG + "/search\?q=(.*)", "f": self._get_blog_search},
            {"r": self._conf.BLOG + "/(.*)/(.*)\?",    "f": self._get_blog_single},
            {"r": self._conf.BLOG + "/(.*)/(.*)",      "f": self._get_blog_single},
            {"r": self._conf.BLOG + "/(.*)\?",         "f": self._get_blog_group},
            {"r": self._conf.BLOG + "/(.*)",           "f": self._get_blog_group},
            {"r": self._conf.BLOG + ".*",              "f": self._get_blog},
            {"r": "/(.*)\?",                           "f": self._get_static},
            {"r": "/(.*)",                             "f": self._get_static}
        ]
            
        if self._req.route(routes):
            # cache the return url        
            self._req.sesh().set_return_url(self._req.spath())
            self._req.sesh().save();
            return True
        
        return False


    def post(self, par):
        routes = [            
            {"r": "/contact-form(.*)",             "f": self._contact_email}
        ]
        if self._req.route(routes):
            return True
        return False
        

    def _contact_email(self, par):
        emails = Emails(self._req)
        emails.contact()
        # now return the static reply page
        self.get(par)


    # def _aspx_redirect(self):
    #     """ check the last part of the path for any stored redirects """
    #     ppart = self._req.pathel(self._req.length()-1, encode=True)
    #     logging.debug(ppart)

    #     q = Redirect.all().filter("fromurl = ", ppart)
    #     np = q.get()
    #     if np:
    #         newp = self._req.path()[:-1]
    #         newp.append(np.tourl)
    #         self._req.redirect(str("/" + "/".join(newp)))
    #     else:
    #         self._req.redirect(self._req.spath())        # some specific redirects        


    def _check_cache_exception(self):
        if re.search("/search\?q=", self._req.spath(), re.IGNORECASE):
            return True
        
        return False


    def _check_get_from_cache(self):
        
        if self._check_cache_exception():
            return False

        if not self._conf.CACHE:
            return False
            
        # only get fom cache if not editng
        if self._req.sesh().can_edit():
            return False

        logging.debug("lookin in cache: " + self._req.get_cache_key())
        data = memcache.get(self._req.get_cache_key())
        if data is None:
            logging.debug("cache miss")
            return False
        
        logging.debug("cache hit")
        self._req.blast(data)

        if self._req.ext() == 'xml':
            self._req.set_header('Content-Type', 'application/rss+xml')

        return True     # got it form cache


    def get_image(self, par):
        """ called directly from main get router """
        try:
            iid = int(par[0]);
            img = Image.get_by_id(iid)
            if img:
                self._req.redirect(str(img.serving_url))
            else:
                self._req.notfound()
        except:
            self._req.notfound()


    def _force_rss(self, par):
        """ if some urls without a .xml extension are requesting rss """
        self._PAGESIZE = self._conf.RSS_PAGE
        self._get_blog([], xml=True)


    def _get_blog_single(self, par):

        ut = Utils()
        self._build_widgets_single()

        o = self._obj
        # if it is the single blog view and the user is an editor then load up the images for the image select box
        if self._req.sesh().can_edit():
            o['images'] = Image.all().order("-date").fetch(self._conf.IMAGES_VIEWER_COUNT)

        content = Content.get_by_key_name(par[1])
        if content:
            o['data'] = self.copy_bits(content)
        
            # versions for admin - perhaps optimise this out with a isAdmin clause
            o['data'].otherversions = content.contentversion_set
            ov = []
            for c in content.contentversion_set:
                c.nicetime = c.createtime.strftime('%e %b %Y - %H:%M:%S')
                ov.append(c)
            o['data'].otherversions = ov
            
            # what to put in the meta description - needed for singe blog post only
            if content.current.summary:
                o['data'].metadesc = ut.strip_tags(content.current.summary)
            else:
                o['data'].metadesc = o['data'].title
     
            # no paging controls - for a single blog
            o['page'] = {}
            
        else:
            return self._req.notfound()

        self._respond(path='blog-single', obj=self._obj)


    def _get_blog_group(self, par):
        """ all blog articles in the group """

        group = Group.get_by_key_name(par[0])
        if group:
            q = group.content_set
            self._obj['title'] = group.title
            self._get_blog_list(q)
        else:
            return self._req.notfound()


    def _get_blog(self, par, xml=False):
        """ all blog articles """

        q = Content.all();
        self._obj['title'] = self._conf.BLOG_TITLE
        self._get_blog_list(q, xml)


    def _get_blog_search(self, par, xml=False):
        """ all blog articles matching search result """
        self._curpage = int(self._req.par('p', default_value = 1))

        self._obj['title'] = "Search"

        search = BlogSearch()
        result = search.get(par[0])
        
        newest = datetime.datetime.fromtimestamp(0)
        self._obj['data'] = []

        count = 0
        for r in result:
            count = count + 1

            logging.debug(r.doc_id)

            c = Content.get_by_key_name(r.doc_id)
            d = self.copy_bits(c)

            self._obj['data'].append(d)
            
            if c.sortdate > newest:
                newest = c.sortdate

        # fill in all our widgets        
        self._build_widgets_list(count, None)


        self._respond(path='blog-search', obj=self._obj, xml=xml, search={"term":par[0], "count": count})


    def _get_blog_list(self, q, xml=False):

        self._curpage = int(self._req.par('p', default_value = 1))

        self._obj['data'] = []

        q.filter('ctype =', 'blog').order("-sortdate");

        if not self._req.sesh().can_edit():
            q.filter('status =', 'published')
        
        # fill in all our widgets        
        self._build_widgets_list(q.count(), q)

        # to stick in the rss
        newest = datetime.datetime.fromtimestamp(0)
        
        for c in q.fetch(self._PAGESIZE, offset=(self._curpage-1) * self._PAGESIZE):
            d = self.copy_bits(c)

            d.rssdate = emailutils.formatdate(time.mktime(c.sortdate.timetuple()), usegmt=True)
            
            self._obj['data'].append(d)

            if c.sortdate > newest:
                newest = c.sortdate

        # format in the rss standard format
        self._obj['rssrecentdate'] = emailutils.formatdate(time.mktime(newest.timetuple()), usegmt=True)
           
        self._respond(path='blog', obj=self._obj, xml=xml)


    def _build_widgets_single(self):
        # create the widgets container
        self._obj['widge'] = {}
        self._obj['widge']['popular'] = self.widgets.popular()


    def _build_widgets_list(self, count, q):

        self._build_widgets_single()
        self._obj['page'] = self.widgets.pagination(count)
        if q:
            self._obj['slider'] = self.widgets.slider(q)

    
    def _get_static(self, par):
        """ all other none blog pages """
        try:
            self._respond(path="pages/" + par[0])
        except:
            return False    # this will triger the not found

        return True
        

    # def _get_widget(self, par):
        
    #     # simply return widget content
    #     content = Content.get_by_key_name(par[0])
    #     if content:
    #         return self.response.write(content.current.content)
    #     else:
    #         return self.redirect('/404')  # respond with a 404 not ging to the 404 page


    def copy_bits(self, c):
        """ used bt the slider widget and the blog list to copy content bits to the contentver for display"""

        if self._req.sesh().can_edit():
            d = c.editing
        else:
            d = c.current

        d.keyname = c.key().name()
        d.group = c.group
        d.author = c.author.displayname

        d.ctype = c.ctype
        d.status = c.status

        d.nicedate = c.sortdate.strftime('%e %b %Y')
        
        # use hard coded imagepath, or the mainimage's url
        if not d.imagepath:
            if d.mainimage:
                d.imagepath = d.mainimage.serving_url
        return d


    def _respond(self, path, obj={}, xml=False, search={}):
        """ draw the html and add it to the response then decide to add to or flush the cashe if admin"""
        
        opt = {
            "appname": self._conf.APP_NAME,
            "blog_name": self._conf.BLOG,
            "fb_app_id": self._conf.FB_APP_ID,
            "can_edit": self._req.sesh().can_edit(),
            "authed": self._req.sesh().authorised(),
            "authfor": self._req.sesh().user_name(),
            "url": self._req.spath(query=False),
            "search": search 
        }

        if self._req.ext() == 'xml' or xml:
            path = "rss"
            self._req.set_header('Content-Type', 'application/rss+xml')

        html = self._req.draw(path=path, obj=obj, opt=opt)

        # if an admin hits the page then clear this out of the cache
        if self._conf.CACHE:
            # if an admin hits the page then clear this out of the cache
            if self._req.sesh().can_edit():
                memcache.delete(self._req.get_cache_key())
            else:
                if not memcache.add(self._req.get_cache_key(), html, 3600):   #3600 = 1 hour 
                    logging.error("MEMCACHE MISTAKE")
