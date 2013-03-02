import logging
import webapp2

from config.conf import Config
from models.session import Session
from routers.request_router import RequestRouter



class RoutingController(webapp2.RequestHandler):

    def initialize(self, request, response):
        # call the base initialize
        webapp2.RequestHandler.initialize(self, request, response)

        self.conf = Config()
        
        # sets up a session member 
        self.sesh = self.parse_sesh()

        # sets up the request router
        self.req = RequestRouter(self.conf, self.sesh, request, response)

        self.upload_url = ''
        self.image_id = ''


    def parse_sesh(self):
        """Get the session form the cookie or the url"""

        sesh = Session()
        sid = ""

        # token in the request then use it
        sid = self.request.get(self.conf.URL_TOKEN_NAME, default_value="")
        # else get the token from the session
        if sid == "":
            if self.conf.TOKEN_NAME in self.request.cookies:
                sid = self.request.cookies[self.conf.TOKEN_NAME]


        if sid == "":
            # no sesion found so create one
            sesh.create()
        else:
            # got a session id so load from memcache or create a new one if its timed out
            sesh.load(sid)

        logging.debug("Session ID: " + sesh.id())
        self.response.headers['Set-Cookie'] = str('%s=%s;path=/;expires=Sat, 1-Jan-2050 00:00:00 GMT;'%(self.conf.TOKEN_NAME, sesh.id()))
        
        return sesh


    def head(self):
        return 


    def get(self):

        if self.req.isAPI():
            self._get_api()
        else:
            self._get_app()


    def post(self):    
        if self.req.isAPI():
            self._post_api()
        else:
            self._post_app()
