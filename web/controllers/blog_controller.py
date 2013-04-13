
import logging
import webapp2

from routing_controller import RoutingController

from routers.route_admin import RouteAdmin
from routers.route_blog import RouteBlog
from routers.route_oauth import RouteOauth
from routers.route_api import RouteApi

# logging.getLogger().setLevel(logging.DEBUG)


class BlogController(RoutingController):

    def _get_app(self):

        route_admin = RouteAdmin(self.req, self.conf)
        route_blog = RouteBlog(self.req, self.conf)
        # route_redirects = RouteRedirects(self.req, self.conf)
        route_oauth = RouteOauth(self.req, self.conf)

        routes = [
            # blog content and admin routes
            {"r": "/admin(.*)",                   "f": route_admin.get},
            {"r": self.conf.BLOG + "(.*)",        "f": route_blog.get},
            {"r": "/rssfeed(.*)",                 "f": route_blog.get},
            # utility routes
            {"r": "/i/(.*)",                      "f": route_blog.get_image},
            # {"r": "/umbraco(.*)",                 "f": self._get_ping},
            # {"r": "/land\?c=(.*)",                "f": route_redirects.landing},
            # {"r": "/camp\?fwd=(.*)",              "f": route_redirects.campaign},
            {"r": "/logout",                      "f": self._logout},
            # oauth routes
            {"r": "/oauthinit\?ch_pv=(.*)",       "f": route_oauth.init},
            {"r": "/verifyoauth\?ch_pv=(.*)",     "f": route_oauth.verify},
            {"r": "/(.*)",                        "f": route_blog.get},

        ]

        if self.req.route(routes):      # mathced
            return 

        return self.req.notfound()
        # didnt match any routes or one leaf function returned false

    
    def _get_api(self):

        logging.debug("GET apicall")

        route_api = RouteApi(self.req, self.conf)

        routes = [
            {"r": self.conf.BLOG + "/session",              "f": route_api.get_session},
        ]

        if self.req.route(routes):      # mathced
            return 

        return self.req.notfound()


    def _post_app(self):
        
        route_admin = RouteAdmin(self.req, self.conf)
        route_blog = RouteBlog(self.req, self.conf)

        routes = [
            {"r": "/admin(.*)",                   "f": route_admin.post},
            {"r": "/.*",                          "f": route_blog.post}
        ]

        if self.req.route(routes):      # mathced
            return 

        return self.req.notfound()


    def _post_api(self):
        
        logging.debug("POST apicall")

        route_api = RouteApi(self.req, self.conf)

        if route_api.post():
            return 

        return self.req.notfound()


    def _get_ping(self, par):
        self.response.write("I'm alive")


    def _logout(self, par):
        self.req.sesh().delete()
        self.req.set_header('Set-Cookie', str('%s=%s;path=/;expires='%(self.conf.TOKEN_NAME, '')))
        self.req.redirect(path=self.request.referer)

    
    def _send_tweet(self, provider, payload):
        return  # DEBUG 

        if self.sesh._authenticated_with == 'tw':

            auth_record = self.sesh._authenticated_pl

            logging.debug(auth_record)
            logging.debug(payload)

            client = oauth.TwitterClient(self.application_key, self.application_secret, "")

            url = "http://api.twitter.com/1/statuses/update.json"

            response = client.make_request(url, token=self.sesh._authenticated_pl['token'], secret=self.sesh._authenticated_pl['secret'], method=urlfetch.POST, additional_params=payload)

            logging.debug(response)

