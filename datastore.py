
from google.appengine.ext import db
from google.appengine.ext import ndb


#### Datastore Classes ####
class App(db.Model):
    number = db.IntegerProperty()
    title = db.StringProperty()
    appId = db.StringProperty()
    heroHeader = db.StringProperty()
    heroCopy = db.TextProperty()
    pdfChapter = db.BooleanProperty(default=True)
    conceptualLink = db.BooleanProperty(default=True)
    manyMold = db.StringProperty()
    version = db.StringProperty(default="1")
    timestamp = db.DateTimeProperty(auto_now=True)
    webTutorial = db.BooleanProperty(default=False)
    webTutorialLink = db.StringProperty()

# for the "Build It" section of a generated app page
class Step(db.Model):
    # appId = db.IntegerProperty() # specifies app the step belongs to
    appId = db.StringProperty()  # temporary identifier | TODO: remove this
    number = db.IntegerProperty()
    header = db.StringProperty()
    copy = db.TextProperty()
    videoPath = db.StringProperty()
    fullscreenPath = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now=True)

class Concept(db.Model):
    # appId = db.IntegerProperty() # specifies app the step belongs to
    appId = db.StringProperty()  # temporary identifier | TODO: remove this
    number = db.IntegerProperty()
    header = db.StringProperty()
    copy = db.TextProperty()
    blockPath = db.StringProperty()
    videoPath = db.StringProperty()
    fullscreenPath = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now=True)

class Custom(db.Model):
    # appId = db.IntegerProperty() # specifies app the step belongs to
    appId = db.StringProperty()  # temporary identifier | TODO: remove this
    number = db.IntegerProperty()
    header = db.StringProperty()
    copy = db.TextProperty()
    blockPath = db.StringProperty()
    videoPath = db.StringProperty()
    fullscreenPath = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now=True)


class Account(db.Model):
    user = db.UserProperty()
    profilePicture = db.BlobProperty()
    firstName = db.StringProperty(default="")
    lastName = db.StringProperty(default="")
    location = db.StringProperty(default="")
    organization = db.StringProperty(default="")
    ifEducator = db.BooleanProperty(default=False)
    educationLevel = db.StringProperty()
    introductionLink = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now=True)
    latitude = db.FloatProperty()
    longitude = db.FloatProperty()
    displayName = db.StringProperty()

class DefaultAvatarImage(db.Model):
        title = db.StringProperty()
        picture = db.BlobProperty(default=None)

class Position(db.Model):
        latitude = db.FloatProperty()
        longitude = db.FloatProperty()

class Comment(db.Model):
        submitter = db.ReferenceProperty(collection_name='submitter')
        timestamp = db.DateTimeProperty(auto_now=True)
        content = db.StringProperty()
        appId = db.StringProperty()
        replyFrom = db.ReferenceProperty(collection_name='replyFrom')
        replyTo = db.ReferenceProperty(collection_name='replyTo')
    
class Tutorial(db.Model):
        number = db.IntegerProperty()
        title = db.StringProperty()
        tutorialId = db.StringProperty()
        heroHeader = db.StringProperty()
        heroCopy = db.TextProperty()
        timestamp = db.DateTimeProperty(auto_now=True)

class TutorialStep(db.Model):
    # appId = db.IntegerProperty() # specifies app the step belongs to
    tutorialId = db.StringProperty()  # temporary identifier | TODO: remove this
    number = db.IntegerProperty()
    header = db.StringProperty()
    copy = db.TextProperty()
    tutorialLink = db.StringProperty()
    timestamp = db.DateTimeProperty(auto_now=True)

class AdminAccount(db.Model):
        name = db.StringProperty()
        gmail = db.StringProperty()
        password = db.StringProperty()
    


class Message(ndb.Model):
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)
    
class Module(ndb.Model):
    """ Represents a single Module """
    m_title = ndb.StringProperty()
    m_description = ndb.StringProperty()
    m_icon = ndb.BlobProperty(indexed=False)
    m_index = ndb.IntegerProperty()
    m_identifier = ndb.StringProperty()
    
class Content(ndb.Model):
    """ Represents a content item """
    c_title = ndb.StringProperty()
    c_description = ndb.StringProperty()
    c_type = ndb.StringProperty()
    c_url = ndb.StringProperty()  # the url of the content
    c_index = ndb.IntegerProperty()    
    c_identifier = ndb.StringProperty()
    c_oldurls = ndb.StringProperty(repeated=True) # this is used by the redirector, normally its the same
                                    # as the c_url but sometimes it is different

class Course(ndb.Model):
    """Represents a single course"""
    c_title = ndb.StringProperty()
    c_url_title = ndb.StringProperty()
    c_description = ndb.StringProperty()
    c_icon = ndb.BlobProperty(indexed=False)
    c_index = ndb.IntegerProperty()
    c_identifier = ndb.StringProperty()


class RSSItem(ndb.Model): 
    title = ndb.StringProperty()
    link = ndb.StringProperty()
    content = ndb.TextProperty()
    date = ndb.StringProperty()
    dateUnFormatted = ndb.DateTimeProperty()
    

# for the "Conceptualize It" section of a generated app page    
# class Concept(db.Model):     

# for the "Customize It" section of a generated app page
# class Custom(db.Model):

    
