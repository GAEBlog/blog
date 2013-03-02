import datetime
import logging
from google.appengine.ext import db
from google.appengine.ext.db import Model   
from google.appengine.ext import blobstore

"""
    Person is the central Identity  
    AuthRecord = Many to One for a person - a person can have many openauth providers 
"""

# This is the key single identity
class Person(db.Model):
    """ has a authrecord_set as well - of all the authentcation providers """

    username = db.StringProperty()          # denormalised - so dont have to dereference Username record 
    email = db.StringProperty()
    passhash = db.StringProperty()          # used for native logon - unused yet
    role = db.StringProperty()
    displayname = db.StringProperty()
    createtime =  db.DateTimeProperty()
    
    def before_put(self):
        self.createtime = datetime.datetime.now()


class Authrecord(db.Model):
    """ Authrecord stores an openauth thing - its parent is Person """    
    
    _user = db.ReferenceProperty(Person)  # will be an authrecord_set property on person
    username = db.StringProperty()        # denormalised username from the username record
    type = db.IntegerProperty(default=1)
    auth_provider = db.StringProperty()
    auth_id = db.StringProperty()         # tis is the unique user ID from this open auth provider - so we know who has just authed
    auth_email = db.StringProperty()
    auth_token = db.StringProperty()
    auth_secret = db.StringProperty()
    logtime =  db.DateTimeProperty()
    
    def before_put(self):
        self.logtime = datetime.datetime.now()


class Blob(db.Model):
    # key nanme is onid
    content = db.TextProperty()
    createtime =  db.DateTimeProperty()
    searchterm = db.StringProperty()
    
    def before_put(self):
        self.createtime = datetime.datetime.now()
            

class Image(db.Model):
    blob_key = blobstore.BlobReferenceProperty()
    serving_url = db.StringProperty()
    author = db.StringProperty()
    title = db.StringProperty()
    tag = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)


class Group(db.Model):                          # id is url to serve it on
    title = db.StringProperty()


class Content(db.Model):                        # id is url to serve it on
    """ 
    The following are added with the 'add_property' hack later on
    current = db.ReferenceProperty(ContentVersion)
    editing = db.ReferenceProperty(ContentVersion)
    
    """

    status = db.StringProperty()               # published or draft
    ctype = db.StringProperty(default="blog")               # blog or widget
    group = db.ReferenceProperty(Group)         # which blog group this belongs to
    sortdate =  db.DateTimeProperty(auto_now_add=True)

    searchcontent = db.TextProperty()           # a copy of the title and banner and sumary to index


class ContentVersion(db.Model):                        # id is url to serve it on
    """ a uniqu content can have many content versions - perhas this should have been managed via a parent 
        instead we have the mycontent to link back to the parent - (this has helped in the flexibility needed to change urls)
    """

    mycontent = db.ReferenceProperty(Content)

    title = db.StringProperty()
    summary = db.TextProperty()
    banner = db.TextProperty()
    thumb = db.StringProperty()
    mainimage = db.ReferenceProperty(Image)
    imagepath = db.StringProperty()
    content = db.TextProperty()
    person = db.ReferenceProperty(Person)
    createtime =  db.DateTimeProperty(auto_now_add=True)

    def before_put(self):
        self.createtime = datetime.datetime.now()


def add_property(cls, name, property): 
    """ the hacky function to add properties to the model to avoid circular dependancy """ 

    setattr(cls, name, property) 
    getattr(cls, name).__property_config__(cls, name) 
    cls._properties[name] = property 


# hack to avoid circular reference 
add_property(Content, 'current',  db.ReferenceProperty(ContentVersion))
add_property(Content, 'editing',  db.ReferenceProperty(ContentVersion, collection_name='editing_set'))


def clone_entity(e, **extra_args):
    """Clones an entity, adding or overriding constructor attributes.

    The cloned entity will have exactly the same property values as the original
    entity, except where overridden. By default it will have no parent entity or
    key name, unless supplied.

    Args:
    e: The entity to clone
    extra_args: Keyword arguments to override from the cloned entity and pass
      to the constructor.
    Returns:
    A cloned, possibly modified, copy of entity e.
    """
    klass = e.__class__
    props = dict((k, v.__get__(e, klass)) for k, v in klass.properties().iteritems())
    props.update(extra_args)
    return klass(**props)



    


