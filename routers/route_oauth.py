import ext.oauth as oauth
import logging
from models.user import User


class RouteOauth():
    """ implement oauth handling - at the moment it is only for twitter - but a bit of refactoring around the keys and client would expand it easily enough """

    def __init__(self, req, conf):
        self._req = req
        self._conf = conf

        # twitter app keys
        self.application_key = self._conf.TWITTER_KEY
        self.application_secret = self._conf.TWITTER_SECRET

    
    def init(self, par):
        try:
            return self._initiate_oauth(self._req.par('ch_pv'))
        except:
            self._req.blast("Oauth exception - did you add your application keys to the config ??")


    def verify(self, par):
        return self._process_oauth(self._req.par('ch_pv'))


    def _initiate_oauth(self, provider):

        trust_root = self.__get_url_root()

        callback_url = "%s/verifyoauth?ch_pv=%s" % (trust_root, provider)

        client = oauth.TwitterClient(self.application_key, self.application_secret, callback_url)

        logging.debug("REFERRER: " + self._req.referer())
        self._req.sesh().set_return_url(self._req.referer())
        self._req.sesh().save();

        return self._req.redirect(path=client.get_authenticate_url())

    
    def _process_oauth(self, provider):

        trust_root = self.__get_url_root()

        callback_url = "%s/verifyoauth" % trust_root

        client = oauth.TwitterClient(self.application_key, self.application_secret, callback_url)

        auth_token = self._req.par("oauth_token")

        try:
            auth_verifier = self._req.par("oauth_verifier")
            user_info = client.get_user_info(auth_token, auth_verifier=auth_verifier)
            
        except Exception, e:
            logging.error(e)
            logging.error("something went wrong logging into twitter")
            logging.debug(self._req.sesh().return_url())
            return self._req.redirect(path=self._req.sesh().return_url())         # TODO redirect to an oauth error message

        # take not of the fact that an authentication event occured
        user = User(self._req.sesh())
        user.auth_event(provider, user_info)

        return self._req.redirect(path=self._req.sesh().return_url())


    def __get_url_root(self):
        """ not sure why we need this for oauth """

        if self._req.netloc() == self._conf.GAE_APP_ID  + ".appspot.com":
            trust_root = self._conf.DOMAIN
        else:
            trust_root = "http://" + self._req.netloc()

        return trust_root