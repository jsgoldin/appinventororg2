import logging
import os
import collections
try: import simplejson as json
except ImportError: import json
from google.appengine.ext import ndb

from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from datastore import App
from datastore import Step
from datastore import Custom
from datastore import Account
from datastore import Comment
from datastore import Tutorial
from datastore import TutorialStep
from datastore import Module, Content, Course
import gdata.analytics.client
import datetime
from geopy import geocoders
from google.appengine.api import mail


APPSDIR = '/apps'
APPS2DIR = '/apps2'


def redirector(requesthandler):
    """Used to redirect old content to their new url in a course
    
    Returns true if a redirect occurs and false otherwise.
    
    The caller function should return if a redirect occurs
    as to stop unwanted execution of code in the caller function
    following the call to redirector.
    """
    # redirect test
    if requesthandler.request.get('flag') == 'true':
        logging.info("Do not redirect!")
        return False
    else:
        # look up a content that uses this url
        results = Content.query(ancestor=ndb.Key('Courses', 'ADMINSET')).filter(Content.c_url == requesthandler.request.path + "?flag=true").fetch()
        if len(results) == 0:
            logging.error("Could not find a content to redirect too!")
        else:
            content = results[0]
            # build the url
            content_id = content.c_identifier
            module_id = content.key.parent().get().m_identifier
            course_id = content.key.parent().parent().get().c_identifier
            redirectURL = "courses/" + course_id + "/" + module_id + "/" + content_id
                
            logging.info("redirecting: " + requesthandler.request.path + " >>> " + redirectURL)
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

class Home(webapp.RequestHandler):
    def get(self):
        #
        # login_url=users.create_login_url(self.request.uri)
        #       logout_url=users.create_logout_url(self.request.uri)

        # allAppsQuery = db.GqlQuery("SELECT * FROM App ORDER BY number ASC")

        # appCount = allAppsQuery.count()
        # allAppsList = allAppsQuery.fetch(appCount)
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        # visitor
        try:            
            pquery = db.GqlQuery("SELECT * FROM AdminAccount where name= :1 ", "System Account")
            adminAccount = pquery.get()
            email = adminAccount.gmail
            password = adminAccount.password
            table_ids = (
                        'ga:34666339',  # TABLE_ID for first website
                                                # This is the table ID, or can be seen as
                                                # ga: PROFILE_ID
                                                # THe profile_id of Appinventor.org is 34666339
                                                # (...)
                        )

            SOURCE_APP_NAME = 'Genomika-Google-Analytics-Quick-Client-v1'
            client = gdata.analytics.client.AnalyticsClient(source=SOURCE_APP_NAME)
            client.client_login(email, password, source=SOURCE_APP_NAME, service=client.auth_service)

            today = datetime.date.today()
            yesterday = today - datetime.timedelta(days=2000)
            counter = 0
            for table_id in table_ids:
                for table_id in table_ids:
                    data_query = gdata.analytics.client.DataFeedQuery({
                    'ids': table_id,
                    'start-date':yesterday.isoformat(),
                    'end-date': today.isoformat(),
                    'metrics': 'ga:visits, ga:pageviews'})      
            feed = client.GetDataFeed(data_query)                                           
             
            numVisitors = feed.entry[0].metric[0].value
            
        except:
            numVisitors = "970979"
        numVisitors = int(numVisitors)
        formattedCounter = intWithCommas(numVisitors)
        template_values = {'allAppsList': allAppsList, 'userStatus': userStatus, 'counter': formattedCounter}
        
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/index.html')
        self.response.out.write(template.render(path, template_values))


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

        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)




        template_values = {'account': account, 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/publicProfile.html')
        self.response.out.write(template.render(path, template_values))



class ProfileHandler(webapp.RequestHandler):
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




        template_values = {'account': account, 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus,
                         'ifEducatorShow': ifEducatorShow, 'educationLevel': educationLevel, 'educationLevelCheck0': educationLevelCheck0, 'educationLevelCheck1': educationLevelCheck1, 'educationLevelCheck2': educationLevelCheck2}
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

        template_values = {'account': account, 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus,
                         'ifEducatorShow': ifEducatorShow, 'educationLevelCheck0': educationLevelCheck0, 'educationLevelCheck1': educationLevelCheck1, 'educationLevelCheck2': educationLevelCheck2}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/changeProfile.html')
        self.response.out.write(template.render(path, template_values))
    
        
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
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
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
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()                    
                    
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
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
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
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
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
    
class StarterAppsHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/starterApps.html')
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
       
class ResourcesHandler(webapp.RequestHandler):
    def get(self):
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()                    
                    
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
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/incrementing-count.html')
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
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/incrementing-countDown.html')
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


class FAQHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/aiFAQ.html')
        self.response.out.write(template.render(path, template_values))

class ListsHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/lists.html')
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

class MediaHandlerTeaching(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/paintpot.html')
        self.response.out.write(template.render(path, template_values))

class StarterAppsHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/starterApps.html')
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

        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'manyMoldAppsList': manyMoldAppsList, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/tryit.html')
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
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
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
        
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()                    
                    
        userStatus = UserStatus().getStatus(self.request.uri)
        
        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
                           }
        
        
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/teachingAI.html')
        self.response.out.write(template.render(path, template_values))

class PresidentsQuiz2Handler(webapp.RequestHandler):
    def get(self):
        
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
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/eventHandlers.html')
        self.response.out.write(template.render(path, template_values))

class ConditionalsInfoHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/conditionals.html')
        self.response.out.write(template.render(path, template_values))

class PropertiesHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus, 'apps2Dir':APPS2DIR}
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

class JavaBridgeHandler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/javaBridge.html')
        self.response.out.write(template.render(path, template_values))

class AppInventor2Handler(webapp.RequestHandler):
    def get(self):
        
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
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
###END OF QUIZ 1###

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
###END OF QUIZ 9###




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

class ContactHandler(webapp.RequestHandler):
    def get(self):
        
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        template_values = { 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/contact.html')
        self.response.out.write(template.render(path, template_values))

class BookHandler(webapp.RequestHandler):
    def get(self):
        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()                    

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
        
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()                    

        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor 2 Book: Create Your Own Android Apps',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
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
        
       
class AboutHandler(webapp.RequestHandler):
    def get(self):
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()                    
                    
        userStatus = UserStatus().getStatus(self.request.uri)
        
        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'About Us',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/about.html')
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
        
        template_values = { 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'userStatus': userStatus}
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
        user = users.get_current_user()
        account_query = db.GqlQuery("Select * from Account where user=:1", user)
        account = account_query.get()

        # if not account:
        #    self.redirect('/assets/img/avatar-default.gif')
        #    return
            
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
            # self.response.headers['Content-Type'] = "image/png"
            # self.response.out.write('/assets/img/avatar-default.gif')
            # self.error(404)
# Map
class TeacherMapHandler(webapp.RequestHandler):
    def get(self):

        # all apps list
        cacheHandler = CacheHandler()
        allAppsList = cacheHandler.GettingCache("App", True, "version", "1", True, "number", "ASC", True)
        allAppsList2 = cacheHandler.GettingCache("App", True, "version", "2", True, "number", "ASC", True)

        # user status
        userStatus = UserStatus()
        userStatus = userStatus.getStatus(self.request.uri)
        # allAccountsQuery = db.GqlQuery("SELECT * FROM Account")
        allAccountsQuery = db.GqlQuery("SELECT * FROM Account WHERE ifEducator=:1", True)
                                                                                    # now only show teachers
                                                                      
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()                    
                    
        userStatus = UserStatus().getStatus(self.request.uri)
        

        accountCount = allAccountsQuery.count()
        accounts = allAccountsQuery.fetch(accountCount)

        account_k_8 = []
        account_high_school = []
        account_college_university = []
        for account in accounts:
           if(account.ifEducator):
               if(account.educationLevel == "K-8"):
                   account_k_8.append(account)
               elif(account.educationLevel == "High School"):
                   account_high_school.append(account)
               elif(account.educationLevel == "College/University"):
                   account_college_university.append(account)
               

        
        template_values = { 'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'], 'allAppsList': allAppsList, 'allAppsList2': allAppsList2, 'accounts': accounts, 'account_k_8':account_k_8, 'account_high_school':account_high_school, 'account_college_university':account_college_university, 'userStatus': userStatus}
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/maps.html')
        self.response.out.write(template.render(path, template_values))               
               
# Google Custom Search
class SearchHandler (webapp.RequestHandler):
    def get(self):
        
        query = self.request.get("q")
        logging.info(query)
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()                    
                    
        userStatus = UserStatus().getStatus(self.request.uri)
        
        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'Search Results: ' + query,
                           'stylesheets' : ['/assets/css/coursesystem.css'],
                           'scripts' : [],
                           'query' : query,
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

        loginurl = users.create_login_url(uri)
        logouturl = users.create_logout_url('/')

        admin = False
        if user:
            ifUser = True
            if users.is_current_user_admin():
                admin = True
        else:
            ifUser = False

        
        
        status = {'loginurl': loginurl, 'logouturl':logouturl, 'ifUser':ifUser, 'account':account, 'admin': admin}
        return status




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
        adam_boolean = true
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


class TestTemplateHandler(webapp.RequestHandler):
    def get(self):

        quiz = self.request.url.rsplit('/', 1)[1]

        template_values = {
            'message': quiz
        }
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/DjangoTest.html')
        self.response.out.write(template.render(path, template_values))

class ScreenHandler(webapp.RequestHandler):
    def get(self):
        template_values = {}

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/screens.html')
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

        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/animationChallenge.html')
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

# Displays the home page of app inventor
class Homehandler(webapp.RequestHandler):
    def get(self):
        # look up all the courses for the global navbar
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()                    
                    
        userStatus = UserStatus().getStatus(self.request.uri)
        
        template_values = {'courses' : courses,
                           'userStatus': userStatus,
                           'title' : 'App Inventor',
                           'stylesheets' : ['/assets/css/coursesystem.css', '/assets/css/owl.carousel.css', '/assets/css/owl.theme_original.css'],
                           'scripts' : ['/assets/js/owl.carousel.js', '/assets/js/home.js'],
                           }
        path = os.path.join(os.path.dirname(__file__), 'pages/home.html')
        self.response.out.write(template.render(path, template_values))  

class TutorialsHandler(webapp.RequestHandler):
    def get(self):
        # retreive all of the courses
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()
        

        userStatus = UserStatus().getStatus(self.request.uri)
                       
        
        template_values = {'courses' : courses,
                           'stylesheets' : ['/assets/css/coursesystem.css'],
                           'scripts' : ['/assets/js/coursesystem.js'],
                           'userStatus': userStatus,
                           'title' : 'Courses'
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'pages/tutorials.html')
        self.response.out.write(template.render(path, template_values))

class ModulesHandler(webapp.RequestHandler):
    def get(self, course_ID=''):    
        # retrieve the course entity with the course_ID
        x = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).filter(Course.c_identifier == course_ID).fetch()
        
        if len(x) == 0:
            template_values = {}
            path = os.path.join(os.path.dirname(__file__), 'pages/pagenotfound.html')
            self.response.out.write(template.render(path, template_values))  
        else:
            # course exists find the first module            
            # and redirect to that
            
            courseId = x[0].key.id()
            modules = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, courseId)).order(Module.m_index).fetch()
            
            course = x[0]
            first_module = modules[0]
             
            self.redirect(course.c_identifier + "/" + first_module.m_identifier)     

class ContentsHandler(webapp.RequestHandler):
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
                courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()
                
                # construct dictionary of courses to modules mapping

                modules = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course_entity.key.id()))).order(Module.m_index).fetch()    
                
             
                userStatus = UserStatus().getStatus(self.request.uri)
                       
                template_values = {"title" : course_entity.c_title ,
                               "module" : module_entity,    
                               "modules" : modules,
                               'stylesheets' : ['/assets/css/coursesystem.css'],
                               'scripts' : ['/assets/js/coursesystem.js'],
                               'userStatus': userStatus,
                               'contents' : contents,
                               'courses' : courses,
                                }


                path = os.path.join(os.path.dirname(__file__), 'pages/modules.html')
                self.response.out.write(template.render(path, template_values))
                
                
               
class ContentHandler(webapp.RequestHandler):
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
                    courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()
                    
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
                           'stylesheets' : ['/assets/css/coursesystem.css'],
                           'scripts' : ['/assets/js/coursesystem.js'],
                           'userStatus': userStatus
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
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()
        
        template_values = {"courses" : courses,
                           'stylesheets' : ['/assets/admin/css/editor.css', '/assets/admin/css/admin.css', '/assets/css/coursesystem.css'],
                           'scripts' : ['/assets/admin/js/courses_editor.js'],
                           'title' : 'Courses Admin',
                           'userStatus' : userStatus
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
            courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()
        
            
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
                courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()            

          
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
                    courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()            


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
            
            new_content = Content(parent=ndb.Key('Courses', 'ADMINSET', Course, long(course_id), Module, long(module_id)), c_title=title, c_description=description, c_type=content_type, c_url=file_path)
            new_content.c_identifier = identifier
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
            # retrieve content entity and update it
            content = ndb.Key('Courses', 'ADMINSET', Course, long(course_id), Module, long(module_id), Content, long(content_id)).get()
            content.c_title = title
            content.c_description = description
            content.c_url = url
            content.c_type = content_type
            content.c_identifier = identifier
            content.put()
        else:
            logging.error("An invalid kind was attempted to be updated: " + kind)


class AdminDashboardHandler(webapp.RequestHandler):    
    def get(self):                      
        userStatus = UserStatus().getStatus(self.request.uri)
        
        # look up all the courses for the global navbar
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()
                    
        template_values = {
                           'stylesheets' : ['/assets/admin/css/admin.css', '/assets/css/coursesystem.css'],
                           'userStatus' : userStatus,
                           'courses' : courses,
                           'title' : 'Admin Dashboard'
                           }
        
        path = os.path.join(os.path.dirname(__file__), 'pages/admin/admin_dashboard.html')
        self.response.out.write(template.render(path, template_values))        

class AdminExportCoursesHandler(webapp.RequestHandler):
    def get(self):

        userStatus = UserStatus().getStatus(self.request.uri)
        
        # look up all the courses for the global navbar
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()
                
        
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
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()
            
        

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
        """ For now this wipes this completely replaces the current contents of the datastore 
        with the imported file. """
        
        
        # delete everything in the current datastore
        
        keysToDelete = []
        
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()
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
                    
                    if content_Index == 'None':
                        content_Index = 0
                   
                    content = Content(parent=ndb.Key('Courses', 'ADMINSET', Course, long(course.key.id()), Module, long(module.key.id())), c_title=content_Title, c_description=content_Description, c_type=content_Type, c_url=content_URL , c_index=int(content_Index), c_identifier=content_Identifier)
                    content.put() 
                i += 1
            i += 1
          


class AdminSerialViewHandler(webapp.RequestHandler):
    """ Creates a serialized output of the courses and content on the site, this page is intended to be 
        downloaded by the user via the course export page. """
    def get(self):
        output = ""
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()
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
                    output += content.c_title + "\n" + content.c_description + "\n" + content.c_type + "\n" + content.c_url + "\n" + str(content.c_index) + "\n" + content.c_identifier + "\n"
                output += "*****\n"
            output += "**********\n"        
        
        self.response.out.write(output)

# TODO: DELETE
class testView(webapp.RequestHandler):
    
    def get(self):
        output = ""
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()
        # for every course
        for course in courses:
            # for every module
            modules = Module.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course.key.id()))).order(Module.m_index).fetch()
            for module in modules:
                # for every content
                contents = Content.query(ancestor=ndb.Key('Courses', 'ADMINSET', Course, long(course.key.id()), Module, long(module.key.id()))).order(Content.c_index).fetch()
                for content in contents:
                    output += content.c_url + "<br>"
    
        
        self.response.out.write(output)        
        
        
class gDocHandler(webapp.RequestHandler):
    def get(self):
        
        userStatus = UserStatus().getStatus(self.request.uri)
        #docId="1f4lPDnfaxxKhzkWvoEuCrHNHpJBRWixIsxr8u0zJR9U"
        docId = self.request.get("docId")
        # look up all the courses for the global navbar
        courses = Course.query(ancestor=ndb.Key('Courses', 'ADMINSET')).order(Course.c_index).fetch()
            
        
        template_values = {
                           'stylesheets' : ['/assets/admin/css/admin.css'],
                           'userStatus' : userStatus,
                           'courses' : courses,
                           'title' : 'Admin Dashboard',
                           'scripts' : ['/assets/admin/js/import.js'],
                           'docId' : docId                           }       
        
        path = os.path.join(os.path.dirname(__file__), 'static_pages/other/gdoc.html')
        self.response.out.write(template.render(path, template_values))      
                

####################################
#       End Jordan's Classes       #
#                                  #
#                                  # 
####################################






# create this global variable that represents the application and specifies which class
# should handle each page in the site
application = webapp.WSGIApplication(
    # MainPage handles the home page load
    [
    # ('/', Home), uncomment to show old home page
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
        ('/moduleX', ModuleXHandler), ('/contact', ContactHandler), ('/about', AboutHandler), ('/book', BookHandler), ('/quizquestions', QuizQuestionsHandler), ('/Quiz1', Quiz1Handler), ('/Quiz2', Quiz2Handler), ('/Quiz3', Quiz3Handler), ('/Quiz4', Quiz4Handler), ('/Quiz5', Quiz5Handler), ('/Quiz6', Quiz6Handler), ('/Quiz7', Quiz7Handler), ('/Quiz8', Quiz8Handler), ('/Quiz9', Quiz9Handler), ('/app-architecture', Handler14), ('/engineering-and-debugging', Handler15), ('/variables-1', Handler16),
        ('/animation-3', Handler17), ('/conditionals', Handler18), ('/lists-2', Handler19),
        ('/iteration-2', Handler20), ('/procedures-1', Handler21), ("/databases", Handler22), ("/sensors-1", Handler23),
        ("/apis", Handler24), ('/course-in-a-box_teaching', CourseInABoxHandlerTeaching), ('/media_teaching', MediaHandlerTeaching),
        ('/DeleteApp', DeleteApp), ('/AddStepPage', AddStepRenderer), ('/DeleteStep', DeleteStep), ('/AddCustomPage', AddCustomRenderer),
        ('/projects', BookHandler), ('/appinventortutorials', BookHandler), ('/get_app_data', GetAppDataHandler),
        ('/get_step_data', GetStepDataHandler), ('/get_custom_data', GetCustomDataHandler), ('/setup', SetupHandler), ('/setupAI2', SetupAI2Handler),
        ('/profile', ProfileHandler), ('/changeProfile', ChangeProfileHandler), ('/saveProfile', SaveProfile), ('/uploadPicture', UploadPictureHandler), ('/imageHandler', ImageHandler), ('/teacherMap', TeacherMapHandler),
        ('/siteSearch', SearchHandler), ('/moleMashManymo', MoleMashManymoHandler),


        # NewAppRenderer 
        ('/hellopurr-steps', NewAppRenderer), ('/paintpot-steps', NewAppRenderer), ('/molemash-steps', NewAppRenderer),
        ('/shootergame-steps', NewAppRenderer), ('/no-text-while-driving-steps', NewAppRenderer), ('/ladybug-chase-steps', NewAppRenderer),
        ('/map-tour-steps', NewAppRenderer), ('/android-where-s-my-car-steps', NewAppRenderer), ('/quiz-steps', NewAppRenderer),
        ('/notetaker-steps', NewAppRenderer), ('/xylophone-steps', NewAppRenderer), ('/makequiz-and-takequiz-1-steps', NewAppRenderer),
        ('/broadcaster-hub-1-steps', NewAppRenderer), ('/robot-remote-steps', NewAppRenderer), ('/stockmarket-steps', NewAppRenderer),
        ('/amazon-steps', NewAppRenderer),

        # AI2

        ('/IHaveADream-steps', NewAppRenderer_AI2), ('/paintpot2-steps', NewAppRenderer_AI2), ('/presidentsQuiz2-steps', NewAppRenderer_AI2), ('/notext-steps', NewAppRenderer_AI2), ('/mathblaster-steps', NewAppRenderer_AI2), ('/AndroidMash-steps', NewAppRenderer_AI2), ('/PresidentsQuiz-steps', NewAppRenderer_AI2), ('/pong-steps', NewAppRenderer_AI2), ('/stockMarket-steps', NewAppRenderer_AI2), ('/logo-steps', NewAppRenderer_AI2),
    ('/book2', Book2Handler), ('/starterApps', StarterAppsHandler), ('/appInventor2Changes', AppInventor2ChangesHandler), ('/presidentsQuizTut', PresidentsQuizTutHandler), ('/IHaveADreamTut', IHaveADreamTutHandler), ('/TimedActivity', TimedActivityHandler), ('/TimedLists', TimedListsHandler), ('/Conditionals', ConditionalsHandler), ('/Variables', VariablesHandler), ('/recordItems', RecordingItemHandler), ('/incrementing', IncrementingVariablesHandler), ('/incrementingCount', IncrementingCountHandler),('/incrementingCountDown', IncrementingCountDownHandler), ('/Walkingalist', WalkingalistHandler), ('/Events-redbtn', EventsRedBtnHandler), ('/Events-shaking', EventsShakingHandler), ('/Lists', ListsHandler), ('/UserListNav', UserListNavHandler), ('/Persistence', PersistenceHandler), ('/FAQ', FAQHandler), ('/knowledgeMap', KnowledgeMapHandler), ('/lists', ListsHandler),
    ('/proc', ProcHandler), ('/location', LocationHandler), ('/resources', ResourcesHandler), ('/Drawing', DrawingHandler), ('/sprites', SpritesHandler),
     ('/MakeQuiz10', MakeQuiz10Handler), ('/teacherList', TeacherListHandler),
     ('/TeachingAI', TeachingAIHandler),
        # AI2 view all steps, error on 'IHaveADream'
        # ('/IHaveADream', AppRenderer),
        ('/IHaveADream', AppRenderer), ('/paintpot2', AppRenderer), ('/AndroidMash', AppRenderer), ('/presidentsQuiz2', AppRenderer), ('/notext', AppRenderer), ('/pong', AppRenderer), ('/stockMarket', AppRenderer), ('/logo', AppRenderer),
     
        # Comment
        ('/postComment', PostCommentHandler), ('/deleteComment', DeleteCommentHandler),

        # Memcache Flush
        ('/memcache_flush_all', MemcacheFlushHandler),

        ('/conditionalsStart', ConditionalsStartHandler),('/introIf', ConditionsHandler),
        ('/conditionalsWhere', ConditionalsWhereHandler),

        ('/IHaveADream2', IHaveADreamHandler), ('/properties', PropertiesHandler), ('/eventHandlers', EventHandlersHandler), ('/quizly', QuizlyHandler), ('/conditionalsInfo', ConditionalsInfoHandler), ('/workingWithMedia', WorkingWithMediaHandler), ('/mathBlaster', MathBlasterHandler), ('/appInventor2', AppInventor2Handler) , ('/slideshowQuiz', SlideShowQuizHandler), ('/javaBridge', JavaBridgeHandler), ('/meetMyClassmates', MeetMyClassmatesHandler), ('/webDatabase', WebDatabaseHandler), ('/concepts', ConceptsHandler), ('/abstraction', AbstractionHandler), ('/galleryHowTo', GalleryHowToHandler),
        ('/sentEmail', EmailHandler),

        # Update Database
        ('/updateDB', UpdateDatabase), ('/updateDBGEO', UpdateGEODatabase), ('/PrintOut', PrintOut),
        ('/convertProfileName1', ConvertProfileName1), ('/convertProfileName2', ConvertProfileName2),
        ('/printUserName', PrintUserName),
        ('/stepIframe', StepIframe),
        
        # Web Tutorial
        ('/webtutorial', WebTutorialHandler), ('/get_tutorial_data', GetTutorialDataHandler), ('/PostTutorial', PostTutorial), ('/AddTutorialStepPage', AddTutorialStepRenderer), ('/PostTutorialStep', PostTutorialStep), ('/get_tutorial_step_data', GetTutorialStepDataHandler),

        # Public Profile
        ('/publicProfile', PublicProfileHandler),

        # AI2 Chapter
        ('/PaintPot2', PaintPot2Handler), ('/MoleMash2', MoleMash2Handler), ('/HelloPurr2', HelloPurr2Handler), ('/NoTexting2', NoTexting2Handler), ('/PresidentsQuiz2', PresidentsQuiz2Handler), ('/MapTour2', MapTour2Handler), ('/AndroidCar2', AndroidCar2Handler), ('/BroadcastHub2', BroadcastHub2Handler), ('/Architecture2', Architecture2Handler), ('/Engineering2', Engineering2Handler), ('/Variables2', Variables2Handler), ('/Creation2', Creation2Handler), ('/Conditionals2', Conditionals2Handler), ('/Lists2', Lists2Handler), ('/Iteration2', Iteration2Handler), ('/Procedures2', Procedures2Handler), ('/Databases2', Databases2Handler), ('/Sensors2', Sensors2Handler), ('/API242', API242Handler), ('/Xylophone2', XYLoPhone2Handler), ('/Ladybug2', Ladybug2Handler),
        ('/starterApps', StarterAppsHandler), ('/robots', RobotsHandler), ('/amazonChapter', AmazonHandler),
        ('/biblio', BiblioHandler),

        
        # Page that contains all the quizzes
        ('/Quizzes', QuizzesHandler),
        # HTML bookChapters
        ('/Chapter1', Chapter1Handler), ('/Chapter2', Chapter2Handler), ('/Chapter3', Chapter3Handler), ('/Chapter4', Chapter4Handler), ('/Chapter5', Chapter5Handler), ('/Chapter6', Chapter6Handler), ('/Chapter7', Chapter7Handler), ('/Chapter8', Chapter8Handler), ('/Chapter9', Chapter9Handler), ('/Chapter10', Chapter10Handler), ('/Chapter11', Chapter11Handler), ('/Chapter12', Chapter12Handler), ('/Chapter13', Chapter13Handler), ('/Chapter14', Chapter14Handler), ('/Chapter15', Chapter15Handler), ('/Chapter16', Chapter16Handler), ('/Chapter17', Chapter17Handler), ('/Chapter18', Chapter18Handler), ('/Chapter19', Chapter19Handler), ('/Chapter20', Chapter20Handler), ('/Chapter21', Chapter21Handler), ('/Chapter22', Chapter22Handler), ('/Chapter23', Chapter23Handler), ('/Chapter24', Chapter24Handler),
        # Test page for learning djang
        ('/Django', TestTemplateHandler), ('/Django1', TestTemplateHandler),

        # Cayla's Pages
        ('/screens', ScreenHandler), ('/HelloPurrMini', HelloPurrMiniHandler), ('/aiSetUp', AppInventorSetUpHandler), ('/NewIHaveADream', NewIHaveADreamHandler), ('/preface', PrefaceHandler), ('/conceptualizePaintPot', ConceptualizePaintPotHandler), ('/conceptualizeMoleMash', ConceptualizeMoleMashHandler), ('/animationChallenge', AnimationChallengeHandler), ('/creativeProject2Game', CreativeProject2GameHandler), ('/googleVoice', GoogleVoiceHandler), ('/conceptualizeNoTexting', ConceptualizeNoTextingHandler), ('/conceptualizeLocation', ConceptualizeLocationHandler), ('/conceptualizeStockMarket', ConceptualizeStockMarketHandler), ('/pretest', PretestHandler), ('/listiteration', ListIterationHandler), ('/conceptualizeSlideshow', ConceptualizeSlideshowHandler), ('/conceptualizeProcedures', ConceptualizeProceduresHandler), ('/conceptualizeIteration', ConceptualizeIterationHandler), ('/conceptualizeNoteTaker', ConceptualizeNoteTakerHandler), ('/conceptualizeCommunication', ConceptualizeCommunicationHandler), ('/pizzaParty', PizzaPartyHandler),

    
        ##################
        # Jordan's Pages #
        ##################
                
        # new home page
        ('/', Homehandler),
        
        # courses page 
        ('/content', TutorialsHandler),
        
        # modules page
        webapp.Route(r'/content/<course_ID>', ModulesHandler),
        
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
        
        
        # TODO: delete this when no longer needed
        ('/testView', testView),
        
        ########################
        #  END Jordan's Pages  #
        ########################
        
        ###############################
        #  Iframe google docs hotfix  #
        ###############################
        ('/gDoc', gDocHandler),        
        ###################################
        #  End Iframe google docs hotfix  #
        ###################################
        
    ],
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()



