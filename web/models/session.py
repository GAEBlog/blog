import pickle
import random
import logging

from google.appengine.api import memcache

_sidChars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
_defaultTimeout = 10 * 24 * 60 * 60 # 10 days

class Session():
    """The Session class pickling itself into memcache"""    

    def __init__(self):
        self._sid = ''                       # the session id
        self._timeout =_defaultTimeout       # how long the session should last after its last activity
        self._new = True                     # created this request
        self._authenticated = False          # simple flag telling us if this session has authenticated somehow
        self._authenticated_for = ''         # the username that this session is authenticated for
        self._role = 'user'                  # what role this user has - 'editor' 'admin' 'user'
        self._auth_email = ''                # captured as part of the oauth proces
        self._return_url = ''                # persisted url that we may use to return to
            

    def load(self, sid):
        """recover or create session state from the given session id.

        Keyword arguments:
        sid -- the sessionid

        """
        # memcache parser
        data=memcache.get(sid)

        # found this data in our store
        if data:
            # this is not a new session
            self._new = False    
            # unpickle our state        
            self.__dict__.update(pickle.loads(data))
            # memcache timeout is absolute, so we need to reset it on each access - sub-optimal can refresh timer without sending data
            memcache.set(sid, data, self._timeout)

        else:
            # not this session must have expired or been pushed out - generate a new sesion
            self.create()


    def create(self):
        """create a new session"""
        
        # Create a new session ID
        # There are about 10^14 combinations, so very unlikely collision - a super ananl app should check for collision and do other session checking
        self._sid = random.choice(_sidChars)+random.choice(_sidChars)+\
                    random.choice(_sidChars)+random.choice(_sidChars)+\
                    random.choice(_sidChars)+random.choice(_sidChars)+\
                    random.choice(_sidChars)+random.choice(_sidChars)
        
        # make sure the new session object is not authenticated
        self._authenticated = False
        self._authenticated_for = ""
        
        # stick this session in memcache
        self.save()

        
    def save(self):
        """persist this sessions pickled state into memcache"""
        logging.debug("SAVING SESH: " + self._sid)
        logging.debug("returl : " + self._return_url)
        if not memcache.set(self._sid, pickle.dumps(self.__dict__), self._timeout):
            logging.error("SET fainel")

        
    def delete(self):
        """remove oueselves from memcache """
        memcache.delete(self._sid)
        # make sure everyone knows we are now not authenticated
        self._authenticated = False;


    def set_authenticated(self, user, role, email):
        self._authenticated = True
        self._authenticated_for = user
        self._role = role
        self._auth_email = email
        self.save()


    def set_return_url(self, url):
        self._return_url = url


    def return_url(self):
        return self._return_url

    
    def id(self):
        return self._sid


    def user_name(self):
        return self._authenticated_for


    def can_edit(self):
        return self._role == 'admin' or self._role == 'editor'


    def get_role(self):
        return self._role


    def authorised(self):
        """is this user authorised - at the moment this is just authenticated as the authorisation logic is not in the session yet"""
        return self._authenticated
