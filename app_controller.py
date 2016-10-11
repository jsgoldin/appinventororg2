import ast
import collections
import datetime
import feedparser
import logging
import os
import time

from google.appengine.api import images
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from datastore import Account, RSSItem
from datastore import App
from datastore import Comment
from datastore import Custom
from datastore import Module, Content, Course
from datastore import Step
from datastore import Tutorial
from datastore import TutorialStep
import gdata.analytics.client
from geopy import geocoders


try: import simplejson as json
except ImportError: import json



APPSDIR = '/apps'
APPS2DIR = '/apps2'


def getCourses():
    """
    Returns an ordered list of all courses on the site.
    """
    return Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()                    

def getCoursesAndModules():
    """
    Returns an ordered list of all courses and the modules inside them.
    [(course_a, [(module_a, module_a_url), (module_b, module_b_url), ... ]), ...]
    """
    courses = getCourses()

    courseModList = []
    for course in courses: 
        # fetch modules for the current course
        modulesList = []
        course_id = long(course.key.id())
        modules = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, course_id)).order(Module.m_index).fetch() 
        for module in modules:
            modulesList.append((str(module.m_title), "/content/" + course.c_identifier + "/" + module.m_identifier))
        courseModList.append((str(course.c_title), modulesList))
    return courseModList
    
def redirector(requesthandler):
    """Used to redirect old content to their new url in a course
    
    Returns true if a redirect occurs and false otherwise.
    
    The caller function should return if a redirect occurs
    as to stop unwanted execution of code in the caller function
    following the call to redirector.
    """
    # redirect test
    if requesthandler.request.get('flag') == 'true':
        logging.critical("Do not redirect!")
        return False
    else:
        # look up a content that uses this url
        
        results = Content.query(ancestor=ndb.Key('Courses', 'ADMINSET')).filter(ndb.OR(Content.c_oldurls.IN([requesthandler.request.path]), Content.c_url == requesthandler.request.path + "?flag=true")).fetch()
        if len(results) == 0:
            logging.critical("Could not find a content to redirect too for: " + str(requesthandler.request.path))
        else:
            content = results[0]
            # build the url
            content_id = content.c_identifier
            module_id = content.key.parent().get().m_identifier
            course_id = content.key.parent().parent().get().c_identifier
            redirectURL = "content/" + course_id + "/" + module_id + "/" + content_id
                
            logging.critical("redirecting: " + requesthandler.request.path + " >>> " + redirectURL)
            requesthandler.redirect(redirectURL)
            return True;



def intWithCommas(x):
    if type(x) not in [type(0), type(0L)]:
        raise TypeError("Parameter must be an integer.")
    if x < 0:
        return '-' + intWithCommas(-x)
    result = ''
    while x >= 1000:
        x, r = divmod(x, 1000)
        result = ",%03d%s" % (r, result)
    return "%d%s" % (x, result)



class PublicProfileHandler(webapp.RequestHandler):
    def get(self):

        key = self.request.get("accountKey")
        account = db.get(key)
        if not account:
            self.response.out.write('Invalid Request')
            return

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)


        # look up all the courses for the global navbar
        courses = getCourses()                    
                    
        userStatus = UserStatus().getStatus(self.request.uri)
        
        template_values = {'account': account,
                           'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor',
                           'stylesheets' : ['/assets/css/coursesystem.css'],
                           'scripts' : [],
                           }

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/publicProfile.html')
        self.response.out.write(template.render(path, template_values))



class ProfileHandler(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            # not signed into google account, once signed in retry
            # validation
            self.redirect(users.create_login_url('/loginValidator'))
            return None
        
        # check if user has an account
        pquery = db.GqlQuery("SELECT * FROM Account where user= :1 ", user)
        account = pquery.get()     
        if not account:
            # no account was found redirect to account creation page
            self.redirect("/createAccount")
            return None
        
        
        courses = getCourses()                          
        
        educationLevelCheck0 = ''
        educationLevelCheck1 = ''
        educationLevelCheck2 = ''
        ifEducatorShow = "collapse"

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        if not user:
            self.redirect(userStatus['loginurl'])

        if account:  # dude has already registered
            message = 'Welcome Back,'
            firstName = account.firstName
            lastName = account.lastName
            location = account.location
            organization = account.organization
            displayName = account.displayName
            ifEducator = account.ifEducator
            if(ifEducator == True):
                ifEducatorShow = "collapse in"
            else:
                ifEducatorShow = "collapse"

            educationLevel = account.educationLevel
            if educationLevel == None:
                educationLevelCheck0 = 'checked'
            else:
                if educationLevel == 'K-8':
                    educationLevelCheck0 = 'checked'
                elif educationLevel == 'High School':
                    educationLevelCheck1 = 'checked'
                elif educationLevel == 'College/University':
                    educationLevelCheck2 = 'checked'
            
        else:
            message = 'Welcome Aboard,'
            firstName = ''
            lastName = ''
            location = ''
            organization = ''
            ifEducator = ''
            educationLevel = ''               
            user = users.get_current_user()
            account = Account()
            account.user = user
            account.firstName = ''
            account.lastName = ''
            account.location = ''
            account.organization = ''
            account.introductionLink = ''
            account.displayName = str(user.nickname())  # default displayname is email
            account.put()

        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

        template_values = {
                           'courses' : courses,
                           'account': account,
                           'allAppsList': allAppsList,
                           'allAppsList2': allAppsList2,
                           'userStatus': userStatus,
                           'ifEducator' : ifEducator,
                           'ifEducatorShow': ifEducatorShow,
                           'educationLevel': educationLevel,
                           'educationLevelCheck0': educationLevelCheck0,
                           'educationLevelCheck1': educationLevelCheck1,
                           'educationLevelCheck2': educationLevelCheck2,
                           'stylesheets' : ['/assets/css/coursesystem.css'],
                           'courseToModules' : getCoursesAndModules(),
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/profile.html')
        self.response.out.write(template.render(path, template_values))

class ChangeProfileHandler(webapp.RequestHandler):
    def get(self):
        
        user = users.get_current_user()
        pquery = db.GqlQuery("SELECT * FROM Account where user= :1 ", user)
        account = pquery.get()

        

        educationLevelCheck0 = ''
        educationLevelCheck1 = ''
        educationLevelCheck2 = ''
        ifEducatorShow = "collapse"

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        if not user:
            self.redirect(userStatus['loginurl'])


        
        
        if account:  # dude has already registered
            message = 'Welcome Back,'
            firstName = account.firstName
            lastName = account.lastName
            location = account.location
            organization = account.organization
            account.displayName = account.displayName
            displayName = account.displayName
            ifEducator = account.ifEducator
            if(ifEducator == True):
                ifEducatorShow = "collapse in"
            else:
                ifEducatorShow = "collapse"

            educationLevel = account.educationLevel
            if educationLevel == None:
                educationLevelCheck0 = 'checked'
            else:
                if educationLevel == 'K-8':
                    educationLevelCheck0 = 'checked'
                elif educationLevel == 'High School':
                    educationLevelCheck1 = 'checked'
                else:
                    educationLevelCheck2 = 'checked'
            
        else:
            message = 'Welcome Aboard,'
            firstName = ''
            lastName = ''
            location = ''
            organization = ''
            ifEducator = ''
            educationLevel = ''

        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

    
        courses = getCourses()                    
                    


        template_values = {'courses' : courses,
                           'account': account,
                           'userStatus': userStatus,
                           'ifEducatorShow': ifEducatorShow,
                           'ifEducator' : ifEducator,
                           'educationLevelCheck0': educationLevelCheck0,
                           'educationLevelCheck1': educationLevelCheck1,
                           'educationLevelCheck2': educationLevelCheck2,
                           'title' : 'Update Profile',
                           'stylesheets' : ['/assets/css/coursesystem.css'],
                           'scripts' : ['/assets/js/updateProfile.js'],
                           'courseToModules' : getCoursesAndModules(),
                           }
        
        
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/changeProfile.html')
        self.response.out.write(template.render(path, template_values))
 
class updateProfilePictureHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        pquery = db.GqlQuery("SELECT * FROM Account where user= :1 ", user)
        account = pquery.get() 
        
        image = self.request.get('pictureFile')
        if image is not None :
            if len(image.strip(' \t\n\r')) != 0:                
                account.profilePicture = db.Blob(image)
                account.put()
        self.redirect("/profile")

        
class SaveProfile(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        pquery = db.GqlQuery("SELECT * FROM Account where user= :1 ", user)
        account = pquery.get()

        # #user status
        # userStatus = UserStatus()
        # userStatus = userStatus.getStatus(self.request.uri)
        # if not user:
        #    self.redirect(userStatus['loginurl'])


        if account:  # dude has already registered
            message = 'Welcome Back,'
        else:
            message = 'Welcome Aboard,'
            account = Account()

        account.user = user
        account.firstName = self.request.get('firstName')
        account.lastName = self.request.get('lastName')
        account.location = self.request.get('location')
        account.organization = self.request.get('organization')
        account.displayName = self.request.get('displayName')
        b = self.request.get('ifEducator')
        if(b == "on"):
                account.ifEducator = True
                # only record lat/lon if it is an educator
                g = geocoders.GoogleV3()
                try:
                    
                    place, (lat, lng) = g.geocode(account.location)
                    account.latitude = float(lat)
                    account.longitude = float(lng)
                except:
                    a = "1"
        else:
                account.ifEducator = False
        
        
        account.educationLevel = self.request.get('educationLevel')
        link = self.request.get('introductionLink')
        if(len(link.strip()) == 0):
            account.introductionLink = ''
        else:
            link = link.replace("http://", "")
            link = link.replace("https://", "")
            account.introductionLink = link
        account.put()

        # if uploading image
        if self.request.get('pictureFile') is not None :
            if len(self.request.get('pictureFile').strip(' \t\n\r')) != 0:
                self.uploadimage()
                self.redirect("/profile?savePic=successful")



        self.redirect("/profile?save=successful" + str(self.request.get('h')))
        # self.redirect("/profile?save=successful")
        
    def uploadimage(self):
        picture = self.request.get('pictureFile')

        user = users.get_current_user()
        account_query = db.GqlQuery("Select * from Account where user=:1", user)
        account = account_query.get()

        x1 = float(self.request.get('x1'))
        y1 = float(self.request.get('y1'))
        x2 = float(self.request.get('x2'))
        y2 = float(self.request.get('y2'))
        newH = float(self.request.get('h'))
        newW = float(self.request.get('w'))

        x_left = float(self.request.get('x_left'))
        y_top = float(self.request.get('y_top'))
        x_right = float(self.request.get('x_right'))
        y_bottom = float(self.request.get('y_bottom'))

        originalW = x_right - x_left
        originalH = y_bottom - y_top

        # originalW = 300
        # originalH = 300


        x1_fixed = x1 - x_left
        y1_fixed = y1 - y_top
        x2_fixed = x2 - x_left
        y2_fixed = y2 - y_top


        if(x1_fixed < 0):
            x1_fixed = 0
        if(y1_fixed < 0):
            y1_fixed = 0
        if(x2_fixed > originalW):
            x2_fixed = originalW
        if(y2_fixed > originalH):
            y2_fixed = originalH


        picture = images.crop(picture, float(x1_fixed / originalW), float(y1_fixed / originalH), float(x2_fixed / originalW), float(y2_fixed / originalH))
        picture = images.resize(picture, 300, 300)


        if not account:
            account = Account()
        if picture:
            account.user = user  # maybe duplicate, but it is really imporant to make sure
            account.profilePicture = db.Blob(picture)  
        account.put()
        return


    
class CourseOutlineHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/outline.html')
        self.response.out.write(template.render(path, template_values))

class GettingStartedHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/gettingstarted.html')
        self.response.out.write(template.render(path, template_values))

class IntroductionHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/introduction.html')
        self.response.out.write(template.render(path, template_values))

class CourseInABoxHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/course-in-a-box.html')
        self.response.out.write(template.render(path, template_values))

class CourseInABoxHandlerTeaching(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/course-in-a-box.html')
        self.response.out.write(template.render(path, template_values))

class CourseInABox2Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = {'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/courseInABox2.html')
        self.response.out.write(template.render(path, template_values))

class SoundBoardHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/soundboard.html')
        self.response.out.write(template.render(path, template_values))

class PortfolioHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/portfolio.html')
        self.response.out.write(template.render(path, template_values))


class IntroTimerHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/introTimerEvents.html')
        self.response.out.write(template.render(path, template_values))

class SmoothAnimationHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/smoothAnimation.html')
        self.response.out.write(template.render(path, template_values))

class MediaHandler(webapp.RequestHandler):
    def get(self):
        courses = getCourses()                    
                    
        userStatus = UserStatus().getStatus(self.request.uri)
        
        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
                           }
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/media.html')
        self.response.out.write(template.render(path, template_values))

class MediaFilesHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/mediaFiles.html')
        self.response.out.write(template.render(path, template_values))

class StructureHandler(webapp.RequestHandler):
    def get(self):
    	courses = getCourses()                    
                    
        userStatus = UserStatus().getStatus(self.request.uri)
        
        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
                           }
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/structure.html')
        self.response.out.write(template.render(path, template_values))

class HelloPurrHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/helloPurr.html')
        self.response.out.write(template.render(path, template_values))

class AppPageHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None

        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/appPage.html')
        self.response.out.write(template.render(path, template_values))

class AppInventorIntroHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = {'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/AppInventorIntro.html')
        self.response.out.write(template.render(path, template_values))

class RaffleHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/raffleApp.html')
        self.response.out.write(template.render(path, template_values))
class LoveYouHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/loveYou.html')
        self.response.out.write(template.render(path, template_values))

class LoveYouWSHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/loveYouWS.html')
        self.response.out.write(template.render(path, template_values))


class AndroidWhereHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/androidWhere.html')
        self.response.out.write(template.render(path, template_values))

class GPSHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/gpsIntro.html')
        self.response.out.write(template.render(path, template_values))

class NoTextingHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/noTexting.html')
        self.response.out.write(template.render(path, template_values))

class MoleMashHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/moleMash.html')
        self.response.out.write(template.render(path, template_values))

class PaintPotHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        

        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/paintPot.html')
        self.response.out.write(template.render(path, template_values))

class ShooterHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/shooter.html')
        self.response.out.write(template.render(path, template_values))

class UserGeneratedHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/userGenerated.html')
        self.response.out.write(template.render(path, template_values))

class BroadcastHubHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/broadcastHub.html')
        self.response.out.write(template.render(path, template_values))


class NoteTakerHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/noteTaker.html')
        self.response.out.write(template.render(path, template_values))


class QuizHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/quiz.html')
        self.response.out.write(template.render(path, template_values))
    


        
class AppInventor2ChangesHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/AppInventor2Changes.html')
        self.response.out.write(template.render(path, template_values))
    
class PresidentsQuizTutHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/presidentsQuizTut.html')
        self.response.out.write(template.render(path, template_values))

class IHaveADreamTutHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/IHaveADreamTut.html')
        self.response.out.write(template.render(path, template_values))




class Mod1ReadingHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/mod1reading.html')
        self.response.out.write(template.render(path, template_values))
        

class Mod2ReadingHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/mod2reading.html')
        self.response.out.write(template.render(path, template_values))
class Mod3ReadingHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/mod3reading.html')
        self.response.out.write(template.render(path, template_values))

class Mod4ReadingHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/mod4reading.html')
        self.response.out.write(template.render(path, template_values))

class Mod5ReadingHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/mod5reading.html')
        self.response.out.write(template.render(path, template_values))

class Mod6ReadingHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/mod6reading.html')
        self.response.out.write(template.render(path, template_values))
        
class Mod7ReadingHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/mod7reading.html')
        self.response.out.write(template.render(path, template_values))

        

class BiblioHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = {'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/biblio.html')
        self.response.out.write(template.render(path, template_values))

class TimedActivityHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/timedActivity.html')
        self.response.out.write(template.render(path, template_values))

class TimedActivitySoundHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/timedActivity-sound.html')
        self.response.out.write(template.render(path, template_values))
class TimedActivitySoundFiveHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/timedActivity-soundFive.html')
        self.response.out.write(template.render(path, template_values))
class TimedActivitySpaceHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/timedActivity-space.html')
        self.response.out.write(template.render(path, template_values))
class TimedActivityFrameHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/timedActivity-frame.html')
        self.response.out.write(template.render(path, template_values))
class TimedActivityStartClickHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/timedActivity-startClick.html')
        self.response.out.write(template.render(path, template_values))
class TimedActivityStartSpeakHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/timedActivity-startSpeak.html')
        self.response.out.write(template.render(path, template_values))
class EventsRedBtnHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/events-redbtn.html')
        self.response.out.write(template.render(path, template_values))

class EventsShakingHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/events-shaking.html')
        self.response.out.write(template.render(path, template_values))
           


class ConditionalsHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Conditionals2.html')
        self.response.out.write(template.render(path, template_values))

class ConditionalsStartHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Conditionals-startStop.html')
        self.response.out.write(template.render(path, template_values))

class ConditionalsWhereHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Conditionals-where.html')
        self.response.out.write(template.render(path, template_values))

class RecordingItemHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/recordingitems.html')
        self.response.out.write(template.render(path, template_values))

class RecordingItemNotesHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/recordingitems-notes.html')
        self.response.out.write(template.render(path, template_values))
class RecordingItemPhoneHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/recordingitems-phone.html')
        self.response.out.write(template.render(path, template_values))
class WalkingalistHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/walkingalist.html')
        self.response.out.write(template.render(path, template_values))

class VariablesHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/variables.html')
        self.response.out.write(template.render(path, template_values))
class VariablesCirclesHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/variablesHowDoYou.html')
        self.response.out.write(template.render(path, template_values))
class VariablesBackForthHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/variables-backForth.html')
        self.response.out.write(template.render(path, template_values))
class ListsHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/lists.html')
        self.response.out.write(template.render(path, template_values))

class ProcHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/procedures2.html')
        self.response.out.write(template.render(path, template_values))      
 
class ProcListHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/procedures2-list.html')
        self.response.out.write(template.render(path, template_values))    
class ProcParamHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/procedures2-param.html')
        self.response.out.write(template.render(path, template_values))      
class ProcAnyLabelHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/procedures2-anyLabel.html')
        self.response.out.write(template.render(path, template_values)) 
class LocationHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/location.html')
        self.response.out.write(template.render(path, template_values))         

class LocationLatLongHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/location-latLong.html')
        self.response.out.write(template.render(path, template_values))
        
class LocationDistanceHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/location-distance.html')
        self.response.out.write(template.render(path, template_values))    

class DrawingHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/drawing.html')
        self.response.out.write(template.render(path, template_values))

class DrawingCanvasHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/drawing-canvas.html')
        self.response.out.write(template.render(path, template_values))

class DrawingCircleHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/drawing-circle.html')
        self.response.out.write(template.render(path, template_values))

class DrawingTouchHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/drawing-touch.html')
        self.response.out.write(template.render(path, template_values))

class DrawingMiddleHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/drawing-middle.html')
        self.response.out.write(template.render(path, template_values))
class SpritesHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/sprites.html')
        self.response.out.write(template.render(path, template_values))
        
class SpritesMoveHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/sprites-move.html')
        self.response.out.write(template.render(path, template_values))  
        
class SpritesBounceHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/sprites-bounce.html')
        self.response.out.write(template.render(path, template_values))        
class ResourcesHandler(webapp.RequestHandler):
    def get(self):
        courses = getCourses()                    
                    
        userStatus = UserStatus().getStatus(self.request.uri)
        
        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/resources.html')
        self.response.out.write(template.render(path, template_values)) 


        
          
class TimedListsHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/timedLists.html')
        self.response.out.write(template.render(path, template_values))
class TimedListsMusicHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/timedLists-music.html')
        self.response.out.write(template.render(path, template_values))
class TimedListsAslHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/timedLists-asl.html')
        self.response.out.write(template.render(path, template_values))
class IncrementingCountHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Incrementing-count.html')
        self.response.out.write(template.render(path, template_values))
class IncrementingCountDownHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Incrementing-countDown.html')
        self.response.out.write(template.render(path, template_values))
    
    
class IncrementingVariablesHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/incrementingvariables.html')
        self.response.out.write(template.render(path, template_values))
    
class UserListNavHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/userListNav.html')
        self.response.out.write(template.render(path, template_values))
class UserListNavNextHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/userListNav-next.html')
        self.response.out.write(template.render(path, template_values))
class UserListNavPrevHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/userListNav-prev.html')
        self.response.out.write(template.render(path, template_values))
class UserListNavLoopHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/userListNav-loop.html')
        self.response.out.write(template.render(path, template_values))
class PersistenceHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/persistence.html')
        self.response.out.write(template.render(path, template_values))

class PersistenceMessageHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/persistence-message.html')
        self.response.out.write(template.render(path, template_values))
class PersistenceNotesHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/persistence-notes.html')
        self.response.out.write(template.render(path, template_values))
class FAQHandler(webapp.RequestHandler):
    def get(self):
        # hardcoded redirection to the howDoYou page
        self.redirect("/content/howDoYou")
        

class ListsTextHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/lists-text.html')
        self.response.out.write(template.render(path, template_values))
class ListsSumHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/lists-sum.html')
        self.response.out.write(template.render(path, template_values))
class KnowledgeMapHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/knowledgeMap.html')
        self.response.out.write(template.render(path, template_values))

class QuizIntroHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/quizIntro.html')
        self.response.out.write(template.render(path, template_values))
class IntroIfHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/introIf.html')
        self.response.out.write(template.render(path, template_values))

class StarterAppsHandler(webapp.RequestHandler):
    def get(self):
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        courses = getCourses()                    

        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor 2: Starter Apps',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
                           'courseToModules' : getCoursesAndModules()
                           }
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/starterApps.html')
        self.response.out.write(template.render(path, template_values))



class PaintPotIntroHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/paintPotIntro.html')
        self.response.out.write(template.render(path, template_values))

class MoleMashManymoHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/moleMashManymo.html')
        self.response.out.write(template.render(path, template_values))

class MediaHandlerTeaching(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/media.html')
        self.response.out.write(template.render(path, template_values))


class TeachingHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/teaching.html')
        self.response.out.write(template.render(path, template_values))

class IHaveADreamHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/IHaveADream.html')
        self.response.out.write(template.render(path, template_values))


class WebDatabaseHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 
            'allAppsList': allAppsList,
            'allAppsList2': allAppsList2,
            'userStatus': userStatus,
            'apps2Dir':APPS2DIR,
            'courseToModules' : getCoursesAndModules()
        }
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/webDatabase.html')
        self.response.out.write(template.render(path, template_values))

class ConceptsHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/concepts.html')
        self.response.out.write(template.render(path, template_values))

class AbstractionHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/proceduralAbstraction.html')
        self.response.out.write(template.render(path, template_values))

class MoleMash2Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/molemashAI2.html')
        self.response.out.write(template.render(path, template_values))
        
class RobotsHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/robotRemoteAI2.html')
        self.response.out.write(template.render(path, template_values))

class AmazonHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/amazon13.html')
        self.response.out.write(template.render(path, template_values))


class HelloPurr2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/hellopurrAI2.html')
        self.response.out.write(template.render(path, template_values))

class PaintPot2Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/paintpotAI2.html')
        self.response.out.write(template.render(path, template_values))
        
class NoTexting2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/notextingAI2.html')
        self.response.out.write(template.render(path, template_values))

class MakeQuiz10Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/MakeQuiz10.html')
        self.response.out.write(template.render(path, template_values))
        
class TeacherListHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        teacherList = db.GqlQuery("SELECT * FROM Account WHERE ifEducator=True");
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR, 'teacherList':teacherList}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/teacherList.html')
        self.response.out.write(template.render(path, template_values))

class TeachingAIHandler(webapp.RequestHandler):
    def get(self):
        
        courses = getCourses()                    
                    
        userStatus = UserStatus().getStatus(self.request.uri)
        
        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
                           }
        
        
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/teachingAI.html')
        self.response.out.write(template.render(path, template_values))

class TeacherIntroHandler(webapp.RequestHandler):
    def get(self):
        
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/teacherIntro.html')
        self.response.out.write(template.render(path, template_values))

class TeacherIntroIntroHandler(webapp.RequestHandler):
    def get(self):
        
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/teacherIntroIntro.html')
        self.response.out.write(template.render(path, template_values))

class PresidentsQuiz2Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/presidentsquizAI2.html')
        self.response.out.write(template.render(path, template_values))

class MapTour2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/maptourAI2.html')
        self.response.out.write(template.render(path, template_values))

class AndroidCar2Handler(webapp.RequestHandler):
    def get(self):
        
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/androidcarAI2.html')
        self.response.out.write(template.render(path, template_values))

class BroadcastHub2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/broadcasthubAI2.html')
        self.response.out.write(template.render(path, template_values))

class XYLoPhone2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/xylophoneAI2.html')
        self.response.out.write(template.render(path, template_values))

    
class Ladybug2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/ladybugAI2.html')
        self.response.out.write(template.render(path, template_values))

class Architecture2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Architecture14.html')
        self.response.out.write(template.render(path, template_values))

class Engineering2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Engineering15.html')
        self.response.out.write(template.render(path, template_values))

class Variables2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Variables16.html')
        self.response.out.write(template.render(path, template_values))

class Creation2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Creating17.html')
        self.response.out.write(template.render(path, template_values))

class Conditionals2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Conditionals18.html')
        self.response.out.write(template.render(path, template_values))

class Lists2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Lists19.html')
        self.response.out.write(template.render(path, template_values))

class Iteration2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Iteration20.html')
        self.response.out.write(template.render(path, template_values))

class Procedures2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Procedures21.html')
        self.response.out.write(template.render(path, template_values))

class Databases2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Databases22.html')
        self.response.out.write(template.render(path, template_values))

class Sensors2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Sensors23.html')
        self.response.out.write(template.render(path, template_values))

class API242Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/API24.html')
        self.response.out.write(template.render(path, template_values))
        
        
class EventHandlersHandler(webapp.RequestHandler):
    def get(self):
        
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        courses = getCourses()                    

        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor 2 Book: Create Your Own Android Apps',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
                           'apps2Dir':APPS2DIR
                           }
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/eventHandlers.html')
        self.response.out.write(template.render(path, template_values))
        

class ConditionalsInfoHandler(webapp.RequestHandler):
    def get(self):
        
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        courses = getCourses()                    

        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor 2 Book: Create Your Own Android Apps',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
                           'apps2Dir':APPS2DIR
                           }
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/conditionals.html')
        self.response.out.write(template.render(path, template_values))
        
class PropertiesHandler(webapp.RequestHandler):
    def get(self):
        
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        courses = getCourses()                    

        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor 2 Book: Create Your Own Android Apps',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
                           'apps2Dir':APPS2DIR
                           }
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/properties.html')
        self.response.out.write(template.render(path, template_values))
       
class QuizlyHandler(webapp.RequestHandler):
    def get(self):
        quizName = self.request.get('quizname')
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
                
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR, 'quizname':quizName}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/dquizly.html')
        self.response.out.write(template.render(path, template_values))

class WorkingWithMediaHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/workingWithMedia.html')
        self.response.out.write(template.render(path, template_values))

class MathBlasterHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/mathBlaster.html')
        self.response.out.write(template.render(path, template_values))


class SlideShowQuizHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/slideshowQuiz.html')
        self.response.out.write(template.render(path, template_values))

class MeetMyClassmatesHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/meetMyClassmates.html')
        self.response.out.write(template.render(path, template_values))

class JavaBridgePageHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/javaBridgePage.html')
        self.response.out.write(template.render(path, template_values))

class AppInventor2Handler(webapp.RequestHandler):
    def get(self):
        
        courses = getCourses()                    
                    
        userStatus = UserStatus().getStatus(self.request.uri)
        
        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : [],
                           }
                
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/appInventor2.html')
        self.response.out.write(template.render(path, template_values))

class GalleryHowToHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/galleryHowTo.html')
        self.response.out.write(template.render(path, template_values))



# MODULES
class Module1Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/module1.html')
        self.response.out.write(template.render(path, template_values))

class Module2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/module2.html')
        self.response.out.write(template.render(path, template_values))

class Module3Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/module3.html')
        self.response.out.write(template.render(path, template_values))

class Module4Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/module4.html')
        self.response.out.write(template.render(path, template_values))

class Module5Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/module5.html')
        self.response.out.write(template.render(path, template_values))

class Module6Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/module6.html')
        self.response.out.write(template.render(path, template_values))

class ModuleXHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/moduleX.html')
        self.response.out.write(template.render(path, template_values))


# Quiz Page
class QuizQuestionsHandler(webapp.RequestHandler):
    def get(self):
        
        template_values = {}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/quizquestions.html')
        self.response.out.write(template.render(path, template_values))
# Quizzes Begin
class Quiz1Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Quiz1.html')
        self.response.out.write(template.render(path, template_values))



class Quiz2Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Quiz2.html')
        self.response.out.write(template.render(path, template_values))


###END OF QUIZ 2###
class Quiz3Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
                        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Quiz3.html')
        self.response.out.write(template.render(path, template_values))
        
###END OF QUIZ 3###
class Quiz4Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Quiz4.html')
        self.response.out.write(template.render(path, template_values))
class ConditionsHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/introIf.html')
        self.response.out.write(template.render(path, template_values))
###END OF QUIZ 4###
class Quiz5Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Quiz5.html')
        self.response.out.write(template.render(path, template_values))
        
###END OF QUIZ 5###
class Quiz6Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Quiz6.html')
        self.response.out.write(template.render(path, template_values))

###END OF QUIZ 6###
class Quiz7Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Quiz7.html')
        self.response.out.write(template.render(path, template_values))
        
###END OF QUIZ 7###
class Quiz8Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Quiz8.html')
        self.response.out.write(template.render(path, template_values))

###END OF QUIZ 8###
class Quiz9Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Quiz9.html')
        self.response.out.write(template.render(path, template_values))

class BookFilesHandler(webapp.RequestHandler):
    def get(self):
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        courses = getCourses()                    

        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor 2 Book: Create Your Own Android Apps',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
                           }
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/bookFiles.html')
        self.response.out.write(template.render(path, template_values))

###END OF QUIZ 9###


#Handlers created by Thomas Oropeza
#Handler for course in a box i have a dream worksheet
class IHDWorksheetHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/i_have_a_dream_worksheet.html')
        self.response.out.write(template.render(path, {}))
        
#Handlers for setup page in introduction course in a box
class SetupOptionsHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/setupOptions.html')
        self.response.out.write(template.render(path, {}))

class SetupPortfolioHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/setup_portfolio.html')
        self.response.out.write(template.render(path, {}))
class PCworksheethandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/PCworksheet.html')
        self.response.out.write(template.render(path, {}))
        
class AppMakerCardsHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/appMakerCards.html')
        self.response.out.write(template.render(path, {}))
class LessonPlan11Handler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/lessonplan11.html')
        self.response.out.write(template.render(path, {}))
class LessonPlan12Handler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/lessonplan12.html')
        self.response.out.write(template.render(path, {}))
class CCPaintPotHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/conceptCustomizePaintPot.html')
        self.response.out.write(template.render(path, template_values)) 
    
class IncrementingTimingWSHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/incrementingTimingWorksheet.html')
        self.response.out.write(template.render(path, {}))
class MoleMashCCHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/molemashCC.html')
        self.response.out.write(template.render(path, {}))
class AdvancedAnimationWSHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/AdvancedAnimationWorksheet.html')
        self.response.out.write(template.render(path, {}))
class LessonPlan21Handler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/lessonplan21.html')
        self.response.out.write(template.render(path, {}))
class LessonPlan22Handler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/lessonplan22.html')
        self.response.out.write(template.render(path, {}))
class LessonPlan23Handler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/lessonplan23.html')
        self.response.out.write(template.render(path, {}))
        
        
#Handlers for module 3 course in a box
class GoogleVoiceSetupHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/googlevoicesetup.html')
        self.response.out.write(template.render(path, {}))
class WhereAmIAppHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/whereamiapp.html')
        self.response.out.write(template.render(path, {}))
class ConceptCustomizeWSHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/ConceptualizeCustomizeTextingWS.html')
        self.response.out.write(template.render(path, template_values)) 
class LocationWSHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/LocationWorksheetCC.html')
        self.response.out.write(template.render(path, {}))
class LessonPlan31Handler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/Lessonplan31.html')
        self.response.out.write(template.render(path, {}))
class LessonPlan32Handler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/Lessonplan32.html')
        self.response.out.write(template.render(path, {}))
        
#Handlers for Module 4

class LIPHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/ListIndexPreTest.html')
        self.response.out.write(template.render(path, {}))
class IteratingListExample(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/IteratingThroughaList.html')
        self.response.out.write(template.render(path, {}))
class ListIndexCCHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/ListIndexCC.html')
        self.response.out.write(template.render(path, {}))
class IndexingChallengesHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/IndexingChallenges.html')
        self.response.out.write(template.render(path, {}))
class ListChoosingHandlers(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/ListListsChoosingList.html')
        self.response.out.write(template.render(path, {}))
class LessonPlan41Handler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/lessonplan41.html')
        self.response.out.write(template.render(path, {}))
class LessonPlan42Handler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/lessonplan42.html')
        self.response.out.write(template.render(path, {}))
class LessonPlan43Handler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/lessonplan43.html')
        self.response.out.write(template.render(path, {}))
#Handlers for Module 5
class NoteTakerTutHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/noteTaker.html')
        self.response.out.write(template.render(path, {}))
class SoundBoardAppHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/CustomizableSoundboard.html')
        self.response.out.write(template.render(path, {}))
class UserGeneratedDataHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/UserGeneratedDataCC.html')
        self.response.out.write(template.render(path, {}))
        
class IntroDrawingHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/introDrawingAnimation.html')
        self.response.out.write(template.render(path, template_values))  
        
class IntroTextingLocationHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/introTextingLocation.html')
        self.response.out.write(template.render(path, template_values)) 

class IntroQuizzesInformationHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/introQuizzesInformation.html')
        self.response.out.write(template.render(path, template_values)) 

class IntroProceduresHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/introProcedures.html')
        self.response.out.write(template.render(path, template_values)) 

class IntroUserGeneratedHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/introUserGenerated.html')
        self.response.out.write(template.render(path, template_values)) 
        
class IntroWebEnabledAppsHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/introWebEnabledApps.html')
        self.response.out.write(template.render(path, template_values)) 

class IntroIntroductionHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/introIntroduction.html')
        self.response.out.write(template.render(path, template_values))  
        
class IntroToProceduresHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/IntroductiontoProcedures.html')
        self.response.out.write(template.render(path, template_values))   

class ArrangingComponentsHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/arrangingComponents.html')
        self.response.out.write(template.render(path, template_values)) 

class AIDesignerHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/aidesigner.html')
        self.response.out.write(template.render(path, template_values)) 

class BlocksEditorHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/blocksEditor.html')
        self.response.out.write(template.render(path, template_values)) 

class CarouselTestHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/carousel2.html')
        self.response.out.write(template.render(path, {}))
        
class CanvasComponentHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/canvasComponent.html')
        self.response.out.write(template.render(path, template_values))
        
        
class CanvasComponentMasterNuggetHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/drawing-canvas.html')
        self.response.out.write(template.render(path, template_values))
        
class CanvasComponentMasterHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/drawing-canvas.html')
        self.response.out.write(template.render(path, template_values))
        
        
class CanvasPropertiesHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/canvasProperties.html')
        self.response.out.write(template.render(path, template_values)) 
class CanvasComponentNuggetHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/canvasComponent.html')
        self.response.out.write(template.render(path, {})) 
class VariablesCirclesNuggetHandler(webapp.RequestHandler):
    def get(self, *args):
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/variablesCircleNugget.html')
        self.response.out.write(template.render(path, {})) 

class VariableCircleMasterHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/variablesHowDoYou.html')
        self.response.out.write(template.render(path, template_values))


class RememberThingsHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/howAppsRememberThings.html')
        self.response.out.write(template.render(path, template_values)) 
class PaintPotTextHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/paintPotText.html')
        self.response.out.write(template.render(path, template_values)) 
        
class HowGamesWorkHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/howGamesWork.html')
        self.response.out.write(template.render(path, template_values)) 
class IncrementingWSHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/incrementing.html')
        self.response.out.write(template.render(path, template_values))
class TimerEventHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/timerevent.html')
        self.response.out.write(template.render(path, template_values))
        
        
class MoleMashTextHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/molemashtext.html')
        self.response.out.write(template.render(path, template_values))



###END OF QUIZ 9###

# Java Bridge

class JBridgeIntroHandler(webapp.RequestHandler):
     def get(self, *args):
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = {
            'userStatus': userStatus,
            'stylesheets' : ['/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
            'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/jbridgeintro.js', '/assets/js/ytexpo.js'],
            'courseToModules' : getCoursesAndModules()
        }
        

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/jBridgeIntro.html')
        self.response.out.write(template.render(path, template_values))

class AIAnimationHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/aianimation.html')
        self.response.out.write(template.render(path, template_values))
     

       
class JBridgeRedClickEclipseHandler(webapp.RequestHandler):
    def get(self, *args):
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/jBridgeRedClickEclipse.html')
        self.response.out.write(template.render(path, template_values))

        
class HowAnimationworksHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/howanimationworks.html')
        self.response.out.write(template.render(path, template_values))
       
class JBridgeRedClickAndroidHandler(webapp.RequestHandler):
    def get(self, *args):
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/jBridgeRedClickAndroid.html')
        self.response.out.write(template.render(path, template_values))

class AnimationChallengeBrianHandler(webapp.RequestHandler):
     def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/animationchallengebrian.html')
        self.response.out.write(template.render(path, template_values))

class AnimationChallengeHelpHandler(webapp.RequestHandler):
     def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/animationChallengeHelp.html')
        self.response.out.write(template.render(path, template_values))

class JBridgeBasicsHandler(webapp.RequestHandler):
    def get(self, *args):
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/jBridgeBasics.html')
        self.response.out.write(template.render(path, template_values))

class AnimationChallengeInternalHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/AnimationChallengeInternal.html')
        self.response.out.write(template.render(path, template_values))
        
class JBridgeMoleMashHandler(webapp.RequestHandler):
     def get(self, *args):
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/jBridgeMoleMash.html')
        self.response.out.write(template.render(path, template_values))

class AnimationIntComponentHandler(webapp.RequestHandler):
     def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/AnimationInternalComponents.html')
        self.response.out.write(template.render(path, template_values))

class JBridgePaintPotHandler(webapp.RequestHandler):
     def get(self, *args):
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/jBridgePaintPot.html')
        self.response.out.write(template.render(path, template_values))
  
class JBridgePrezQuiz(webapp.RequestHandler):      
     def get(self, *args):
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/java_bridge/US-Presidents-Quiz.html')
        self.response.out.write(template.render(path, template_values))

class JBridgeStockMarket(webapp.RequestHandler):      
     def get(self, *args):
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/java_bridge/Stock-Market-Tracker.html')
        self.response.out.write(template.render(path, template_values))
  
  
  

class PongTutorialHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/pongTutorial.html')
        self.response.out.write(template.render(path, template_values))

# LESSON PLANS

class LPIntroHandler(webapp.RequestHandler):
    def get(self):
        

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/lesson_plans/ai_introduction.html')
        self.response.out.write(template.render(path, template_values))

class LPCreatingHandler(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/lesson_plans/creating.html')
        self.response.out.write(template.render(path, template_values))

class LPConceptsHandler(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/lesson_plans/programming_concepts.html')
        self.response.out.write(template.render(path, template_values))

class LPAugmentedHandler(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/lesson_plans/augmented.html')
        self.response.out.write(template.render(path, template_values))

class LPGamesHandler(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/lesson_plans/games.html')
        self.response.out.write(template.render(path, template_values))

class LPIteratingHandler(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/lesson_plans/iterating.html')
        self.response.out.write(template.render(path, template_values))

class LPUserGenHandler(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/lesson_plans/user_gen_data.html')
        self.response.out.write(template.render(path, template_values))

class LPForeachHandler(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/lesson_plans/foreach.html')
        self.response.out.write(template.render(path, template_values))

class LPPersistenceWorksheetHandler(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/lesson_plans/persistence_worksheet.html')
        self.response.out.write(template.render(path, template_values))

class LPPersistenceFollowupHandler(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/lesson_plans/persistence_followup.html')
        self.response.out.write(template.render(path, template_values))

class LPFunctionsHandler(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/lesson_plans/functions.html')
        self.response.out.write(template.render(path, template_values))

class LPCodeReuseHandler(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/lesson_plans/code_reuse.html')
        self.response.out.write(template.render(path, template_values))

class LPQRHandler(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/lesson_plans/qr_code.html')
        self.response.out.write(template.render(path, template_values))

class BookHandler(webapp.RequestHandler):
    def get(self):
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        courses = getCourses()                    

        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor 1 Book: Create Your Own Android Apps',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/book.html')
        self.response.out.write(template.render(path, template_values))
        
class Book2Handler(webapp.RequestHandler):
    def get(self):
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        courses = getCourses()                    

        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor 2 Book: Create Your Own Android Apps',
                           'stylesheets' : [],
                           'scripts' : ['/assets/js/coursesystem.js'],
                           'courseToModules' : getCoursesAndModules()
                           }
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/book2.html')
        self.response.out.write(template.render(path, template_values))

# Inventor's Manual Handlers #

class Handler14(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), '/assets/pdf/chapter14.html')
        self.response.out.write(template.render(path, template_values))

class Handler15(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), '/assets/pdf/chapter15.html')
        self.response.out.write(template.render(path, template_values))

class Handler16(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), '/assets/pdf/chapter16.html')
        self.response.out.write(template.render(path, template_values))

class Handler17(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), '/assets/pdf/chapter17.html')
        self.response.out.write(template.render(path, template_values))

class Handler18(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), '/assets/pdf/chapter18.html')
        self.response.out.write(template.render(path, template_values))

class Handler19(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), '/assets/pdf/chapter19.html')
        self.response.out.write(template.render(path, template_values))

class Handler20(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), '/assets/pdf/chapter20.html')
        self.response.out.write(template.render(path, template_values))

class Handler21(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), '/assets/pdf/chapter21.html')
        self.response.out.write(template.render(path, template_values))

class Handler22(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), '/assets/pdf/chapter22.html')
        self.response.out.write(template.render(path, template_values))

class Handler23(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), '/assets/pdf/chapter23.html')
        self.response.out.write(template.render(path, template_values))

class Handler24(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), '/assets/pdf/chapter24.html')
        self.response.out.write(template.render(path, template_values))









# ADMIN







class AddAppHandler(webapp.RequestHandler):
    def get(self):
        
        # login_url=users.create_login_url(self.request.uri)
        #       logout_url=users.create_logout_url(self.request.uri)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'addapp.html')
        self.response.out.write(template.render(path, template_values))

class AddStepHandler(webapp.RequestHandler):
    def get(self):
        
        # login_url=users.create_login_url(self.request.uri)
        #       logout_url=users.create_logout_url(self.request.uri)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'admin_step.html')
        self.response.out.write(template.render(path, template_values))

class AddConceptHandler(webapp.RequestHandler):
    def get(self):
        
        # login_url=users.create_login_url(self.request.uri)
        #       logout_url=users.create_logout_url(self.request.uri)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'addconcept.html')
        self.response.out.write(template.render(path, template_values))

class AddCustomHandler(webapp.RequestHandler):
    def get(self):
        
        # login_url=users.create_login_url(self.request.uri)
        #       logout_url=users.create_logout_url(self.request.uri)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'addcustom.html')
        self.response.out.write(template.render(path, template_values))
        
class PostStep(webapp.RequestHandler):
    def post(self):
        stepId = self.request.get('modify_step_name')  # the ID is a header


        if (stepId):
            cacheHandler = CacheHandler()
            step = cacheHandler.GettingCache("Step", True, "header", stepId, False, None, None, False)

        else:
            step = Step()

        if self.request.get('appId'):
            step.appId = self.request.get('appId')

        if self.request.get('number'):
            step.number = int(self.request.get('number'))

        if self.request.get('header'):
            step.header = self.request.get('header')

        if self.request.get('copy'):
            step.copy = self.request.get('copy')

        if self.request.get('videoPath'):
            step.videoPath = self.request.get('videoPath')

        if self.request.get('fullscreenPath'):
            step.fullscreenPath = self.request.get('fullscreenPath')

        step.put()

        # flush all the memcache
        memcache.flush_all()  

        self.redirect('/AddStepPage?add_step_app_name=' + step.appId)  # TODO: change to admin or app area


class PostCustom(webapp.RequestHandler):
    def post(self):

        customId = self.request.get('modify_custom_name')  # the ID is a header


        if (customId):
            cacheHandler = CacheHandler()
            custom = cacheHandler.GettingCache("Custom", True, "header", customId, False, None, None, False)

        else:
            custom = Custom()

        if self.request.get('appId'):
            custom.appId = self.request.get('appId')

        if self.request.get('number'):
            custom.number = int(self.request.get('number'))

        if self.request.get('header'):
            custom.header = self.request.get('header')

        if self.request.get('copy'):
            custom.copy = self.request.get('copy')

        if self.request.get('videoPath'):
            custom.videoPath = self.request.get('videoPath')

        if self.request.get('fullscreenPath'):
            custom.fullscreenPath = self.request.get('fullscreenPath')

        custom.put()

        # flush all the memcache
        memcache.flush_all()
        
        self.redirect('/AddCustomPage?add_custom_app_name=' + custom.appId)



class AddCustomRenderer(webapp.RequestHandler):
    def get(self):
        custom_listing = ""

        appId = self.request.get('add_custom_app_name')
        cacheHandler = CacheHandler()
        app = cacheHandler.GettingCache("App", True, "appId", appId, False, None, None, False)
        appTitle = app.title

        cacheHandler = CacheHandler()
        customs = cacheHandler.GettingCache("Custom", True, "appId", appId, True, "number", "ASC", True)
   
        for custom in customs:
            custom_listing += str(custom.number) + '. ' + custom.header + '|'

        template_values = {
            'appId': appId,
            'appTitle': appTitle,
            'custom_listing': custom_listing
        }

        path = os.path.join(os.path.dirname(__file__), 'static_pages/admin/admin_custom.html')
        self.response.out.write(template.render(path, template_values))

class PostApp(webapp.RequestHandler):
    def post(self):

        appId = self.request.get('modify_app_name')

        if (appId):
            cacheHandler = CacheHandler()
            app = cacheHandler.GettingCache("App", True, "appId", appId, False, None, None, False)
        else:
            app = App()

        if self.request.get('appNumber'):
            app.number = int(self.request.get('appNumber'))

        if self.request.get('appId'):
            app.appId = self.request.get('appId')

        if self.request.get('title'):
            app.title = self.request.get('title')

        if self.request.get('heroCopy'):
            app.heroCopy = self.request.get('heroCopy')

        if self.request.get('heroHeader'):
            app.heroHeader = self.request.get('heroHeader')
            
        if self.request.get('pdfChapter'):
            b = self.request.get('pdfChapter')
            if(b == "True"):
                app.pdfChapter = True
            else:
                app.pdfChapter = False
                
        if self.request.get('conceptualLink'):
            b = self.request.get('conceptualLink')
            if(b == "True"):
                app.conceptualLink = True
            else:
                app.conceptualLink = False

        if self.request.get('webTutorial'):
            b = self.request.get('webTutorial')
            if(b == "True"):
                if self.request.get('webTutorialLink'):
                    app.webTutorialLink = self.request.get('webTutorialLink')
                    app.webTutorial = True
                else:
                    app.webTutorial = False
            else:
                app.webTutorial = False

        if (self.request.get('manyMold').strip() != ''):
            app.manyMold = self.request.get('manyMold')

        if (self.request.get('version').strip() != ''):
            app.version = self.request.get('version')
            

        app.put()  # now the app has a key() --> id()

        # flush all the memcache
        memcache.flush_all()
        
        self.redirect('/admin/apps')  # TODO: change to /admin (area)
        # wherever we put() to datastore, we'll need to also save the appId

class DeleteApp(webapp.RequestHandler):
    def get(self):
        appId = self.request.get('del_app_name')
        logging.info("appId is " + appId)

        query = db.GqlQuery("SELECT * FROM App WHERE appId = :1", appId).get()
        db.delete(query)

#                app_to_del = db.GqlQuery("SELECT * FROM App WHERE appId = :1", appId)
#                result = app_to_del.get()
#                db.delete(result)


        # flush all the memcache
        memcache.flush_all()
        
        self.redirect('/Admin')

class DeleteStep(webapp.RequestHandler):
    def get(self):
        logging.info("hello world")
        stepId = self.request.get('del_step_name')  # this id is actually step header, should be re-thinked later
        stepId = self.request.get('del_step_name')  # this id is actually step header, should be re-thinked later
        
        logging.info("stepId is " + stepId)

        query = db.GqlQuery("SELECT * FROM Step WHERE header = :1", stepId).get()
        appID = query.appId
        db.delete(query)


        # flush all the memcache
        memcache.flush_all()

        self.redirect('/AddStepPage?add_step_app_name=' + appID)







class AddStepRenderer(webapp.RequestHandler):
    def get(self):
        step_listing = ""

        appId = self.request.get('add_step_app_name')
        cacheHandler = CacheHandler()
        app = cacheHandler.GettingCache("App", True, "appId", appId, False, None, None, False)
        appTitle = app.title


        cacheHandler = CacheHandler()
        steps = cacheHandler.GettingCache("Step", True, "appId", appId, True, "number", "ASC", True)
        
        for step in steps:
            step_listing += str(step.number) + '. ' + step.header + '|'

        template_values = {
            'appId': appId,
            'appTitle': appTitle,
            'step_listing': step_listing
        }

        path = os.path.join(os.path.dirname(__file__), 'static_pages/admin/admin_step.html')
        self.response.out.write(template.render(path, template_values))





        
class AdminHandler(webapp.RequestHandler):
    def get(self):
        

        app_listing = ""
        app_listing2 = ""
        tutorials_listing = ""

        cacheHandler = CacheHandler()
        apps = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        apps2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

        tutorials = cacheHandler.GettingCache("Tutorial", False, None, None, True, "number", "ASC", True)
        # apps = apps + apps2

        for app in apps:
            app_listing += app.appId + '|'
        for app in apps2:
            app_listing2 += app.appId + '|'
        for tutorial in tutorials:
            tutorials_listing += tutorial.tutorialId + '|'

        template_values = {
            
            'app_listing': app_listing,
            'app_listing2': app_listing2,
            'tutorials_listing': tutorials_listing
        }
        path = os.path.join(os.path.dirname(__file__), 'static_pages/admin/admin_main.html')
        self.response.out.write(template.render(path, template_values))





class AppRenderer(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        path = self.request.path
        t_path = path[1:]
        logging.info(t_path)
        cacheHandler = CacheHandler()
        app = cacheHandler.GettingCache("App", True, "appId", t_path, False, None, None, False)
        # logging.info(app.heroCopy)

            
        steps = cacheHandler.GettingCache("Step", True, "appId", t_path, True, "number", "ASC", True)    
        customs = cacheHandler.GettingCache("Custom", True, "appId", t_path, True, "number", "ASC", True)

        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)


        if(app.version == '1'):
            currentAppsDir = APPSDIR
        elif(app.version == '2'):
            currentAppsDir = APPS2DIR

        template_values = {
            'steps': steps,
            'customs': customs,
            'app': app,
            'userStatus': userStatus,
            'allAppsList': allAppsList,
            'allAppsList2': allAppsList2,
            'currentAppsDir':currentAppsDir
            }

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/app_base.html')
        self.response.out.write(template.render(path, template_values))

class NewAppRenderer(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        path = self.request.path
        # t_path = path[1:]
        t_path = path[1:(len(path) - 6)]  # take out -steps in path
        

        
        
        user = users.get_current_user()
        pquery = db.GqlQuery("SELECT * FROM Account where user= :1 ", user)
        account = pquery.get()



        cacheHandler = CacheHandler()
        app = cacheHandler.GettingCache("App", True, "appId", t_path, False, None, None, False)
        # logging.info(app.heroCopy)

            
        steps = cacheHandler.GettingCache("Step", True, "appId", t_path, True, "number", "ASC", True)    
        customs = cacheHandler.GettingCache("Custom", True, "appId", t_path, True, "number", "ASC", True)

        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

   
        # check if reach the last one
        try:
            nextApp = allAppsList[app.number]
        except:
            nextApp = None
            
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)

        # comment
        pquery = db.GqlQuery("SELECT * FROM Comment WHERE appId = :1 ORDER BY timestamp DESC", t_path)  # t_path is appID
        # pquery = db.GqlQuery("SELECT * FROM Comment")
        comments = pquery.fetch(pquery.count())

        template_values = {
            'steps': steps,
            'customs': customs,
            'app': app,
            'allAppsList': allAppsList, 'allAppsList2': allAppsList2,
            'userStatus': userStatus,
            'nextApp':nextApp,
            'comments': comments,
            'currentAppsDir':APPSDIR
            }

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/app_base_new.html')
        self.response.out.write(template.render(path, template_values))

class NewAppRenderer_AI2(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        path = self.request.path
        # t_path = path[1:]
        t_path = path[1:(len(path) - 6)]  # take out -steps in path
        
        user = users.get_current_user()
        pquery = db.GqlQuery("SELECT * FROM Account where user= :1 ", user)
        account = pquery.get()



        cacheHandler = CacheHandler()
        app = cacheHandler.GettingCache("App", True, "appId", t_path, False, None, None, False)
        # logging.info(app.heroCopy)

            
        steps = cacheHandler.GettingCache("Step", True, "appId", t_path, True, "number", "ASC", True)    
        customs = cacheHandler.GettingCache("Custom", True, "appId", t_path, True, "number", "ASC", True)

        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # check if forward to the first one
        try:
            if(app.number - 2 >= 0):
                previousApp = allAppsList2[app.number - 2]
            else:
                previousApp = None
        except:
            previousApp = None

        # check if reach the last one
        try:
            nextApp = allAppsList2[app.number]
        except:
            nextApp = None
            
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)

        # comment
        pquery = db.GqlQuery("SELECT * FROM Comment WHERE appId = :1 ORDER BY timestamp DESC", t_path)  # t_path is appID
        # pquery = db.GqlQuery("SELECT * FROM Comment")
        comments = pquery.fetch(pquery.count())

        template_values = {
            'steps': steps,
            'customs': customs,
            'app': app,
            'allAppsList': allAppsList, 'allAppsList2': allAppsList2,
            'allAppsList2':allAppsList2,
            'userStatus': userStatus,
            'previousApp': previousApp,
            'nextApp':nextApp,
            'comments': comments,
            'currentAppsDir':APPS2DIR
            }

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/app_base_new.html')
        self.response.out.write(template.render(path, template_values))

# commenting system
class PostCommentHandler (webapp.RequestHandler):
    def post(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)

        user = users.get_current_user()

        if not user:
            self.redirect(userStatus['loginurl'])

        content = self.request.get('comment_content').strip(' \t\n\r')
        if(content != ''):
            user = users.get_current_user()
            pquery = db.GqlQuery("SELECT * FROM Account where user= :1 ", user)
            account = pquery.get()
            if not account:
                account = Account()
                account.user = user
                account.displayName = str(user.nickname())
                account.put()
            comment = Comment()
            comment.submitter = account
            comment.content = content
            comment.appId = self.request.get('comment_appId')
            if(self.request.get('comment_replyTo')):
                comment.replyTo = db.get(self.request.get('comment_replyTo'))
                # comment.replyTo = self.request.get('comment_replyTo')
            comment.put()
            emailHandler = EmailHandler()
            emailHandler.sendToAdmin(self.request.get('redirect_link'), comment)

        
        self.redirect(self.request.get('redirect_link'))
class DeleteCommentHandler (webapp.RequestHandler):
    def get(self):
        

        user = users.get_current_user()
        
        

        if users.is_current_user_admin():
            commentKey = self.request.get('commentKey')
            if(commentKey != ""):
                # check all comments see if there exists comment/comments that references to the above one.
                pquery = db.GqlQuery("SELECT * FROM Comment") 
                comments = pquery.fetch(pquery.count())
                for comment in comments:
                    if comment.replyTo: 
                        if (str(comment.replyTo.key()) == str(commentKey)):
                            comment.replyTo = None
                            comment.put()
                db.delete(commentKey)
            self.redirect(self.request.get('redirect_link'))
        else:
            
            print 'Content-Type: text/plain'
            print 'You are NOT administrator'
        
 

class DCLHandler(webapp.RequestHandler):
    def get(self):
        courses = getCourses()                    
                    
        userStatus = UserStatus().getStatus(self.request.uri)
        
        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'About Us',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/dcl.html')
        self.response.out.write(template.render(path, template_values))

class GetAppDataHandler(webapp.RequestHandler):
    def get(self):
        logging.info("I'm inside get_app_data()")
        app = self.request.get('app')
        cacheHandler = CacheHandler()        
        app_to_get = cacheHandler.GettingCache("App", True, "appId", app, False, None, None, False)

        appId = app

        number = app_to_get.number;
        title = app_to_get.title;
        heroHeader = app_to_get.heroHeader;
        heroCopy = app_to_get.heroCopy;
        pdfChapter = app_to_get.pdfChapter;
        webTutorial = app_to_get.webTutorial;
        webTutorialLink = app_to_get.webTutorialLink;
        conceptualLink = app_to_get.conceptualLink;
        manyMold = app_to_get.manyMold;
        version = app_to_get.version;

        my_response = {'number': number, 'title': title, 'heroHeader': heroHeader, 'heroCopy': heroCopy, 'pdfChapter':pdfChapter, 'webTutorial': webTutorial, 'webTutorialLink': webTutorialLink, 'conceptualLink': conceptualLink, 'manyMold': manyMold, "version": version}
#        json = JSON.dumps(my_response)

        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
        self.response.out.write(json.dumps(my_response))


class GetStepDataHandler(webapp.RequestHandler):
    def get(self):
        logging.info("I'm inside get_step_data()")
        step_header = self.request.get('step_header')
        cacheHandler = CacheHandler()
        step = cacheHandler.GettingCache("Step", True, "header", step_header, False, None, None, False)

        appId = step.appId;
        number = step.number;
        header = step.header;
        copy = step.copy;
        videoPath = step.videoPath;
        fullPath = step.fullscreenPath;

        my_response = {'appId': appId, 'number': number, 'header': header, 'copy': copy, 'videoPath': videoPath, 'fullPath': fullPath}
        #        json = JSON.dumps(my_response)

        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
        self.response.out.write(json.dumps(my_response))

class GetCustomDataHandler(webapp.RequestHandler):
    def get(self):
        logging.info("I'm inside get_custom_data()")
        custom_header = self.request.get('custom_header')
        logging.info("custom_header: " + custom_header)
        cacheHandler = CacheHandler()
        custom = cacheHandler.GettingCache("Custom", True, "header", custom_header, False, None, None, False)

        number = custom.number;
        header = custom.header;
        copy = custom.copy;
        videoPath = custom.videoPath;
        fullPath = custom.fullscreenPath;

        my_response = {'number': number, 'header': header, 'copy': copy, 'videoPath': videoPath, 'fullPath': fullPath}
        #        json = JSON.dumps(my_response)

        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
        self.response.out.write(json.dumps(my_response))

class SetupHandler(webapp.RequestHandler):
    def get(self):

        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 
            'allAppsList': allAppsList,
            'allAppsList2': allAppsList2,
            'userStatus': userStatus,
            'courseToModules' : getCoursesAndModules()
        }

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/setup2.html')
        self.response.out.write(template.render(path, template_values))

class SetupAI2Handler(webapp.RequestHandler):
    def get(self):

        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/setupAI2.html')
        self.response.out.write(template.render(path, template_values))

class TryItHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)


        manyMoldAppsList = []
        for app in allAppsList:
            if app.manyMold:
                manyMoldAppsList.append(app)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
       
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'manyMoldAppsList': manyMoldAppsList}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/tryit.html')
        self.response.out.write(template.render(path, template_values))


# Upload Pic
class UploadPictureHandler(webapp.RequestHandler):
    def post(self):
                
        picture = self.request.get('pictureFile')

        user = users.get_current_user()
        account_query = db.GqlQuery("Select * from Account where user=:1", user)
        account = account_query.get()



        x1 = float(self.request.get('x1'))
        y1 = float(self.request.get('y1'))
        x2 = float(self.request.get('x2'))
        y2 = float(self.request.get('y2'))
        newH = float(self.request.get('h'))
        newW = float(self.request.get('w'))

        x_left = float(self.request.get('x_left'))
        y_top = float(self.request.get('y_top'))
        x_right = float(self.request.get('x_right'))
        y_bottom = float(self.request.get('y_bottom'))

        originalW = x_right - x_left
        originalH = y_bottom - y_top

        # originalW = 300
        # originalH = 300

        


        x1_fixed = x1 - x_left
        y1_fixed = y1 - y_top
        x2_fixed = x2 - x_left
        y2_fixed = y2 - y_top


        if(x1_fixed < 0):
            x1_fixed = 0
        if(y1_fixed < 0):
            y1_fixed = 0
        if(x2_fixed > originalW):
            x2_fixed = originalW
        if(y2_fixed > originalH):
            y2_fixed = originalH


        picture = images.crop(picture, float(x1_fixed / originalW), float(y1_fixed / originalH), float(x2_fixed / originalW), float(y2_fixed / originalH))
        picture = images.resize(picture, 300, 300)

        if not account:
            account = Account()
            account.displayName = str(user.nickname())
        if picture:
            account.user = user  # maybe duplicate, but it is really imporant to make sure
            account.profilePicture = db.Blob(picture)  
        account.put()
        ad = picture
        self.redirect('/changeProfile')
                

class ImageHandler (webapp.RequestHandler):
    def get(self):
                    
        account_key = self.request.get('key')

        if(len(account_key) == 0):
            self.redirect('/assets/img/avatar-default.gif')
            return    

        account = db.get(account_key)
        if account.profilePicture:
            self.response.headers['Content-Type'] = "image/png"
            self.response.out.write(account.profilePicture)
        else:
            self.redirect('/assets/img/avatar-default.gif')
            

# gets JSON string with data for map
class getEducatorsInfo(webapp.RequestHandler):
    def get(self):
        allTeachers = db.GqlQuery("SELECT * FROM Account WHERE ifEducator=:1", True)
        teachers = {"teachers" : []}
        for teacher in allTeachers:    
            teacherDict = {}
            teacherDict["name"] = teacher.firstName + " " + teacher.lastName
            teacherDict["coord"] = {"lat" : teacher.latitude, "long" : teacher.longitude}
            teacherDict["educationLevel"] = teacher.educationLevel
            teacherDict["organization"] = teacher.organization
            teacherDict["introductionLink"] = teacher.introductionLink
            teachers["teachers"].append(teacherDict)
        self.response.out.write(json.dumps(teachers, ensure_ascii=False))
        
class getEducatorsTiles(webapp.RequestHandler):
    def get(self):
        
        k8Teachers = db.GqlQuery("SELECT * FROM Account WHERE ifEducator=:1 AND educationLevel='K-8'", True)
        hsTeachers = db.GqlQuery("SELECT * FROM Account WHERE ifEducator=:1 AND educationLevel='High School'", True)
        cTeachers = db.GqlQuery("SELECT * FROM Account WHERE ifEducator=:1 AND educationLevel='College/University'", True)
        # only show profiles that have pictures
        # for the section below the map
        k8WithPic = []
        for teacher in k8Teachers:
            if teacher.profilePicture:
                k8WithPic.append(teacher)
        hsWithPic = []
        for teacher in hsTeachers:
            if teacher.profilePicture:
                hsWithPic.append(teacher)
        cWithPic = []
        for teacher in cTeachers:
            if teacher.profilePicture:
                cWithPic.append(teacher)                            

        template_values = {
                           'k8Teachers' : k8WithPic,
                           'hsTeachers' : hsWithPic,
                           'cTeachers' : cWithPic
                           }                                     
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/teacherTilesTemplate.html')
        self.response.out.write(template.render(path, template_values))            
                
            
class TeacherMapHandler(webapp.RequestHandler):
    def get(self):
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
                                                                      
        courses = getCourses()                    
                    
        userStatus = UserStatus().getStatus(self.request.uri)        


        template_values = { 'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'Who is teaching App Inventor',
                           'stylesheets' : ['/assets/css/coursesystem.css'],
                           'scripts' : [ ], # this page places the scripts on top, so the map loads first                    
                           'userStatus': userStatus,
                           'courseToModules' : getCoursesAndModules(),
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/AIEducators.html')
        self.response.out.write(template.render(path, template_values))               
               
# Google Custom Search
class SearchHandler (webapp.RequestHandler):
    def get(self):
        
        query = self.request.get("q")
        logging.info(query)
        courses = getCourses()                    
                    
        userStatus = UserStatus().getStatus(self.request.uri)
        
        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'Search Results: ' + query,
                           'stylesheets' : ['/assets/css/coursesystem.css'],
                           'scripts' : [],
                           'query' : query,
                           'courseToModules' : getCoursesAndModules(),
                           }
           
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/searchResult.html')
        self.response.out.write(template.render(path, template_values))


# Cache

class CacheHandler(webapp.RequestHandler):

    def GettingCache(self, tableName, whereClause, whereField, dataId, orderClause, orderField, orderValue, fetch):
        keyName = tableName.lower()
        if(whereClause == True):
            keyName = keyName + dataId

        expiredTime = 86400
        data = memcache.get(keyName)

        if data is not None:
            return data
        else:
            query = self.createDBQuery(tableName, whereClause, whereField, dataId, orderClause, orderField, orderValue)
            if(whereClause == True):
                datasQuery = db.GqlQuery(query, dataId)
            else:
                datasQuery = db.GqlQuery(query)

            if(fetch == False):
                data = datasQuery.get()
            else:
                data = datasQuery.fetch(datasQuery.count())
            
            memcache.add(keyName, data, expiredTime)
            return data
  

    def createDBQuery(self, tableName, whereClause, whereField, dataId, orderClause, orderField, orderValue):
         
        query1 = "SELECT * FROM " + tableName + " "
        if(whereClause == True):
            query2 = "WHERE " + whereField + " =:1 "
        else:
            query2 = ""
        if(orderClause == True):
            query3 = "ORDER BY " + orderField + " " + orderValue
        else:
            query3 = ""

        return query1 + query2 + query3

class MemcacheFlushHandler(webapp.RequestHandler):

    def get(self):
        memcache.flush_all()       
       
        if users.is_current_user_admin():
            if(self.request.get('redirect_link')):  # implemented now, it is not required
                self.redirect(self.request.get('redirect_link'))
            else:
                self.redirect("/Admin")
        else:        
            print 'Content-Type: text/plain'
            print 'You are NOT administrator'        
        return


# user status checking(login/logout)
class UserStatus(webapp.RequestHandler):   
    def getStatus(self, uri):
        user = users.get_current_user()
        pquery = db.GqlQuery("SELECT * FROM Account where user= :1 ", user)
        account = pquery.get()

        loginurl = users.create_login_url('/loginValidator')
        logouturl = users.create_logout_url('/')

        isAccount = False
        logging.info(account)
        if user and account:
            logging.info("user has an account!")
            isAccount = True
        else:
            logging.info("user does not have an account!")
            

        admin = False
        if user:
            ifUser = True
            if users.is_current_user_admin():
                admin = True
        else:
            ifUser = False

        status = {'loginurl': loginurl, 'logouturl':logouturl, 'ifUser':ifUser, 'account':account, 'isAccount' : isAccount, 'admin': admin}
        return status


class loginValidationHandler(webapp.RequestHandler):
    def get(self):
        # check to see if the user that just signed in has an account
        # if they do not have an account redirect them the account creation page
        # if they have an account redirect them to the homepage
        
        user = users.get_current_user()
        if not user:
            # not signed into google account, once signed in retry
            # validation
            self.redirect(users.create_login_url('/loginValidator'))
            return None
        
        # check if user has an account
        pquery = db.GqlQuery("SELECT * FROM Account where user= :1 ", user)
        account = pquery.get()
        
        if account:
            # account was found, redirect to home
            self.redirect("/")
            return None
        else:
            # no account was found redirect to account creation page
            self.redirect("/createAccount")
            return None

class CreateAccountHandler(webapp.RequestHandler):
    def get(self):
        courses = getCourses()                                
        userStatus = UserStatus().getStatus(self.request.uri)
        
        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'Register an Account',
                           'stylesheets' : ['/assets/css/coursesystem.css'],
                           'scripts' : ['/assets/js/accountRegisteration.js'],
                           }
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/accountregistration.html')
        self.response.out.write(template.render(path, template_values))        

class updateAccountHandler(webapp.RequestHandler):
    def post(self):
        logging.info("updateAccountHandlercalled!!!!!!!!!!")
        firstName = self.request.get('sfirstName');
        lastName = self.request.get('slastName');
        displayName = self.request.get('sdisplayName')
        isEducator = self.request.get('sisEducator')
        organization = self.request.get('sorganization')
        educationLevel = self.request.get('seducationLevel')
        website = self.request.get('swebsite')        
        location = self.request.get('slocation')      
       
        # retrieve account
        user = users.get_current_user()
        pquery = db.GqlQuery("SELECT * FROM Account where user= :1 ", user)
        account = pquery.get()
        
       

                
        if not account:
            # no account was found redirect to account creation page
            self.redirect("/createAccount")
            return None
        
        account.user = user
        account.firstName = firstName
        account.lastName = lastName
        account.location = location
        
        if isEducator == "true":
            account.ifEducator = True
        else:
            account.ifEducator = False
            
        
        # attempt to geocode location
        
        logging.info("about to try geocoder!")
        g = geocoders.GoogleV3()
        if account.location:
            try:             
                place, (lat, lng) = g.geocode(account.location)
                account.latitude = lat
                account.longitude = lng
            except:
                logging.error("failed to gecode location for " + str(displayName))
        
        account.educationLevel = educationLevel
        account.organization = organization
        account.introductionLink = website
        account.displayName = displayName  
        account.put()
        self.redirect("/")
        
    


class RegisterAccountHandler(webapp.RequestHandler):
    def post(self):
        firstName = self.request.get('sfirstName');
        lastName = self.request.get('slastName');
        displayName = self.request.get('sdisplayName')
        isEducator = self.request.get('sisEducator')
        organization = self.request.get('sorganization')
        educationLevel = self.request.get('seducationLevel')
        website = self.request.get('swebsite')        
        location = self.request.get('slocation')       
        # validation occurs here
        # TODO: validation!
        
        
        # actual creation of account happens here
        user = users.get_current_user()
        account = Account()
        account.user = user
        account.firstName = firstName
        account.lastName = lastName
        account.location = location
        
        if isEducator == "true":
            account.ifEducator = True
        else:
            account.ifEducator = False
            
        
        # attempt to geocode location
        
        logging.info("about to try geocoder!")
        g = geocoders.GoogleV3()
        if account.location:
            try:             
                place, (lat, lng) = g.geocode(account.location)
                account.latitude = lat
                account.longitude = lng
            except:
                logging.error("failed to gecode location for " + str(displayName))
        
        account.organization = organization
        account.introductionLink = website
        account.displayName = displayName  
        account.put()
        
        
# only use when add new field to database
class UpdateDatabase (webapp.RequestHandler):
    def get(self):
        adam_boolean = true
        pquery = db.GqlQuery("SELECT * FROM Comment")
        comments = pquery.fetch(pquery.count())
        
        for comment in comments:
            if comment.replyTo:
                parent = comment.replyTo
                child = comment
                parent.replayFrom = child
                
    
    def bacup3(self):
      # this is from adam
        adam_boolean = True
        pquery = db.GqlQuery("SELECT * FROM Account")
        accounts = pquery.fetch(pquery.count())
        for account in accounts:
            b = False
            if account.lastName == None:
                account.lastName = ""
                b = True
                print account.displayName
            if account.firstName == None:
                account.firstName = ""
                b = True
            if account.location == None:
                account.location = ""
                b = True
            if account.organization == None:
                account.organization = ""
                b = True
            if(b == True):
                account.put()
        
    def backup2(self):

        pquery = db.GqlQuery("SELECT * FROM Account")
        accounts = pquery.fetch(pquery.count())
        
        for account in accounts:
            old = account.displayName
            i = old.find('@')
            if (i != -1):
               account.displayName = old[:i]
               account.put()

        return
    def backup(self):
        pquery = db.GqlQuery("SELECT * FROM Account")
        accounts = pquery.fetch(pquery.count())

        for account in accounts:
            if account.introductionLink:
                link = account.introductionLink
                if(len(link.strip()) == 0):
                    account.introductionLink = ''
                else:
                    link = link.replace("http://", "")
                    link = link.replace("https://", "")
                    account.introductionLink = link
                account.put()

        return
        
class UpdateGEODatabase (webapp.RequestHandler):
    def get(self):

        pquery = db.GqlQuery("SELECT * FROM Account")
        accounts = pquery.fetch(pquery.count())
        g = geocoders.GoogleV3()
        for account in accounts:
            if account.location:
                try:             
                    place, (lat, lng) = g.geocode(account.location)
                    account.latitude = lat
                    account.longitude = lng
                    account.put()
                except:
                    print "account_key:" + str(account.key()) + "\n"
                    print "account_name:" + account.displayName + "\n"
                    # print "account_location:" + account.location + "\n"
                    print "\n"
        return

class PrintOut (webapp.RequestHandler):
    def get(self):

        account = db.get("ahBzfmFwcGludmVudG9yb3Jncg8LEgdBY2NvdW50GOn7Aww")
        g = geocoders.GoogleV3()
        
           
        place, (lat, lng) = g.geocode(account.location)

        print lat
        print lng

        return
    
# convert profile user name
class ConvertProfileName1 (webapp.RequestHandler):
    def get(self):
        pquery = db.GqlQuery("SELECT * FROM Account")
        accounts = pquery.fetch(pquery.count())

        for account in accounts:
            
            try:
                firstName = account.firstName
                lastName = account.lastName
                if firstName == None or lastName == None:
                    account.displayName = str(account.user.nickname())
                    account.put()
                elif firstName.strip() == "" or lastName.strip() == "":
                    account.displayName = str(account.user.nickname())
                    account.put()
                elif firstName.strip() == "None" or lastName.strip() == "None":
                    account.displayName = str(account.user.nickname())
                    account.put()
                else:
                    account.displayName = firstName.strip() + " " + lastName.strip()
                    account.put()
                
            except:
                 print "1"
        return
class ConvertProfileName2 (webapp.RequestHandler):
    def get(self):
        pquery = db.GqlQuery("SELECT * FROM Account")
        accounts = pquery.fetch(pquery.count())

        for account in accounts:
            if account.displayName == None:
                    account.displayName = str(account.user.nickname())
                    account.put()
            
        return

class PrintUserName (webapp.RequestHandler):
    def get(self):
        key = self.request.get('key')
        account = db.get(key)

        self.response.headers['Content-Type'] = 'text/plain'

        if(account.firstName == None):
            self.response.write(" firstName: " + "\"" + "None" + "\"")
        else:
            self.response.write(" firstName: " + "\"" + account.firstName.strip() + "\"")

        if(account.lastName == None):
            self.response.write(" lastName: " + "\"" + "None" + "\"")
        else:
            self.response.write(" lastName: " + "\"" + account.firstName.strip() + "\"")

            
        if(account.displayName == None):
            self.response.write(" displayName: " + "\"" + "None" + "\"")
        else:
            self.response.write(" displayName: " + "\"" + account.displayName.strip() + "\"")


        
        return



    

class StepIframe(webapp.RequestHandler):
    def get(self):
        
        # login_url=users.create_login_url(self.request.uri)
        #       logout_url=users.create_logout_url(self.request.uri)

        # allAppsQuery = db.GqlQuery("SELECT * FROM App ORDER BY number ASC")

        # appCount = allAppsQuery.count()
        # allAppsList = allAppsQuery.fetch(appCount)
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/app_base_new_ai2_step_iframe.html')
        self.response.out.write(template.render(path, template_values))


# Web Tutorial
class WebTutorialHandler(webapp.RequestHandler):
    def get(self):
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        tutorialId = self.request.get("tutorialId")
        tutorial = db.GqlQuery("SELECT * FROM Tutorial WHERE tutorialId = :1", tutorialId).get()

        pquery = db.GqlQuery("SELECT * FROM TutorialStep WHERE tutorialId = :1", tutorialId)
        tuturialSteps = pquery.fetch(pquery.count())

        
        template_values = {
            'userStatus': userStatus,
            'tutorial': tutorial,
            'tuturialSteps': tuturialSteps
            }

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/web_tutorial.html')
        self.response.out.write(template.render(path, template_values))

class GetTutorialDataHandler(webapp.RequestHandler):
    def get(self):
        logging.info("I'm inside get_tutorial_data()")
        tutorial = self.request.get('tutorial')
        cacheHandler = CacheHandler()        
        tutorial_to_get = cacheHandler.GettingCache("Tutorial", True, "tutorialId", tutorial, False, None, None, False)

        tutorialId = tutorial

        number = tutorial_to_get.number;
        title = tutorial_to_get.title;
        heroHeader = tutorial_to_get.heroHeader;
        heroCopy = tutorial_to_get.heroCopy;
        

        my_response = {'number': number, 'title': title, 'heroHeader': heroHeader, 'heroCopy': heroCopy, 'tutorialId': tutorialId}
#       json = JSON.dumps(my_response)

        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
        self.response.out.write(json.dumps(my_response))
        
class GetTutorialStepDataHandler(webapp.RequestHandler):
    def get(self):
        logging.info("I'm inside get_tutorial_step_data()")
        step_header = self.request.get('step_header')
        cacheHandler = CacheHandler()
        step = cacheHandler.GettingCache("TutorialStep", True, "header", step_header, False, None, None, False)

        tutorialId = step.tutorialId;
        number = step.number;
        header = step.header;
        copy = step.copy;
        tutorialLink = step.tutorialLink;

        my_response = {'tutorialId': tutorialId, 'number': number, 'header': header, 'copy': copy, 'tutorialLink': tutorialLink}
#       json = JSON.dumps(my_response)

        

        self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
        self.response.out.write(json.dumps(my_response))

class PostTutorialStep(webapp.RequestHandler):
    def post(self):
        tutorialStepId = self.request.get('modify_tutorial_step_name')  # the ID is a header


        if (tutorialStepId):
            cacheHandler = CacheHandler()
            tutorialStep = cacheHandler.GettingCache("TutorialStep", True, "header", tutorialStepId, False, None, None, False)

        else:
            tutorialStep = TutorialStep()

        if self.request.get('tutorialId'):
            tutorialStep.tutorialId = self.request.get('tutorialId')

        if self.request.get('number'):
            tutorialStep.number = int(self.request.get('number'))

        if self.request.get('header'):
            tutorialStep.header = self.request.get('header')

        if self.request.get('copy'):
            tutorialStep.copy = self.request.get('copy')

        if self.request.get('tutorialLink'):
            tutorialStep.tutorialLink = self.request.get('tutorialLink')


        tutorialStep.put()

        # flush all the memcache
        memcache.flush_all()

        self.redirect('/AddTutorialStepPage?add_step_tutorial_name=' + tutorialStep.tutorialId)  # TODO: change to admin or app area

class PostTutorial(webapp.RequestHandler):
    def post(self):

        tutorialId = self.request.get('modify_tutorial_name')

        if (tutorialId):
            cacheHandler = CacheHandler()
            tutorial = cacheHandler.GettingCache("Tutorial", True, "tutorialId", tutorialId, False, None, None, False)
        else:
            tutorial = Tutorial()

        if self.request.get('tutorialNumber'):
            tutorial.number = int(self.request.get('tutorialNumber'))

        if self.request.get('tutorialId'):
            tutorial.tutorialId = self.request.get('tutorialId')

        if self.request.get('tutorialTitle'):
            tutorial.title = self.request.get('tutorialTitle')

        if self.request.get('tutorialHeroCopy'):
            tutorial.heroCopy = self.request.get('tutorialHeroCopy')

        if self.request.get('tutorialHeroHeader'):
            tutorial.heroHeader = self.request.get('tutorialHeroHeader')
            
        
            

        tutorial.put()  # now the app has a key() --> id()

        # flush all the memcache
        memcache.flush_all()
        
        self.redirect('/Admin')  # TODO: change to /admin (area)
        # wherever we put() to datastore, we'll need to also save the appId

class AddTutorialStepRenderer(webapp.RequestHandler):
    def get(self):
        step_listing = ""

        tutorialId = self.request.get('add_step_tutorial_name')
        cacheHandler = CacheHandler()
        tutorial = cacheHandler.GettingCache("Tutorial", True, "tutorialId", tutorialId, False, None, None, False)
        tutorialTitle = tutorial.title


        cacheHandler = CacheHandler()
        steps = cacheHandler.GettingCache("TutorialStep", True, "tutorialId", tutorialId, True, "number", "ASC", True)
        
        for step in steps:
            step_listing += str(step.number) + '. ' + step.header + '|'

        template_values = {
            'tutorialId': tutorialId,
            'tutorialTitle': tutorialTitle,
            'step_listing': step_listing
        }

        path = os.path.join(os.path.dirname(__file__), 'static_pages/admin/admin_tutorial_step.html')
        self.response.out.write(template.render(path, template_values))


class EmailHandler(webapp.RequestHandler):
    def get(self):


        mail.send_mail(sender=" App Inventor <lubin2012tj@gmail.com>",
              to="<blu2@dons.usfca.edu>",
              subject="Gmail ApI Test",
              body="""
                    Test Here

                    """)

    def sendToAdmin(self, link, comment):
        mail.send_mail(sender=" AppInventor Comment <appinventorcomment@gmail.com>",
              to="David W Wolber <wolberd@gmail.com>",
              subject="[Comment Notification]",
              body='',
              html='<p><b>' + comment.submitter.displayName + '</b> says "' + comment.content + '"</p></p> <a href="http://www.appinventor.org/' + link + '">See this comment</a></p>'

              )


class QuizzesHandler(webapp.RequestHandler):
    def get(self):
        template_values = {
            'url_linktext': 'Go to Quiz 1'
        }
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/Quizzes.html')
        self.response.out.write(template.render(path, template_values))


class ScreenHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}  

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/screens.html')
        self.response.out.write(template.render(path, template_values))

class ScreenSwapHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}  

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/screens-swap.html')
        self.response.out.write(template.render(path, template_values))    
class ScreenShareHandler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}  

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/screens-share.html')
        self.response.out.write(template.render(path, template_values))

class HelloPurrMiniHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/HelloPurrMini.html')
        self.response.out.write(template.render(path, template_values))

class Chapter1Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch01.html')
        self.response.out.write(template.render(path, template_values))

class Chapter2Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch02.html')
        self.response.out.write(template.render(path, template_values))

class Chapter3Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch03.html')
        self.response.out.write(template.render(path, template_values))


class Chapter4Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch04.html')
        self.response.out.write(template.render(path, template_values))

class Chapter5Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch05.html')
        self.response.out.write(template.render(path, template_values))

class Chapter6Handler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch06.html')
        self.response.out.write(template.render(path, template_values))

class Chapter7Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch07.html')
        self.response.out.write(template.render(path, template_values))

class Chapter8Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch08.html')
        self.response.out.write(template.render(path, template_values))

class Chapter9Handler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch09.html')
        self.response.out.write(template.render(path, template_values))

class Chapter10Handler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch10.html')
        self.response.out.write(template.render(path, template_values))

class Chapter11Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch11.html')
        self.response.out.write(template.render(path, template_values))

class Chapter12Handler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch12.html')
        self.response.out.write(template.render(path, template_values))

class Chapter13Handler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch13.html')
        self.response.out.write(template.render(path, template_values))

class Chapter14Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch14.html')
        self.response.out.write(template.render(path, template_values))

class Chapter15Handler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch15.html')
        self.response.out.write(template.render(path, template_values))

class Chapter16Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch16.html')
        self.response.out.write(template.render(path, template_values))

class Chapter17Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch17.html')
        self.response.out.write(template.render(path, template_values))

class Chapter18Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch18.html')
        self.response.out.write(template.render(path, template_values))

class Chapter19Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch19.html')
        self.response.out.write(template.render(path, template_values))

class Chapter20Handler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch20.html')
        self.response.out.write(template.render(path, template_values))

class Chapter21Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}
        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch21.html')
        self.response.out.write(template.render(path, template_values))

class Chapter22Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch22.html')
        self.response.out.write(template.render(path, template_values))

class Chapter23Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch23.html')
        self.response.out.write(template.render(path, template_values))

class Chapter24Handler(webapp.RequestHandler):
    def get(self):
        if redirector(self) == True:
            return None
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'bookChapters/ch24.html')
        self.response.out.write(template.render(path, template_values))


class ConceptualizeIHaveADreamHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/conceptualizeIHaveADream.html')
        self.response.out.write(template.render(path, template_values))      

class AppInventorSetUpHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/aiSetUp.html')
        self.response.out.write(template.render(path, template_values))  

class NewIHaveADreamHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/NewIHaveADream.html')
        self.response.out.write(template.render(path, template_values))

class PrefaceHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/preface.html')
        self.response.out.write(template.render(path, template_values))

class ConceptualizePaintPotHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/conceptualizePaintPot.html')
        self.response.out.write(template.render(path, template_values))

class ConceptualizeMoleMashHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/conceptualizeMoleMash.html')
        self.response.out.write(template.render(path, template_values))

class AnimationChallengeHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/UIScroll.html')
        self.response.out.write(template.render(path, template_values))

class WhatTheHeckIsCheckpointHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/WhatTheHeckIsCheckpoint.html')
        self.response.out.write(template.render(path, template_values))

class FirebaseDBHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/FirebaseDB.html')
        self.response.out.write(template.render(path, template_values))

class HueNewHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/HueNew.html')
        self.response.out.write(template.render(path, template_values))

class UIMoreAboutButtonsHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/UIMoreAboutButtons.html')
        self.response.out.write(template.render(path, template_values))

class UILLTCHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/UILLTC.html')
        self.response.out.write(template.render(path, template_values))

class UIMultipleScreensHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/UIMultipleScreens.html')
        self.response.out.write(template.render(path, template_values))

class UIArrangementsHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/UIArrangements.html')
        self.response.out.write(template.render(path, template_values))

class UIScrollHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/UIScroll.html')
        self.response.out.write(template.render(path, template_values))

class javaBridgeHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/javaBridge.html')
        self.response.out.write(template.render(path, template_values))

class LLTCHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'pages/IntroHTMLPages/UILLTC.html')
        self.response.out.write(template.render(path, template_values))

class CreativeProject2GameHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/creativeProject2Game.html')
        self.response.out.write(template.render(path, template_values))

class GoogleVoiceHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/googleVoice.html')
        self.response.out.write(template.render(path, template_values))

class ConceptualizeNoTextingHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/conceptualizeNoTexting.html')
        self.response.out.write(template.render(path, template_values))

class ConceptualizeLocationHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/conceptualizeLocation.html')
        self.response.out.write(template.render(path, template_values))


class PretestHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/pretest.html')
        self.response.out.write(template.render(path, template_values))

class ListIterationHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/listiteration.html')
        self.response.out.write(template.render(path, template_values))

class ConceptualizeSlideshowHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/conceptualizeSlideshow.html')
        self.response.out.write(template.render(path, template_values))

class ConceptualizeProceduresHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/conceptualizeProcedures.html')
        self.response.out.write(template.render(path, template_values))

class ConceptualizeIterationHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/conceptualizeIteration.html')
        self.response.out.write(template.render(path, template_values))

class ConceptualizeNoteTakerHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/conceptualizeNoteTaker.html')
        self.response.out.write(template.render(path, template_values))

class ConceptualizeCommunicationHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/conceptualizeCommunication.html')
        self.response.out.write(template.render(path, template_values))

class ConceptualizeStockMarketHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/conceptualizeStockMarket.html')
        self.response.out.write(template.render(path, template_values))

class PizzaPartyHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/pizzaParty.html')
        self.response.out.write(template.render(path, template_values))

        
        
        
        
        
####################################
#         Jordan's classes         #
#                                  #
#                                  # 
####################################

class Homehandler(webapp.RequestHandler):
    def get(self):
        # look up all the courses for the global navbar
        userStatus = UserStatus().getStatus(self.request.uri)

        template_values = {'userStatus': userStatus,
                           'title' : 'Learn to build Android apps | Appinventor',
                           'stylesheets' : ['/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js',  '/assets/js/ytexpo.js'],
                           'courseToModules' : getCoursesAndModules(),
                           }
        
        
        path = os.path.join(os.path.dirname(__file__), 'pages/home.html')
        self.response.out.write(template.render(path, template_values))  

class TutorialsHandler(webapp.RequestHandler):
    def get(self):
        # retreive all of the courses
        courses = getCourses()
        

        userStatus = UserStatus().getStatus(self.request.uri)
                       
        
        template_values = {'courses' : courses,
                           'stylesheets' : ['/assets/css/coursesystem.css'],
                           'scripts' : ['/assets/js/coursesystem.js'],
                           'userStatus': userStatus,
                           'title' : 'Courses'
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'pages/tutorials.html')
        self.response.out.write(template.render(path, template_values))

class CourseOverviewHandler(webapp.RequestHandler):
    """
    TODO: This page will display the course overview page associated with
    a module.

    We need to add a new entry in the course datastore entity called overview url.

    And it will be rendered here!
    """
    def get(self, course_ID=''):    
        # retrieve the course entity with the course_ID
        x = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).filter(Course.c_identifier == course_ID).fetch()
        
        if len(x) == 0:
            template_values = {}
            path = os.path.join(os.path.dirname(__file__), 'pages/pagenotfound.html')
            self.response.out.write(template.render(path, template_values))  
        else:
            # course exists, find the first module            
            # and redirect to that
            
            courseId = x[0].key.id()
            modules = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, courseId)).order(Module.m_index).fetch()
            
            course = x[0]
            first_module = modules[0]
             
            self.redirect(course.c_identifier + "/" + first_module.m_identifier)     

class ContentsHandler(webapp.RequestHandler):
    """
    TODO: Phase out unused template variables with courseToModules!
    I think there are some redudant ones in here.
    """
    def get(self, module_ID="", course_ID=""):
        # retrieve corresponding contents entities
        
        # retrieve the key of the course entity with the course_title
        x = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).filter(Course.c_identifier == course_ID).fetch()
        
        if len(x) == 0:
            template_values = {}
            path = os.path.join(os.path.dirname(__file__), 'pages/pagenotfound.html')
            self.response.out.write(template.render(path, template_values))     
        else:
            course_entity = x[0]
            # course exists, attempt to look up module title entity
            x = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()))).filter(Module.m_identifier == module_ID).fetch()
            if len(x) == 0:
                template_values = {}
                path = os.path.join(os.path.dirname(__file__), 'pages/pagenotfound.html')
                self.response.out.write(template.render(path, template_values))  
            else:
                # module and course exist, display the page!
                module_entity = x[0]
                contents = Content.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()), Module, long(module_entity.key.id()))).order(Content.c_index).fetch()
                
                # retrieve all of the courses for the navbar
                courses = getCourses()
                
                # construct dictionary of courses to modules mapping

                modules = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()))).order(Module.m_index).fetch()    
                
             
                userStatus = UserStatus().getStatus(self.request.uri)
                       
                template_values = {"title" : course_entity.c_title ,
                                   "description" : course_entity.c_description ,
                                   "module" : module_entity,    
                                   "modules" : modules,
                                   "stylesheets" : ["/assets/css/coursesystem.css"],
                                   "scripts" : ["/assets/js/coursesystem.js"],
                                   "userStatus": userStatus,
                                   "contents" : contents,
                                   "courses" : courses,
                                   'courseToModules' : getCoursesAndModules(),
                                }
                
                path = os.path.join(os.path.dirname(__file__), 'pages/modules.html')
                self.response.out.write(template.render(path, template_values))
                
                
               
class ContentHandler(webapp.RequestHandler):
    """
    TODO: Phase out unused template variables with courseToModules!
    I think there are some redudant ones in here.
    """
    def get(self, course_ID="", module_ID="", content_ID=""):
        # retrieve corresponding content entity
        
        # retrieve the key of the course entity with the course_title
        x = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).filter(Course.c_identifier == course_ID).fetch()
        
        if len(x) == 0:
            template_values = {}
            path = os.path.join(os.path.dirname(__file__), 'pages/pagenotfound.html')
            self.response.out.write(template.render(path, template_values))     
        else:
            course_entity = x[0]
            # course exists, attempt to look up module title entity
            x = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()))).filter(Module.m_identifier == module_ID).fetch()
            if len(x) == 0:
                template_values = {}
                path = os.path.join(os.path.dirname(__file__), 'pages/pagenotfound.html')
                self.response.out.write(template.render(path, template_values))  
            else:
                # module and course exist, attempt to look up content
                module_entity = x[0]
                
                content = Content.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()), Module, long(module_entity.key.id()))).filter(Content.c_identifier == content_ID).fetch()
                
                if len(content) == 0:
                    template_values = {}
                    path = os.path.join(os.path.dirname(__file__), 'pages/pagenotfound.html')
                    self.response.out.write(template.render(path, template_values))  
                else:
                    # everything was found! display the page
                    content = content[0]
                    
                    # must look up all content in current module
                    module_contents = Content.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()), Module, long(module_entity.key.id()))).order(Content.c_index).fetch()
                    
                    
                    
                    # look up all the courses for the global navbar
                    courses = getCourses()
                    
                    # look up all the modules in the current course for display in the left nav bar
                    modules = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()))).order(Module.m_index).fetch()
                    
                    # look up the next_module_entity
                    next_module_entity = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()))).filter(Module.m_index > module_entity.m_index).order(Module.m_index).fetch()
                    
                    if len(next_module_entity) == 0:
                        next_module_entity = "null"
                    else:
                        next_module_entity = next_module_entity[0]
                    
                    # construct dictionary of courses to modules
                    
                    moduleContentMapping = collections.OrderedDict()
                    # iterate over all the modules in the current course
                    
                    for module in modules:
                        # initialize key in mapping
                        moduleContentMapping[str(module.m_title)] = ['null']
                        # now look up the content associated with this module
                        contents = Content.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()), Module, long(module.key.id()))).order(Content.c_index).fetch()
                        for mod_content in contents:                     
                            moduleContentMapping[str(module.m_title)].append(mod_content)

                    userStatus = UserStatus().getStatus(self.request.uri)
                                     
                    template_values = {"current_content" : content,
                           "next_module" : next_module_entity,
                           "module" : module_entity,
                           "course" : course_entity,
                           "contents" : module_contents,
                           "title" : content.c_title,
                           "courses" : courses,
                           "content" : content,
                           "moduleContentMapping" : moduleContentMapping,
                           'stylesheets' : [],
                           'scripts' : ['/assets/js/coursesystem.js'],
                           'userStatus': userStatus,
                           'courseToModules' : getCoursesAndModules(),
                           }
                    
                    path = os.path.join(os.path.dirname(__file__), 'pages/content.html')
                    self.response.out.write(template.render(path, template_values))  
        



class AdminCourseDisplayHandler(webapp.RequestHandler):
    """Generates and renders the admin courses page"""
    def get(self):
        # ancestor query all of the courses that belong to the ADMINSET
        # For now, all courses created belong to the adminset, we could change this in the future
        # and have multiple sets of courses, adding on another layer of abstraction in the menu system
        # the only reason I could see doing this is too allow users to create their own courses
        userStatus = UserStatus().getStatus(self.request.uri)
        
        # look up all the courses for the global navbar and the display
        courses = getCourses()
        
        template_values = {"courses" : courses,
                           'stylesheets' : ['/assets/admin/css/editor.css', '/assets/admin/css/admin.css', '/assets/css/coursesystem.css'],
                           'scripts' : ['/assets/admin/js/courses_editor.js'],
                           'title' : 'Courses Admin',
                           'userStatus' : userStatus,
                           'courseToModules' : getCoursesAndModules(),
                           }
        
        
        path = os.path.join(os.path.dirname(__file__), 'pages/admin/courses_editor.html')
        self.response.out.write(template.render(path, template_values))  

class AdminModuleDisplayHandler(webapp.RequestHandler):
    def get(self, course_ID=''):
        # retrieve corresponding module entities
        
        # retrieve the key of the course entity with the course_title
        x = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).filter(Course.c_identifier == course_ID).fetch()
        
        if len(x) == 0:
            template_values = {}
            path = os.path.join(os.path.dirname(__file__), 'pages/pagenotfound.html')
            self.response.out.write(template.render(path, template_values))  
        else:
            # course exists display the page!
            courseId = x[0].key.id()
            modules = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, courseId)).order(Module.m_index).fetch()
        
        
            userStatus = UserStatus().getStatus(self.request.uri)
        
            # look up all the courses for the global navbar and the display
            courses = getCourses()
        
            
            # construct dictionary of courses to modules mapping
            moduleContentMapping = collections.OrderedDict()
            # iterate over all the modules in the current course
             
            
                    
            for module in modules:
                # initialize key in mapping
                moduleContentMapping[str(module.m_title)] = [module.m_icon]
                moduleContentMapping[str(module.m_title)].append(module.m_description)
                # now look up the content associated with this module
                contents = Content.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(courseId), Module, long(module.key.id()))).order(Content.c_index).fetch()
                for mod_content in contents:                     
                    moduleContentMapping[str(module.m_title)].append(mod_content)
             
            template_values = {"modules" : modules,
                               "course" : x[0],
                               'title' : 'Module Administration',
                               'userStatus' : userStatus,
                               "courses" : courses,
                               'moduleContentMapping' : moduleContentMapping,
                               'stylesheets' : ['/assets/admin/css/editor.css', '/assets/css/coursesystem.css'],
                               'scripts' : ['/assets/admin/js/modules_editor.js'],
                              }
            
            path = os.path.join(os.path.dirname(__file__), 'pages/admin/modules_editor.html')
            self.response.out.write(template.render(path, template_values))
        
class AdminContentsDisplayHandler(webapp.RequestHandler):
    def get(self, course_ID="", module_ID=""):
        # retrieve corresponding contents entities
        
        # retrieve the key of the course entity with the course_ID
        x = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).filter(Course.c_identifier == course_ID).fetch()
        
        if len(x) == 0:
            template_values = {}
            path = os.path.join(os.path.dirname(__file__), 'pages/pagenotfound.html')
            self.response.out.write(template.render(path, template_values))     
        else:
            course_entity = x[0]
            # course exists, attempt to look up module title entity
            x = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()))).filter(Module.m_identifier == module_ID).fetch()
            if len(x) == 0:
                template_values = {}
                path = os.path.join(os.path.dirname(__file__), 'pages/pagenotfound.html')
                self.response.out.write(template.render(path, template_values))  
            else:
                # module and course exist, display the page!
                module_entity = x[0]
                contents = Content.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()), Module, long(module_entity.key.id()))).order(Content.c_index).fetch()
        
                userStatus = UserStatus().getStatus(self.request.uri)
        
                # look up all the courses for the global navbar and the display
                courses = getCourses()            

          
                template_values = {"contents" : contents,
                                   "course" : course_entity,
                                   "module" : module_entity,
                                   'title' : 'Content Administration',
                                   'userStatus' : userStatus,
                                   "courses" : courses,
                                   'stylesheets' : ['/assets/admin/css/editor.css', '/assets/css/coursesystem.css'],
                                   'scripts' : ['/assets/admin/js/contents_editor.js'],
                                    }
                
                path = os.path.join(os.path.dirname(__file__), 'pages/admin/contents_editor.html')
                self.response.out.write(template.render(path, template_values))
                
 
 

class AdminContentDisplayHandler(webapp.RequestHandler):
    def get(self, course_ID="", module_ID="", content_ID=""):
        # retrieve corresponding content entity
        
        
        # retrieve the key of the course entity with the course_title
        x = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).filter(Course.c_identifier == course_ID).fetch()
        
        if len(x) == 0:
            template_values = {}
            path = os.path.join(os.path.dirname(__file__), 'pages/pagenotfound.html')
            self.response.out.write(template.render(path, template_values))     
        else:
            course_entity = x[0]
            # course exists, attempt to look up module title entity
            x = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()))).filter(Module.m_identifier == module_ID).fetch()
            if len(x) == 0:
                template_values = {}
                path = os.path.join(os.path.dirname(__file__), 'pages/pagenotfound.html')
                self.response.out.write(template.render(path, template_values))  
            else:
                # module and course exist, attempt to look up content
                module_entity = x[0]
                
                content = Content.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()), Module, long(module_entity.key.id()))).filter(Content.c_identifier == content_ID).fetch()
                
                if len(content) == 0:
                    template_values = {}
                    path = os.path.join(os.path.dirname(__file__), 'pages/pagenotfound.html')
                    self.response.out.write(template.render(path, template_values))  
                else:
                    # everything was found! display the page
                    content = content[0]
                    
                    # self.response.out.write("<h4>Okay we need to look up a content item called: " + content_Title + " inside of  module called: " + module_Title + " inside of course called: " + course_Title + "</h4>")
        
                    # must look up all content in current module
                    module_contents = Content.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()), Module, long(module_entity.key.id()))).order(Content.c_index).fetch()
                    
                    
                    # look up userstatus for globalnavbar
                    userStatus = UserStatus().getStatus(self.request.uri)
        
                    # look up all the courses for the global navbar and the display
                    courses = getCourses()            


                    # look up the next_module_entity
                    next_module_entity = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()))).filter(Module.m_index > module_entity.m_index).order(Module.m_index).fetch()
                    
                    if len(next_module_entity) == 0:
                        next_module_entity = "null"
                    else:
                        next_module_entity = next_module_entity[0]
                    
                    # render the template
                    template_values = {"current_content" : content,
                           "module" : module_entity,
                           "course" : course_entity,
                           "contents" : module_contents,
                           "title" : "Content Display Preview",
                           "content" : content,
                           'userStatus' : userStatus,
                           'courses' : courses,
                           'next_module' : next_module_entity,
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/coursesystem.css'],
                           'scripts' : ['/assets/js/coursesystem.js']
                           }
                            
                    path = os.path.join(os.path.dirname(__file__), 'pages/content.html')
                    self.response.out.write(template.render(path, template_values))  
                    

class AdminCourseSystemCreateHandler(webapp.RequestHandler):
    def post(self, kind=""):
        if kind == "Course":
            logging.info("creating course")
            # retrieve data from the request
            title = self.request.get("title")
            description = self.request.get("description")
            icon = str(self.request.get("icon"))
            last_index = int(self.request.get("last_index"))
            new_index = last_index + 1
            identifier = self.request.get("s_identifier")            
            # root ancestor of all courses, for now the ADMINSET are the courses created by the admins
            course_ancestor_key = ndb.Key('Courses', 'ADMINSET')
            # create the new Course entity and store it in the datastore
            new_course = Course(parent=course_ancestor_key, c_title=title, c_description=description, c_icon=icon, c_index=new_index, c_identifier=identifier)
            new_course.put()
        elif kind == "Module":
            title = self.request.get("title")
            description = self.request.get("description")
            icon = str(self.request.get("icon"))
            course_id = self.request.get("course_id")
            identifier = self.request.get("s_identifier")
            new_module = Module(parent=ndb.Key('Courses', 'ADMINSET', Course, long(course_id)), m_title=title, m_description=description, m_icon=icon, m_identifier=identifier)        
            new_module.put()   
        elif kind == "Content":
            title = self.request.get("s_title")
            description = self.request.get("s_description")
            content_type = str(self.request.get("s_content_type"))
            course_id = self.request.get("s_course_id")
            module_id = self.request.get("s_module_id")
            file_path = self.request.get("s_file_path")
            identifier = self.request.get("s_identifier")
            old_urls = self.request.get("s_oldurls")
            #split old_urls into list
            old_urls = str(old_urls).split()
            logging.info(str(old_urls) + " " + str(type(old_urls)))
            
            new_content = Content(parent=ndb.Key('Courses', 'ADMINSET', Course, long(course_id), Module, long(module_id)), c_title=title, c_description=description, c_type=content_type, c_url=file_path)
            new_content.c_identifier = identifier
            new_content.c_url = file_path
            new_content.c_oldurls = old_urls
            new_content.put()
        else:
            logging.error("An invalid kind was attempted to be created: " + kind)
            
class AdminCourseSystemDeleteHandler(webapp.RequestHandler):
    def post(self, kind=""):
        if kind == "Course":            
            ndb.delete_multi(ndb.Query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(self.request.get("course_id")))).iter(keys_only=True))
        elif kind == "Module":
            ndb.delete_multi(ndb.Query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(self.request.get("course_id")), Module, long(self.request.get("module_id")))).iter(keys_only=True))    
        elif kind == "Content":
            ndb.Key('Courses', 'ADMINSET', Course, long(self.request.get("course_id")), Module, long(self.request.get("module_id")), Content, long(self.request.get("content_id"))).delete()
        else:
            logging.error("An invalid kind was attempted to be deleted: " + kind)

class AdminCourseSystemReorderHandler(webapp.RequestHandler):
    def post(self, kind=""):
        if kind == "Course":
            orderArray = self.request.get("s_resultArray").split(",")
            x = 0;
            while(x < len(orderArray) - 1):
                # retrieve corresponding course entity and update index
                course = ndb.Key('Courses', 'ADMINSET', Course, long(orderArray[x + 1])).get()
                course.c_index = int(orderArray[x])
                course.put()
                x += 2
        elif kind == "Module":
            logging.info("LETS DO THIS")
            orderArray = self.request.get('s_array').split(",")
            x = 0;
            while(x < len(orderArray) - 1):
                # retrieve corresponding module and update index
                module = ndb.Key('Courses', 'ADMINSET', Course, long(self.request.get("course_id")), Module, long(orderArray[x + 1])).get()
                module.m_index = int(orderArray[x])
                module.put()
                x += 2
        elif kind == "Content":
            orderArray = self.request.get('s_resultArray').split(",")   
            x = 0;
            while(x < len(orderArray) - 1):
                # retrieve corresponding content and update index
                content = ndb.Key('Courses', 'ADMINSET', Course, long(self.request.get("s_course_id")), Module, long(self.request.get("s_module_id")), Content, long(orderArray[x + 1])).get()
                content.c_index = int(orderArray[x])
                content.put()
                x += 2
        else:
            logging.error("An invalid kind was attempted to be reordered: " + kind)
    
    
class AdminCourseSystemUpdateHandler(webapp.RequestHandler):
    def post(self, kind=""):
        if kind == "Course":
            title = self.request.get("s_title")
            description = self.request.get("s_description")
            course_id = self.request.get("s_course_id")
            icon = str(self.request.get('s_icon'))
            identifier = self.request.get('s_identifier')
            # retrieve course entity and update it
            course = ndb.Key('Courses', 'ADMINSET', Course, long(course_id)).get()
            course.c_title = title
            course.c_description = description
            course.c_icon = icon
            course.c_identifier = identifier
            course.put()
        elif kind == "Module":
            title = self.request.get("s_title")
            description = self.request.get("s_description")
            course_id = self.request.get("s_course_id")
            module_id = self.request.get("s_module_id")
            icon = str(self.request.get('s_icon'))
            identifier = self.request.get('s_identifier')
            # retrieve module entity and update it
            module = ndb.Key('Courses', 'ADMINSET', Course, long(course_id), Module, long(module_id)).get()
            module.m_title = title
            module.m_description = description
            module.m_icon = icon
            module.m_identifier = identifier
            module.put()
        elif kind == "Content":
            title = self.request.get("s_title")
            description = self.request.get("s_description")
            course_id = self.request.get("s_course_id")
            module_id = self.request.get("s_module_id")
            content_id = self.request.get("s_content_id")
            content_type = self.request.get("s_content_type")
            url = self.request.get("s_url")
            identifier = self.request.get("s_identifier")
            oldurls = self.request.get("s_oldurls")
            # split oldurls into list
            oldUrlList = oldurls.split()    
            # retrieve content entity and update it
            content = ndb.Key('Courses', 'ADMINSET', Course, long(course_id), Module, long(module_id), Content, long(content_id)).get()
            content.c_title = title
            content.c_description = description
            content.c_url = url
            content.c_type = content_type
            content.c_identifier = identifier
            content.c_oldurls = oldUrlList
            content.put()
        else:
            logging.error("An invalid kind was attempted to be updated: " + kind)


class AdminDashboardHandler(webapp.RequestHandler):    
    def get(self):                      
        userStatus = UserStatus().getStatus(self.request.uri)
        
        # look up all the courses for the global navbar
        courses = getCourses()
                    
        template_values = {
                           'stylesheets' : ['/assets/admin/css/admin.css', '/assets/css/coursesystem.css'],
                           'userStatus' : userStatus,
                           'courses' : courses,
                           'title' : 'Admin Dashboard',
                           'courseToModules' : getCoursesAndModules(),
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'pages/admin/admin_dashboard.html')
        self.response.out.write(template.render(path, template_values))        

class AdminExportCoursesHandler(webapp.RequestHandler):
    def get(self):

        userStatus = UserStatus().getStatus(self.request.uri)
        
        # look up all the courses for the global navbar
        courses = getCourses()
                
        
        template_values = {
                           'stylesheets' : ['/assets/admin/css/admin.css'],
                           'userStatus' : userStatus,
                           'courses' : courses,
                           'title' : 'Admin Dashboard'
                           }       
        
        path = os.path.join(os.path.dirname(__file__), 'pages/admin/export_courses.html')
        self.response.out.write(template.render(path, template_values))        

class AdminImportCoursesHandler(webapp.RequestHandler):
    def get(self):
        userStatus = UserStatus().getStatus(self.request.uri)
        
        # look up all the courses for the global navbar
        courses = getCourses()
            
        

        template_values = {
                           'stylesheets' : ['/assets/admin/css/admin.css'],
                           'userStatus' : userStatus,
                           'courses' : courses,
                           'title' : 'Admin Dashboard',
                           'scripts' : ['/assets/admin/js/import.js'],
                           }       
        
        path = os.path.join(os.path.dirname(__file__), 'pages/admin/import_courses.html')
        
        self.response.out.write(template.render(path, template_values))      
        
    def post(self):
        """ For now this completely replaces the current contents of the course system 
        with the imported file. """
        
        
        # delete everything in the current datastore
        
        keysToDelete = []
        
        courses = getCourses()
        # for every course
        for course in courses:
            # for every module
            modules = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course.key.id()))).order(Module.m_index).fetch()
            for module in modules:
                # for every content
                contents = Content.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course.key.id()), Module, long(module.key.id()))).order(Content.c_index).fetch()
                for content in contents:
                    keysToDelete += [content.key]
                keysToDelete += [module.key]
            keysToDelete += [course.key]
             
        ndb.delete_multi(keysToDelete)
        
        importFileContents = self.request.get("s_File_Contents")
        i = 0
        splitContent = importFileContents.split('\n')
        while i < len(splitContent) - 1:
            course_Title = splitContent[i]
            i += 1      
            course_Description = splitContent[i]
            i += 1                                                      
            course_Icon = splitContent[i]
            i += 1                                                      
            course_Index = splitContent[i]
            i += 1
            course_Identifier = splitContent[i]
            i += 1     
            
            if course_Index == 'None':
                courses_Index = 0
            
            course = Course(parent=ndb.Key('Courses', 'ADMINSET'), c_title=course_Title, c_description=course_Description, c_icon=str(course_Icon), c_index=int(course_Index), c_identifier=course_Identifier)
            course.put()
                
            while splitContent[i] != "**********":
                module_Title = splitContent[i]
                i += 1
                module_Description = splitContent[i]
                i += 1                
                module_Icon = splitContent[i]
                i += 1
                module_Index = splitContent[i]
                i += 1
                module_Identifier = splitContent[i]
                i += 1    
                
                if module_Index == 'None':
                        module_Index = 0
                
                module = Module(parent=ndb.Key('Courses', 'ADMINSET', Course, long(course.key.id())), m_title=module_Title, m_description=module_Description, m_icon=str(module_Icon), m_index=int(module_Index), m_identifier=module_Identifier)
                module.put()
                
                while splitContent[i] != "*****":
                    content_Title = splitContent[i]
                    i += 1
                    content_Description = splitContent[i]
                    i += 1              
                    content_Type = splitContent[i]
                    i += 1    
                    content_URL = splitContent[i]
                    i += 1
                    content_Index = splitContent[i]
                    i += 1
                    content_Identifier = splitContent[i]
                    i += 1    
                    content_oldurls = splitContent[i]
                    content_oldurlsList = ast.literal_eval(content_oldurls)                    
                    i += 1                   
                    if content_Index == 'None':
                        content_Index = 0
                   
                    content = Content(parent=ndb.Key('Courses', 'ADMINSET', Course, long(course.key.id()), Module, long(module.key.id())), c_title=content_Title, c_description=content_Description, c_type=content_Type, c_url=content_URL , c_index=int(content_Index), c_identifier=content_Identifier)
                    content.c_oldurls = content_oldurlsList
                    content.put() 
                i += 1
            i += 1
          


class AdminSerialViewHandler(webapp.RequestHandler):
    """ Creates a serialized output of the courses and content on the site, this page is intended to be 
        downloaded by the user via the course export page. """
    def get(self):
        output = ""
        courses = getCourses()
        # for every course
        for course in courses:
            output += course.c_title + "\n" + course.c_description + "\n" + course.c_icon + "\n" + str(course.c_index) + "\n" + course.c_identifier + "\n"
            # for every module
            modules = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course.key.id()))).order(Module.m_index).fetch()
            for module in modules:
                output += module.m_title + "\n" + module.m_description + "\n" + module.m_icon + "\n" + str(module.m_index) + "\n" + module.m_identifier + "\n"
                # for every content
                contents = Content.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course.key.id()), Module, long(module.key.id()))).order(Content.c_index).fetch()
                for content in contents:
                    logging.info(str(content.c_oldurls))
                    
                    # format old url list to whitespace seperated string
                    oldurlstring = ""
                    for url in content.c_oldurls:
                        oldurlstring += url + " "
                    oldurlstring = oldurlstring.strip()
                    
                    output += content.c_title + "\n" + content.c_description + "\n" + content.c_type + "\n" + content.c_url + "\n" + str(content.c_index) + "\n" + content.c_identifier + "\n" + str(content.c_oldurls) + "\n"
                output += "*****\n"
            output += "**********\n"        
        
        self.response.out.write(output)


        
class gDocHandler(webapp.RequestHandler):
    def get(self):
        
        userStatus = UserStatus().getStatus(self.request.uri)
        #docId="1f4lPDnfaxxKhzkWvoEuCrHNHpJBRWixIsxr8u0zJR9U"
        docId = self.request.get("docId")
        # look up all the courses for the global navbar
        courses = getCourses()
            
        
        template_values = {
                           'stylesheets' : ['/assets/admin/css/admin.css'],
                           'userStatus' : userStatus,
                           'courses' : courses,
                           'title' : 'Admin Dashboard',
                           'scripts' : ['/assets/admin/js/import.js'],
                           'docId' : docId                           }       
        
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/gdoc.html')
        self.response.out.write(template.render(path, template_values))      

class updateRSSHandler(webapp.RequestHandler):
    """
    Updates the datastore's copy of the app inventor blog rss feed.
    This is called via a cron job.
    """
    
    def clean_content(self, content):
        """ 
        Gets rid of the add a comment link at the bottom of an item.
        Hacky solution, just drops everything after the last a tag.
        """
        endIndex = content.rfind("<a")
        logging.info(endIndex)
        return content[:endIndex]
        
    
    def read_feed(self):
        feed = feedparser.parse( "http://appinventorblog.com/feed/" )
       
        results = RSSItem.query(ancestor=ndb.Key('RSSFeeds', 'AppInventorBlog')).fetch()
        
        savedLinks = []
        for item in results:
            savedLinks += [item.link]
        logging.info(savedLinks)

        for item in feed.entries:
            # if the item is not in the datastore add it
            if(item["link"] not in savedLinks):
                new_item = RSSItem(parent=ndb.Key('RSSFeeds', 'AppInventorBlog'))
                new_item.title = item["title"]
                new_item.content = self.clean_content(item["content"][0]["value"])
                new_item.link = item["link"]
                new_item.dateUnFormatted = datetime.datetime(*(item['updated_parsed'][0:6]))
                new_item.date = time.strftime("%B %d, %Y", item.published_parsed)
                new_item.put()
            else:
                self.response.out.write("<h1>" + item["title"] + " " + time.strftime("%B %d, %Y", item.published_parsed) +"SAVED!!!</h1>")
    
    def get(self):
        self.read_feed()
        

            

####################################
#       End Jordan's Classes       #
#                                  #
#                                  # 
####################################





class ObjectivesModule1(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'pages/objectives/objective1.html')
        self.response.out.write(template.render(path, {}))


      
class AboutHandler(webapp.RequestHandler):
    def get(self):
        userStatus = UserStatus().getStatus(self.request.uri)
                
        template_values = {
                           'userStatus' : userStatus,
                           'courseToModules' : getCoursesAndModules(),
                           'title' : 'About'
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'pages/about.html')
        self.response.out.write(template.render(path, template_values)) 
     
class BlogHandler(webapp.RequestHandler):
    def get(self):
        userStatus = UserStatus().getStatus(self.request.uri)
        rssItems = RSSItem.query(ancestor=ndb.Key('RSSFeeds', 'AppInventorBlog')).order(-RSSItem.dateUnFormatted).fetch(4)        
        
        logging.info(rssItems)
        
        template_values = {
                           'userStatus' : userStatus,
                           'courseToModules' : getCoursesAndModules(),
                           'title' : 'About',
                           'rssItems' : rssItems
                           }
                
        path = os.path.join(os.path.dirname(__file__), 'pages/blog.html')
        self.response.out.write(template.render(path, template_values)) 
        
class TeamHandler(webapp.RequestHandler):
    def get(self):
        userStatus = UserStatus().getStatus(self.request.uri)
                
        template_values = {
                           'userStatus' : userStatus,
                           'courseToModules' : getCoursesAndModules(),
                           'title' : 'Team'
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'pages/team.html')
        self.response.out.write(template.render(path, template_values)) 

class ContactUsHandler(webapp.RequestHandler):
    def get(self):
        userStatus = UserStatus().getStatus(self.request.uri)
                
        template_values = {
                           'userStatus' : userStatus,
                           'courseToModules' : getCoursesAndModules(),
                           'title' : 'Team'
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'pages/contact_us.html')
        self.response.out.write(template.render(path, template_values)) 

<<<<<<< HEAD
=======
class JBridgeHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'pages/javaBridge.html')
        self.response.out.write(template.render(path, {}))



>>>>>>> a0a97ced319e885819e0235561f0d84241ed0a37
class CourseInABoxIntroHanlder(webapp.RequestHandler):
    def get(self):
        userStatus = UserStatus().getStatus(self.request.uri)

        template_values = {
                           'userStatus' : userStatus,
                           'courseToModules' : getCoursesAndModules(),
                           'title' : 'Course In A Box Intro',
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/course-in-a-box-intro.html')
        self.response.out.write(template.render(path, template_values))      


class AsteroidsPart1Handler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/asteroids_part1.html')
        self.response.out.write(template.render(path, {}))      


# create this global variable that represents the application and specifies which class
# should handle each page in the site
application = webapp.WSGIApplication(
    # MainPage handles the home page load
    [
        ('/hellopurr', AppRenderer), ('/paintpot', AppRenderer), ('/molemash', AppRenderer),
        ('/shootergame', AppRenderer), ('/no-text-while-driving', AppRenderer), ('/ladybug-chase', AppRenderer),
        ('/map-tour', AppRenderer), ('/android-where-s-my-car', AppRenderer), ('/quiz', AppRenderer),
        ('/notetaker', AppRenderer), ('/xylophone', AppRenderer), ('/makequiz-and-takequiz-1', AppRenderer),
        ('/broadcaster-hub-1', AppRenderer), ('/robot-remote', AppRenderer), ('/stockmarket', AppRenderer),
        ('/amazon', AppRenderer), ('/gettingstarted', GettingStartedHandler),
        ('/AddApp', AddAppHandler), ('/AddStep', AddStepHandler),
        ('/AddConcept', AddConceptHandler), ('/AddCustom', AddCustomHandler),
        ('/PostApp', PostApp), ('/PostStep', PostStep), ('/PostCustom', PostCustom),
        ('/outline', CourseOutlineHandler), ('/introduction', IntroductionHandler), ('/course-in-a-box', CourseInABoxHandler), ('/course-in-a-box2', CourseInABox2Handler), ('/portfolio', PortfolioHandler), ('/introTimer', IntroTimerHandler), ('/smoothAnimation', SmoothAnimationHandler), ('/soundboard', SoundBoardHandler),
        ('/media', MediaHandler), ('/mediaFiles', MediaFilesHandler), ('/teaching-android', TeachingHandler), ('/lesson-introduction-to-app-inventor', LPIntroHandler),
        ('/lesson-plan-creating', LPCreatingHandler), ('/lesson-plan-paintpot-and-initial-discussion-of-programming-con', LPConceptsHandler),
        ('/lesson-plan-mobile-apps-and-augmented-real', LPAugmentedHandler), ('/lesson-plan-games', LPGamesHandler),
        ('/iterate-through-a-list', LPIteratingHandler), ('/lesson-plan-user-g', LPUserGenHandler),
        ('/lesson-plan-foreach-iteration-and', LPForeachHandler), ('/persistence-worksheet', LPPersistenceWorksheetHandler),
        ('/persistence-r', LPPersistenceFollowupHandler), ('/functions', LPFunctionsHandler),
        ('/hellopurrLesson', HelloPurrHandler), ('/paintpotLesson', PaintPotHandler), ('/molemashLesson', MoleMashHandler), ('/no-text-while-drivingLesson', NoTextingHandler), ('/notetakerLesson', NoteTakerHandler), ('/broadcaster-hub-1Lesson', BroadcastHubHandler), ('/quizLesson', QuizHandler), ('/shootergameLesson', ShooterHandler), ('/paintPotIntro', PaintPotIntroHandler), ('/structure', StructureHandler), ('/appPage', AppPageHandler), ('/appInventorIntro', AppInventorIntroHandler), ('/loveYouLesson', LoveYouHandler), ('/loveYouWS', LoveYouWSHandler), ('/raffle', RaffleHandler), ('/gpsIntro', GPSHandler), ('/androidWhere', AndroidWhereHandler), ('/quizIntro', QuizIntroHandler), ('/userGenerated', UserGeneratedHandler), ('/tryit', TryItHandler),
        ('/procedures', LPCodeReuseHandler), ('/deploying-an-app-and-posting-qr-code-on-web', LPQRHandler),
        ('/module1', Module1Handler), ('/module2', Module2Handler), ('/module3', Module3Handler),
        ('/module4', Module4Handler), ('/module5', Module5Handler), ('/module6', Module6Handler),
        ('/moduleX', ModuleXHandler), ('/dcl',DCLHandler),('/book', BookHandler), ('/quizquestions', QuizQuestionsHandler), ('/Quiz1', Quiz1Handler), ('/Quiz2', Quiz2Handler), ('/Quiz3', Quiz3Handler), ('/Quiz4', Quiz4Handler), ('/Quiz5', Quiz5Handler), ('/Quiz6', Quiz6Handler), ('/Quiz7', Quiz7Handler), ('/Quiz8', Quiz8Handler), ('/Quiz9', Quiz9Handler), ('/app-architecture', Handler14), ('/engineering-and-debugging', Handler15), ('/variables-1', Handler16),
        ('/animation-3', Handler17), ('/conditionals', Handler18), ('/lists-2', Handler19),
        ('/iteration-2', Handler20), ('/procedures-1', Handler21), ("/databases", Handler22), ("/sensors-1", Handler23),
        ("/apis", Handler24), ('/course-in-a-box_teaching', CourseInABoxHandlerTeaching), ('/media_teaching', MediaHandlerTeaching),
        ('/DeleteApp', DeleteApp), ('/AddStepPage', AddStepRenderer), ('/DeleteStep', DeleteStep), ('/AddCustomPage', AddCustomRenderer),
        ('/projects', BookHandler), ('/appinventortutorials', BookHandler), ('/get_app_data', GetAppDataHandler),
        ('/get_step_data', GetStepDataHandler), ('/get_custom_data', GetCustomDataHandler), ('/setup', SetupHandler), ('/setupAI2', SetupAI2Handler),
        ('/profile', ProfileHandler), ('/changeProfile', ChangeProfileHandler), ('/saveProfile', SaveProfile), ('/uploadPicture', UploadPictureHandler), ('/imageHandler', ImageHandler), ('/teacherMap', TeacherMapHandler), 
        ('/siteSearch', SearchHandler), ('/moleMashManymo', MoleMashManymoHandler),


        # AI1 APPS 
        ('/hellopurr-steps', NewAppRenderer), ('/paintpot-steps', NewAppRenderer), ('/molemash-steps', NewAppRenderer),
        ('/shootergame-steps', NewAppRenderer), ('/no-text-while-driving-steps', NewAppRenderer), ('/ladybug-chase-steps', NewAppRenderer),
        ('/map-tour-steps', NewAppRenderer), ('/android-where-s-my-car-steps', NewAppRenderer), ('/quiz-steps', NewAppRenderer),
        ('/notetaker-steps', NewAppRenderer), ('/xylophone-steps', NewAppRenderer), ('/makequiz-and-takequiz-1-steps', NewAppRenderer),
        ('/broadcaster-hub-1-steps', NewAppRenderer), ('/robot-remote-steps', NewAppRenderer), ('/stockmarket-steps', NewAppRenderer),
        ('/amazon-steps', NewAppRenderer),

        # AI2
        ('/IHaveADream-steps', NewAppRenderer_AI2), ('/paintpot2-steps', NewAppRenderer_AI2), ('/presidentsQuiz2-steps', NewAppRenderer_AI2), ('/notext-steps', NewAppRenderer_AI2), ('/mathblaster-steps', NewAppRenderer_AI2), ('/AndroidMash-steps', NewAppRenderer_AI2), ('/PresidentsQuiz-steps', NewAppRenderer_AI2), ('/pong-steps', NewAppRenderer_AI2), ('/stockMarket-steps', NewAppRenderer_AI2), ('/logo-steps', NewAppRenderer_AI2),
        ('/book2', Book2Handler), ('/starterApps', StarterAppsHandler), ('/appInventor2Changes', AppInventor2ChangesHandler), ('/presidentsQuizTut', PresidentsQuizTutHandler), ('/IHaveADreamTut', IHaveADreamTutHandler), ('/TimedActivity', TimedActivityHandler), ('/TimedActivitySound', TimedActivitySoundHandler), ('/TimedActivitySoundFive', TimedActivitySoundFiveHandler), ('/TimedActivitySpace', TimedActivitySpaceHandler), ('/TimedActivityFrame', TimedActivityFrameHandler), ('/TimedActivityStartClick', TimedActivityStartClickHandler), ('/TimedActivityStartSpeak', TimedActivityStartSpeakHandler), ('/TimedLists', TimedListsHandler), ('/TimedListsMusic', TimedListsMusicHandler), ('/TimedListsAsl', TimedListsAslHandler), ('/Conditionals', ConditionalsHandler), ('/Variables', VariablesHandler), ('/VariablesCircles', VariablesCirclesHandler),('/VariablesBackForth', VariablesBackForthHandler), 
        ('/recordItems', RecordingItemHandler), ('/recordItemsNotes', RecordingItemNotesHandler),('/recordItemsPhone', RecordingItemPhoneHandler), ('/incrementing', IncrementingVariablesHandler), ('/incrementingCount', IncrementingCountHandler),('/incrementingCountDown', IncrementingCountDownHandler), ('/Walkingalist', WalkingalistHandler), ('/Events', EventsRedBtnHandler), ('/Events-redbtn', EventsRedBtnHandler), ('/Events-shaking', EventsShakingHandler), ('/Lists', ListsHandler), ('/UserListNav', UserListNavHandler), ('/UserListNavNext', UserListNavNextHandler), ('/UserListNavPrev', UserListNavPrevHandler), ('/UserListNavLoop', UserListNavLoopHandler),('/Persistence', PersistenceHandler), ('/PersistenceMessage', PersistenceMessageHandler), ('/PersistenceNotes', PersistenceNotesHandler),('/FAQ', FAQHandler), ('/knowledgeMap', KnowledgeMapHandler), ('/lists', ListsHandler), ('/listsText', ListsTextHandler),('/listsSum', ListsSumHandler),
        ('/proc', ProcHandler), ('/procList', ProcListHandler), ('/procParam', ProcParamHandler), ('/procAnyLabel', ProcAnyLabelHandler),('/location', LocationHandler), ('/locationLatLong', LocationLatLongHandler),('/locationDistance', LocationDistanceHandler),('/resources', ResourcesHandler), ('/Drawing', DrawingHandler), ('/DrawingCanvas', DrawingCanvasHandler), ('/DrawingCircle', DrawingCircleHandler), ('/DrawingTouch', DrawingTouchHandler), ('/DrawingMiddle', DrawingMiddleHandler),('/sprites', SpritesHandler),('/spritesMove', SpritesMoveHandler),('/spritesBounce', SpritesBounceHandler),
        ('/MakeQuiz10', MakeQuiz10Handler), ('/teacherList', TeacherListHandler),
        ('/TeachingAI', TeachingAIHandler),
        # AI2 view all steps, error on 'IHaveADream'
        ('/IHaveADream', AppRenderer), ('/paintpot2', AppRenderer), ('/AndroidMash', AppRenderer), ('/presidentsQuiz2', AppRenderer), ('/notext', AppRenderer), ('/pong', AppRenderer), ('/stockMarket', AppRenderer), ('/logo', AppRenderer),
     
        # Comment
        ('/postComment', PostCommentHandler), 
        ('/deleteComment', DeleteCommentHandler),

        # Memcache Flush
        ('/memcache_flush_all', MemcacheFlushHandler),

        ('/conditionalsStart', ConditionalsStartHandler),
        ('/introIf', ConditionsHandler),
        ('/conditionalsWhere', ConditionalsWhereHandler),

        ('/IHaveADream2', IHaveADreamHandler),
        ('/properties', PropertiesHandler),
        ('/eventHandlers', EventHandlersHandler),
        ('/quizly', QuizlyHandler),
        ('/conditionalsInfo', ConditionalsInfoHandler),
        ('/workingWithMedia', WorkingWithMediaHandler),
        ('/mathBlaster', MathBlasterHandler),
        ('/appInventor2', AppInventor2Handler),
        ('/slideshowQuiz', SlideShowQuizHandler),
        ('/javaBridgePage', JavaBridgePageHandler),
        ('/meetMyClassmates', MeetMyClassmatesHandler),
        ('/webDatabase', WebDatabaseHandler),
        ('/concepts', ConceptsHandler),
        ('/abstraction', AbstractionHandler), 
        ('/galleryHowTo', GalleryHowToHandler),
        ('/sentEmail', EmailHandler), 
        ('/bookFiles', BookFilesHandler),

        # Update Database
        ('/updateDB', UpdateDatabase),
        ('/updateDBGEO', UpdateGEODatabase),
        ('/PrintOut', PrintOut),
        ('/convertProfileName1', ConvertProfileName1),
        ('/convertProfileName2', ConvertProfileName2),
        ('/printUserName', PrintUserName),
        ('/stepIframe', StepIframe),
        
        # Web Tutorial
        ('/webtutorial', WebTutorialHandler),
        ('/get_tutorial_data', GetTutorialDataHandler),
        ('/PostTutorial', PostTutorial),
        ('/AddTutorialStepPage', AddTutorialStepRenderer),
        ('/PostTutorialStep', PostTutorialStep),
        ('/get_tutorial_step_data', GetTutorialStepDataHandler),

        # Public Profile
        ('/publicProfile', PublicProfileHandler),

        # AI2 Chapter
        ('/PaintPot2', PaintPot2Handler),
        ('/MoleMash2', MoleMash2Handler),
        ('/HelloPurr2', HelloPurr2Handler),
        ('/NoTexting2', NoTexting2Handler),
        ('/PresidentsQuiz2', PresidentsQuiz2Handler),
        ('/MapTour2', MapTour2Handler),
        ('/AndroidCar2', AndroidCar2Handler),
        ('/BroadcastHub2', BroadcastHub2Handler),
        ('/Architecture2', Architecture2Handler),
        ('/Engineering2', Engineering2Handler),
        ('/Variables2', Variables2Handler),
        ('/Creation2', Creation2Handler),
        ('/Conditionals2', Conditionals2Handler),
        ('/Lists2', Lists2Handler),
        ('/Iteration2', Iteration2Handler),
        ('/Procedures2', Procedures2Handler),
        ('/Databases2', Databases2Handler),
        ('/Sensors2', Sensors2Handler),
        ('/API242', API242Handler),
        ('/Xylophone2', XYLoPhone2Handler),
        ('/Ladybug2', Ladybug2Handler),
        ('/starterApps', StarterAppsHandler),
        ('/robots', RobotsHandler),
        ('/amazonChapter', AmazonHandler),
        ('/biblio', BiblioHandler),
        
        # Course additional reading and material handlers
        ('/mod1reading', Mod1ReadingHandler),
        ('/mod2reading', Mod2ReadingHandler),
        ('/mod3reading', Mod3ReadingHandler),
        ('/mod4reading', Mod4ReadingHandler),
        ('/mod5reading', Mod5ReadingHandler),
        ('/mod6reading', Mod6ReadingHandler),
        ('/mod7reading', Mod7ReadingHandler),

        # Page that contains all the quizzes
        ('/Quizzes', QuizzesHandler),
        # HTML bookChapters
        ('/Chapter1', Chapter1Handler),
        ('/Chapter2', Chapter2Handler),
        ('/Chapter3', Chapter3Handler),
        ('/Chapter4', Chapter4Handler),
        ('/Chapter5', Chapter5Handler),
        ('/Chapter6', Chapter6Handler),
        ('/Chapter7', Chapter7Handler), 
        ('/Chapter8', Chapter8Handler),
        ('/Chapter9', Chapter9Handler),
        ('/Chapter10', Chapter10Handler),
        ('/Chapter11', Chapter11Handler),
        ('/Chapter12', Chapter12Handler),
        ('/Chapter13', Chapter13Handler),
        ('/Chapter14', Chapter14Handler),
        ('/Chapter15', Chapter15Handler),
        ('/Chapter16', Chapter16Handler),
        ('/Chapter17', Chapter17Handler),
        ('/Chapter18', Chapter18Handler),
        ('/Chapter19', Chapter19Handler),
        ('/Chapter20', Chapter20Handler),
        ('/Chapter21', Chapter21Handler),
        ('/Chapter22', Chapter22Handler),
        ('/Chapter23', Chapter23Handler),
        ('/Chapter24', Chapter24Handler),
        
        # Cayla's Pages
        ('/screens', ScreenHandler),
        ('/screensSwap', ScreenSwapHandler),
        ('/screensShare', ScreenShareHandler),
        ('/HelloPurrMini', HelloPurrMiniHandler),
        ('/aiSetUp', AppInventorSetUpHandler),
        ('/NewIHaveADream', NewIHaveADreamHandler),
        ('/preface', PrefaceHandler),
        ('/conceptualizePaintPot', ConceptualizePaintPotHandler),
        ('/conceptualizeMoleMash', ConceptualizeMoleMashHandler),
        ('/animationChallenge', AnimationChallengeHandler),
        ('/creativeProject2Game', CreativeProject2GameHandler),
        ('/googleVoice', GoogleVoiceHandler),
        ('/conceptualizeNoTexting', ConceptualizeNoTextingHandler),
        ('/conceptualizeLocation', ConceptualizeLocationHandler),
        ('/conceptualizeStockMarket', ConceptualizeStockMarketHandler),
        ('/pretest', PretestHandler),
        ('/listiteration', ListIterationHandler),
        ('/conceptualizeSlideshow', ConceptualizeSlideshowHandler),
        ('/conceptualizeProcedures', ConceptualizeProceduresHandler),
        ('/conceptualizeIteration', ConceptualizeIterationHandler),
        ('/conceptualizeNoteTaker', ConceptualizeNoteTakerHandler),
        ('/conceptualizeCommunication', ConceptualizeCommunicationHandler),
        ('/pizzaParty', PizzaPartyHandler),
        
        ('/gDoc', gDocHandler),        
    
    
        
    
        # new home page
        ('/', Homehandler, BlogHandler),
        
        # courses page 
        ('/content', TutorialsHandler),
        
        # modules page
        webapp.Route(r'/content/<course_ID>', CourseOverviewHandler),
        
        # contents page
        webapp.Route(r'/content/<course_ID>/<module_ID>', ContentsHandler),
        
        # content display page
        webapp.Route(r'/content/<course_ID>/<module_ID>/<content_ID>', ContentHandler),
          
        # Editor Display Handlers
        ('/admin/courses', AdminCourseDisplayHandler),  # courses menu
        webapp.Route(r'/admin/courses/<course_ID>', handler=AdminModuleDisplayHandler),  # modules menu
        webapp.Route(r'/admin/courses/<course_ID>/<module_ID>', handler=AdminContentsDisplayHandler),  # contents menu
        webapp.Route(r'/admin/courses/<course_ID>/<module_ID>/<content_ID>', handler=AdminContentDisplayHandler),  # contents menu
        
        # Editor Modifier Handlers
        webapp.Route(r'/admin/course_system/create/<kind>', handler=AdminCourseSystemCreateHandler),
        webapp.Route(r'/admin/course_system/delete/<kind>', handler=AdminCourseSystemDeleteHandler),
        webapp.Route(r'/admin/course_system/reorder/<kind>', handler=AdminCourseSystemReorderHandler),
        webapp.Route(r'/admin/course_system/update/<kind>', handler=AdminCourseSystemUpdateHandler),
        
        # more admin pages
        ('/admin/dashboard', AdminDashboardHandler),
        ('/admin/apps', AdminHandler),
        ('/admin/exportcourses', AdminExportCoursesHandler),
        ('/admin/importcourses', AdminImportCoursesHandler),
        ('/admin/serialview', AdminSerialViewHandler),
        
        # used on the teacher map page
        ('/getEducatorsInfo', getEducatorsInfo),
        ('/getEducatorsTiles', getEducatorsTiles),
        
        # teacher module
         ('/teacherIntro', TeacherIntroHandler),
         ('/teacherIntroIntro', TeacherIntroIntroHandler),
        
        # handles logging in and sign up
        ('/loginValidator', loginValidationHandler),
        ('/createAccount', CreateAccountHandler),
        ('/registerAccount', RegisterAccountHandler),
        ('/updateAccount', updateAccountHandler),
        ('/updateProfilePicture', updateProfilePictureHandler),
        
        #RSS feed stuff
        ('/admin/updateRSS', updateRSSHandler),
        
        
        
        ('/Objective1', ObjectivesModule1),
        
        
        
        #Handlers for introduction Module
        ('/ihdworksheet',IHDWorksheetHandler),
        ('/setup_options' , SetupOptionsHandler ),
        ('/setup_portfolio' , SetupPortfolioHandler),
        ('/pcworksheet', PCworksheethandler),
        ('/appmakercards', AppMakerCardsHandler),
        ('/lessonplan11' , LessonPlan11Handler),
        ('/lessonplan12', LessonPlan12Handler),
        
        #Handlers for build drawing and animated games module
        ('/conceptualizeCustomize', CCPaintPotHandler),
        ('/incrementingTiming', IncrementingTimingWSHandler),
        ('/molemashCC', MoleMashCCHandler),
        ('/animationChallenge', AnimationChallengeHandler),
        ('/advancedanimationWS', AdvancedAnimationWSHandler),
        ('/lessonplan21', LessonPlan21Handler),
        ('/lessonplan22', LessonPlan22Handler),
        ('/lessonplan23', LessonPlan23Handler),
        
        #Handlers for module 3 Course in a Box
        ('/googlevoicesetup', GoogleVoiceSetupHandler),
        ('/whereamiapp', WhereAmIAppHandler),
        ('/conceptcustomizeWS', ConceptCustomizeWSHandler),
        ('/locationws', LocationWSHandler),
        ('/lessonplan31', LessonPlan31Handler),
        ('/lessonplan32', LessonPlan32Handler),
        
        #Handlers for module 4
        ('/listindextpretest', LIPHandler),
        ('/iteratinglist', IteratingListExample),
        ('/listindexCC', ListIndexCCHandler),
        ('/indexingchallenges', IndexingChallengesHandler),
        ('/listchoosing', ListChoosingHandlers),
        ('/lessonplan41', LessonPlan41Handler),
        ('/lessonplan42', LessonPlan42Handler),
        ('/lessonplan43', LessonPlan43Handler),
        
        #Handlers for module
        ('/notetakertut', NoteTakerTutHandler),
        ('/customizesoundboard', SoundBoardAppHandler),
        ('/userGeneratedDataCC', UserGeneratedDataHandler),
        
        
        #handler for intro drawing ani games module
        ('/introdrawing', IntroDrawingHandler),
        ('/carouseltest', CarouselTestHandler),
        ('/canvasComponent', CanvasComponentHandler),
        ('/canvasProperties', CanvasPropertiesHandler),
        ('/canvasComponentNugget', CanvasComponentNuggetHandler),
        ('/canvasComponentMaster', CanvasComponentMasterHandler),
        ('/canvasComponentNuggetMaster', CanvasComponentMasterNuggetHandler),
        ('/VariablesCirclesNugget', VariablesCirclesNuggetHandler ),
        ('/variableCircleMaster', VariableCircleMasterHandler),
        ('/paintPotText', PaintPotTextHandler),
        ('/howGamesWork', HowGamesWorkHandler),
        ('/incrementingws', IncrementingWSHandler),
        ('/timerEvent', TimerEventHandler),
        ('/molemashtext', MoleMashTextHandler),
                
        ('/about', AboutHandler),
        ('/about/blog', BlogHandler),
        ('/about/team', TeamHandler),
        ('/about/contact-us', ContactUsHandler),

        
        #handlers for intro module pages

        ('/aianimation', AIAnimationHandler),
        ('/howanimationworks', HowAnimationworksHandler),
        ('/animationchallengebrian', AnimationChallengeBrianHandler),
        ('/animationChallengeHelp', AnimationChallengeHelpHandler),
        ('/animationChallengeinternal', AnimationChallengeInternalHandler),
        ('/animationinternalcomp', AnimationIntComponentHandler),
        ('/pongtutorial', PongTutorialHandler),
        
         #handlers for intro module pages

        ('/introTextingLocation',IntroTextingLocationHandler),
        ('/introQuizzesInfo',IntroQuizzesInformationHandler),
        ('/introProcedures',IntroProceduresHandler),
        ('/introUserGen',IntroUserGeneratedHandler),
        ('/introWeb',IntroWebEnabledAppsHandler),

        ('/introIntro', IntroIntroductionHandler),



        #Handlers for Java Bridge
        ('/jBridgeIntro', JBridgeIntroHandler),
        ('/jBridgeRedClickEclipse', JBridgeRedClickEclipseHandler),
        ('/jBridgeRedClickAndroid', JBridgeRedClickAndroidHandler),
        ('/jBridgeBasics', JBridgeBasicsHandler),
        ('/jBridgeMoleMash', JBridgeMoleMashHandler),
        ('/jBridgePaintPot', JBridgePaintPotHandler),
        ('/jbridge-presidents-quiz', JBridgePrezQuiz),
        ('/jbridge-stock-market-tracker', JBridgeStockMarket),


        ('/course-in-a-box-intro', CourseInABoxIntroHanlder),


        #handlers for procedures gdoc
        ('/introToProcedures', IntroToProceduresHandler),

        #handlers for essential training
        ('/arrangingComponents', ArrangingComponentsHandler),
        ('/aidesigner', AIDesignerHandler),
        ('/blocksEditor', BlocksEditorHandler),


        ('/asteroids-part1', AsteroidsPart1Handler),

        #Leonard's pages
        ('/whatTheHeckIsCheckpoint', WhatTheHeckIsCheckpointHandler),
        ('/firebaseDB', FirebaseDBHandler),
        ('/hueNew', HueNewHandler),
<<<<<<< HEAD
        ('/UImoreAboutButtons', UIMoreAboutButtonsHandler),
        ('/UILLTC', UILLTCHandler),
        ('/UImultipleScreens', UIMultipleScreensHandler),
        ('/UIarrangements', UIArrangementsHandler),
        ('/UIscroll', UIScrollHandler),
        ('/javaBridge', javaBridgeHandler)
=======

        ('/jbridge', JBridgeHandler)
>>>>>>> a0a97ced319e885819e0235561f0d84241ed0a37


    ],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()



