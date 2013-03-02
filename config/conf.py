
class Config():

	GAE_APP_ID = "your-app"							# your GAE app id as per the app.yaml

	CACHE = True									# should we memcache the pages
	MCPRE = "appengineblog"   						# some chars to make sure our memcache key is long enough for short urls like '/blog'

	APP_NAME = 'My GAE Blog'						# used in the meta title and templates
	BLOG_TITLE = "Blog"								# used in the main list of the blog
	TOKEN_NAME = 'mgb_tkn'  						# the cookie name for the session token
	URL_TOKEN_NAME = 'tkn'							# if the session token is passed on the url (esp for api)
	
	BASE_HOST=''									# defaults to the current host, local of deployed version nles set above
	BLOG = "/blog"									# what root path for the blog
	DOMAIN = "http://www.gaeblog.com"				# the proxied domain - used in oauth and the the allow origin response of any api request to allow the api to be called directly (to allow the reverse proxy to be bypassed)

	RSS_PAGE = 100									# how many articles per page
	BLOG_PAGE = 10
	IMAGES_VIEWER_COUNT = 20

	# oauth application keys
	TWITTER_KEY =  'your twitter key'
	TWITTER_SECRET = 'your twitter secret'

	FB_APP_ID = 'your facebook app id'					# fb app id as passed into the javascript call  - keep a localhost one  handy 
	

	def __init__(self):
		# self.include_live()
		self.include_test()


	def include_live(self):
		self.FB_APP_ID = 'our live id'
		BASE_HOST = 'http://your-app.appspot.com',        # appspot url - TODO must accomodate the current scheme - but this is the base for the CDN


	def include_test(self):
		self.CACHE = False								  # during dev its easier not to memcache the pages
		self.FB_APP_ID = 'our test id'
