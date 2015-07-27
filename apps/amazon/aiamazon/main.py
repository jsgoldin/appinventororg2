#!/usr/bin/env python
###
### This web service is used in conjunction with App
### Inventor for Android (see
### <http://appinventor.org). This service calls Amazon API

### Author: Dave Wolber via template of Hal Abelson

import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.db import Key
from django.utils import simplejson as json

# DWW
import os
from google.appengine.ext.webapp import template
import urllib

# dww
from pyaws import ecs


class GetValueHandler(webapp.RequestHandler):

  def get_value(self, tag):

    # You can do any type of computing here, just set the variable value
    # before the calls to WriteToWeb/WriteToPhone

    # check if tag has isbn: prefix, and search by ISBN if so 
    if tag.startswith("isbn:"):
       splitTag=tag.split(":")
       if len(splitTag)>1:
           valueList=self.amazonByISBN(splitTag[1])
       else:
	   valueList=self.searchAmazon(tag)
    else:
       valueList = self.searchAmazon(tag)

    value=valueList
  
    if self.request.get('fmt') == "html":
    	WriteToWeb(self,tag,value )
    else:
	WriteToPhone(self,tag,value)

  def post(self):
    tag = self.request.get('tag')
    self.get_value(tag)

  # there is a web ui for this as well, here is the get
  def get(self):
    # this did pump out the form
    template_values={}
    path = os.path.join(os.path.dirname(__file__),'index.html')
    self.response.out.write(template.render(path,template_values))

# AMAZON SPECIFIC FUNCTIONS
# books is a list from amazon, we will return another list where each entry is a list of the fields of a book
  def buildResultList(self,books):
    i=0
    amazon_books=[]
   
    limit = 5
    if len(books)<5:
	limit=len(books)
    while i<limit:
    	smallBook=[]
	amount="0"
	
	
	#if books[i].OfferSummary:
		#if books[i].OfferSummary.LowestNewPrice:
			
	try:
		amount=books[i].OfferSummary.LowestNewPrice.FormattedPrice
	except:
		amount=0.0
					
	title =  "\""+books[i].Title+"\""
	smallBook.append(title.encode('utf-8'))
	# smallBook.append(amount.encode('utf-8'))
	smallBook.append(str(amount))
	smallBook.append(books[i].ASIN.encode('utf-8'))
        amazon_books.append(smallBook)
    	i=i+1
    return amazon_books

  def searchAmazon(self,keywords):
    ecs.setLicenseKey('11GY40BZY8FWYGMMVKG2')
    ecs.setSecretKey('4BKnT84c3U8EfpgVbTlj4+siFIQo3+TQURTHXhFx')
    ecs.setLocale('us') 
    
    books = ecs.ItemSearch(keywords, SearchIndex='Books', ResponseGroup='Medium',AssociateTag='appinventoror-20')
    amazon_books=self.buildResultList(books)
    return amazon_books
    
  def amazonByISBN(self,isbn):
    ecs.setLicenseKey('11GY40BZY8FWYGMMVKG2')
    ecs.setSecretKey('4BKnT84c3U8EfpgVbTlj4+siFIQo3+TQURTHXhFx')
    ecs.setLocale('us') 
    
    books = ecs.ItemLookup(isbn, IdType='ISBN',  SearchIndex='Books', ResponseGroup='Medium', AssociateTag='appinventoror-20')
    amazon_books=self.buildResultList(books)
    return amazon_books



class MainPage(webapp.RequestHandler):

  def get(self):
    template_values = {}
    # render the page using the template engine
    path = os.path.join(os.path.dirname(__file__),'index.html')
    self.response.out.write(template.render(path,template_values))


#### Utilty procedures for generating the output

def WriteToPhone(handler,tag,value):
 
    handler.response.headers['Content-Type'] = 'application/jsonrequest'
    json.dump(["VALUE", tag, value], handler.response.out)

def WriteToWeb(handler, tag,value):
    template_values={"result":  value}  
    path = os.path.join(os.path.dirname(__file__),'index.html')
    handler.response.out.write(template.render(path,template_values))
  

### Assign the classes to the URL's

application =     \
   webapp.WSGIApplication([('/', MainPage),
                           ('/getvalue', GetValueHandler)
                           ],
                          debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()


