# AMAZON SPECIFIC FUNCTIONS
# books is a list from amazon, we will return another list where each entry is a list of the fields of a book
from pyaws import ecs
class foo:
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
	smallBook.append(amount)
	smallBook.append(books[i].ASIN.encode('utf-8'))
        amazon_books.append(smallBook)
    	i=i+1
    return amazon_books

  def searchAmazon(self,keywords):
    ecs.setLicenseKey('11GY40BZY8FWYGMMVKG2')
    ecs.setSecretKey('4BKnT84c3U8EfpgVbTlj4+siFIQo3+TQURTHXhFx')
    ecs.setLocale('us') 
    
    books = ecs.ItemSearch(keywords, SearchIndex='Books', ResponseGroup='Medium',AssociateTag='appinventoror-22')
    amazon_books=self.buildResultList(books)
    return amazon_books
    
  def amazonByISBN(self,isbn):
    ecs.setLicenseKey('11GY40BZY8FWYGMMVKG2')
    ecs.setSecretKey('4BKnT84c3U8EfpgVbTlj4+siFIQo3+TQURTHXhFx')
    ecs.setLocale('us') 
    
    books = ecs.ItemLookup(isbn, IdType='ISBN', SearchIndex='Books', ResponseGroup='Medium')
    amazon_books=self.buildResultList(books)
    return amazon_books

f = foo()
f.searchAmazon("baseball")