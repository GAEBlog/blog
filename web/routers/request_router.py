import re
import urllib
import logging
import urlparse


from responders.responder_html import HTMLResponder
from responders.responder_json import JSONResponder

BASE_HOST=''


class RequestRouter():
    """ Base class for all out routers 

        This adds a little more functionality to the url handling of gaes request object
        and implements a regex router - it also splits the world into two - api requests and not.

        This class also generates the responders (factory function style) based on the path.
        This responder creation might need t be externalised so its easier to override than being in the consructor, perhaps a bit of ioc
    """

    def __init__(self, conf, sesh, req, resp):
        self._conf = conf
        self._sesh = sesh
        self._req = req
        self._resp = resp
        self._qs = urllib.unquote_plus(req.query_string)

        self._useAPI = False
        self._pa = []
        self._pl = 0
        self._extension = 'html'
        self._spath = ""
        self._netloc = ""

        self._parse_path()

        self._responder = HTMLResponder(conf, resp)
        if self._useAPI:
            self._responder = JSONResponder(conf, resp)

    
    def netloc(self):
        return self._netloc


    def query(self):
        return self._qs


    def body(self):
        return self._req.body


    def referer(self):
        return self._req.referer


    def sesh(self):
        return self._sesh


    def redirect(self, path, status=303):
        self._resp.set_status(status)
        self._resp.headers["Location"] = str(path)


    def notfound(self):
        self._resp.set_status(404)
        self._responder.notfound()


    def respond_unauth(self):
        self._resp.set_status(401)
        self._responder.unauthorised()

    
    def set_header(self, head, val):
        self._resp.headers[head] = val


    def isAPI(self):
        return self._useAPI


    def path(self):
        """ returns the array of path elements """
        return self._pa


    def get_cache_key(self):
        return self._cache_key


    def spath(self, query=True):
        """ returns the full clean path string including the querystring"""
        if query:
            return self._spath
        else:
            return self._po


    def setpar(self, par, val):
        pars = urlparse.parse_qs(self._qs)
        if isinstance(val, list):
            pars[par] = val
        else:
            pars[par] = [val]
        
        return "/" + "/".join(self._pa) + "?" + urllib.urlencode(pars, True)


    def remove_par(self, par):
        pars = urlparse.parse_qs(self._qs)
        if par in pars:
            del(pars[par])
            self._qs = urllib.urlencode(pars, True)


    def length(self):
        return self._pl


    def ext(self):
        return self._extension


    def pathel(self, ind, encode=False):
        if ind + 1 > self._pl:
            return None
        else:
            if encode:
                return urllib.quote(self._pa[ind])
            else:
                return self._pa[ind]


    def par(self, what, default_value=None):
        return self._req.get(what, default_value)


    # def cleaned_path(self):
    #     return "/" + "/".join(self.req.path()) + '?' + self.request.query_string


    def route(self, routes):
        """ given the array of routes and functions return the first match"""
        
        for r in routes:
            logging.debug("checking with: " + r['r'])
            p = re.compile(r['r'], re.IGNORECASE)
            m = p.match(self._spath)

            if m:
                logging.debug(m.groups())
                # call the passed in function 
                rval = r['f'](m.groups())
                if rval == None:
                    return True;
                return rval

        return False # no math
   

    def _parse_path(self):

        # decode, strip trailing, replace spaces with hyphens and split on seperators
        pa = urllib.unquote_plus(self._req.path).rstrip('/').replace(' ', '-').split('/')[1:]

        pl = len(pa)

        # if we have a path then check for an extension, record it - case anyone cares later (and i think they do) and remove it from the path.
        if pl > 0:
            lastbits = pa[-1].split('.')
            if len(lastbits) > 1:
                self._extension = lastbits[1].lower()
                pa[-1] = lastbits[0]


        # netloc used for oauth, scheme not used yet....
        urlstuff = urlparse.urlparse(self._req.url)
        self._netloc = urlstuff.netloc

        # check for api
        if pl > 0:
            # chack for api
            if pa[0].lower() == 'api':
                self._useAPI = True
                pa = pa[1:]

        # reconstruct our path minus the api bit
        self._po = self._spath = "/" + "/".join(pa)

        # including app version so can cache multiple page versions in our single memcache
        self._cache_key = self._conf.MCPRE + "-" + self._conf.APP_VER + "-" + self._spath
        if self._extension != "":
            self._cache_key = self._cache_key + "." + self._extension
        if self._qs:
            self._cache_key = self._cache_key + "?" + self._qs
            self._spath = self._spath + "?" + self._qs

        self._pa = pa
        self._pl = pl

        logging.debug(pa)
        logging.debug(self._spath)


    def blast(self, content):
        """ simpley blast this content directly to the reponder """ 
        self._responder.blast(content)


    def draw(self, path="", obj={}, opt={}):
        """ go throught the responders (most probably template) rendering """
        return self._responder.draw(path, obj, opt)


    def draw_code(self, code="success", message="ok", obj={}):
        """ only available on json responder """
        return self._responder.draw_code(code, message, obj)

