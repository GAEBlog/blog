import logging

from models import Person
from models import Authrecord

from utils import Utils

class User():
    """The Users -  rules around the Persons model and authenticating users""" 

    def __init__(self, sesh):
        self._sesh = sesh
        self._person = None


    def auth_event(self, provider, user_info):
        ''' This gets called whenver any good auth thing happens '''

        auth_id = provider + '-' + str(user_info['id'])   # user_info['id'] is the unique id from this oauth provider
        logging.debug("New Oauth: " + auth_id)

        # find this auth_id in our auth records
        query = Authrecord.all()
        query.filter("auth_id", auth_id)
        auth_obj = query.get()

        if auth_obj:                        # so was pre existing authorisation so lets bring back Jenny and set her as authenticated
            logging.debug("got auth record for " + auth_id)
            self._person = auth_obj.parent()
            username = self._person.username

        else:
            # no auth object - so must create a new person and create a new auth object and check this username has not been used
            username = self.create_new_user(user_info['username'], 'user', email='')    # will use rawname from the oauth to create a self._person
            if username == "":
                return False
            else:
                auth_obj = Authrecord(parent = self._person)
                auth_obj.before_put()

                auth_obj.username = username
                auth_obj.auth_provider = provider
                auth_obj.auth_id = auth_id
                auth_obj.auth_email = "na"
                auth_obj.auth_token = user_info['token']
                auth_obj.auth_secret = user_info['secret']

                auth_obj.put()

        # mark the current session as authenticated
        if username != "":
            self._sesh.set_authenticated(username, self._person.role, self._person.email)


    def get_sesh_person(self):
        
        username = self._sesh.user_name()
        return self.get_person(username)


    def get_person(self, username):
        if username == "":
            return None

        logging.debug("finding person by username: >" + username + "<")
        q = Person.all().filter("username =", username)
        return q.get()


    def create_new_user(self, rawname, role, email=""):
        ''' Creates a new Person record with a unique username, or returns a person wiht the matching username'''

        ut = Utils()
        username = ut.cleanUserName(rawname)

        if ut.validateUserName(username):

            # check for username
            person = self.get_person(username)

            # create a new person if we have not got this one 
            if person == None:
                person = Person()
                person.email = email
                person.passhash = '';                           # no passhash if not got a direct logon
                person.username = username
                person.displayname = ut.tidyUserName(rawname)   # allow the username to be updated on the myHoots or profile or summink
                person.before_put()
                person.role = role
                person.put();
            
            self._person = person
            
            return username
        else:
            return ""
    