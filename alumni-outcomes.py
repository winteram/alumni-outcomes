
import os
import re
import cgi
import webapp2
import jinja2
import json
#import oauth2 as oauth
#import oauth
import urllib
import urlparse
import httplib2
import logging
import short2long

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.api import urlfetch
from google.appengine.ext.webapp import util

from gaesessions import get_current_session

jinja_environment = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

## Credentials for interacting with LinkedIn
API_KEY = "e3m3hhk13i99"
API_SECRET = "i1vChLn1sxp5hjcP"
OAUTH_USER = "9597d89b-c2e1-46fe-b9fd-00fde4896c6a"
OAUTH_SECRET = "ef7c0dd9-55b3-4fd7-853c-89f6e65ca3b3"
RANDSTRING = "thisWASaRANDOMstring1234inaway"


## DEFINE DATASTORE TABLES & FIELDS
# holding onto user credentials
class User(db.Model):
	userid = db.StringProperty()
	uname = db.StringProperty()
	utoken = db.StringProperty()
	usecret = db.StringProperty()

# crawling jobs
class Template(db.Model):
	name = db.StringProperty()
	short = db.StringProperty()
	school = db.StringProperty()
	N = db.IntegerProperty()
	N_loaded = db.IntegerProperty()
	N_crawled = db.IntegerProperty()
	created = db.DateTimeProperty(auto_now_add=True)

# people crawled / to be crawled
class Person(db.Model):
	first_name = db.StringProperty()
	last_name = db.StringProperty()
	is_crawled = db.BooleanProperty()
	n_results = db.IntegerProperty()
	crawled_first_name = db.StringProperty()
	crawled_last_name = db.StringProperty()
	industry = db.StringProperty()
	location = db.StringProperty()
	country = db.StringProperty()

# job positions people may hold
class Position(db.Model):
	title = db.StringProperty()
	company_name = db.StringProperty()


# Helper function for interacting with datastore: Constructor for template key
def template_key():
  """Constructs a Datastore key for a Template entity with default_template."""
  return db.Key.from_path('Template', 'default_template')

def api_fetch(token,resource="/v1/~",params={},method="GET",):
	h = httplib2.Http()
	params.update({'oauth2_access_token':token,'format':'json'})
	url = 'https://api.linkedin.com' + resource + '?' + urllib.urlencode(params)
	resp, content = h.request(url, method)
	if resp['status'] != '200':
		if resp['status'] == '403':
			err = "Throttled"
			return {'error':err}
		else:
			err = "Invalid response %s, %s" % (resp['status'],resp['reason'])
			return {'error':err}
	logging.info(content)
	try:
		response = json.loads(content)
	except:
		err = "Bad JSON: %s" % content
		return {'error':err}
	else:
		return response

### Functions for handling web requests
# This function handles all requests to '/'; this is user's starting point.
class MainPage(webapp2.RequestHandler):
	def get(self):
		session = get_current_session()

		# Default values for jinja template in "index.html"
		fileloaded = 'false'
		is_crawled = 'false'
		newchecked = 'checked="checked"'
		oldchecked = ''
		newhidden = ''
		oldhidden = 'style="display:none"'
		newdisable = ''
		olddisable = ''
		begindisabled = ''
		loadedtemplate = ''

		if session.has_key('template'):
			loadedtemplate = session['template']

		# if there was an error in loading the template
		ecode = self.request.get('ecode')
		if ecode == '400':
			errormsg = '<p>Input job name exists, please select another.</p>'
		elif ecode == '401':
			errormsg = '<p>Problem loading input file. Each line should be "last name, first name".</p>'
		elif ecode == '402':
			errormsg = '<p>Problem parsing input file. (session variable)</p>'
		else:
			errormsg = ''

		# if file has been loaded
		loadfile = self.request.get('loadfile')
		if loadfile:
			newchecked = ''
			oldchecked = 'checked="checked"'
			newhidden = 'style="display:none"'
			oldhidden = ''			
			newdisable = 'disabled="disabled"'		# only show currently loading template
			fileloaded = 'true'						# input to alumni.js:initAlumni, fileloaded=true
			begindisabled = 'disabled="disabled"'	# disable "begin" button (which would start crawling) as file has to be parsed first

		# if file has been parsed
		parsefile = self.request.get('parsefile')
		if parsefile:
			newchecked = ''
			oldchecked = 'checked="checked"'
			newhidden = 'style="display:none"'
			oldhidden = ''							# show templates available to crawl

		# if returning from OAuth
		crawled = self.request.get('crawled')
		if crawled:
			if crawled=='True':
				newchecked = ''
				oldchecked = 'checked="checked"'
				newhidden = 'style="display:none"'
				oldhidden = ''			
				newdisable = 'disabled="disabled"'		# only show currently loading template
				is_crawled = 'true'						# input to alumni.js:initAlumni, crawled=true (doing this through AJAX for progress bar)
				begindisabled = 'disabled="disabled"'	# disable "begin" button (which would restart crawling) as file is being crawled
			else:
				errormsg = '<p>Problem with authentication</p>'

		# if receiving ~~mystery delete query~~
		clearall = self.request.get('obliterate')
		if clearall:
			template_q = Template.all()
			for template in template_q.run():
				template.delete()

			person_q = Person.all()
			for person in person_q.run():
				person.delete()

			position_q = Position.all()
			for position in position_q.run():
				position.delete()

			return self.redirect('/')

		# get list of templates to put in options for crawling / displaying
		templates = []
		template_q = db.GqlQuery("SELECT * FROM Template WHERE ANCESTOR IS :1",template_key())
		for template in template_q:
			temp = {'name':template.name,'short':template.short,'N':template.N}
			templates.append(temp)

		# Disable "load templates" if no templates to load
		if len(templates) == 0: olddisable = 'disabled="disabled"'
		# dictionary of values to populate jinja template (index.html)
		template_values = {
			'errormsg': errormsg,
			'newchecked': newchecked,
			'oldchecked': oldchecked,
			'newhidden': newhidden,
			'oldhidden': oldhidden,
			'fileloaded': fileloaded,
			'begindisabled': begindisabled,
			'crawled': is_crawled,
			'newdisable': newdisable,
			'olddisable': olddisable,
			'templates': templates,
			'loadedtemplate': loadedtemplate
		}

		template = jinja_environment.get_template('index.html')
		return self.response.out.write(template.render(template_values))

class LoadContent(webapp2.RequestHandler):
	def post(self):
		session = get_current_session()

		func = self.request.get('func')
		# Parse the input for a new template, check for errors, pull the content of the file to be parsed, and return to MainPage with "loadfile"=True
		if func == 'loadfile':
			# check template name doesn't already exist.
			template_name = self.request.get('template-name')
			template_q = db.GqlQuery("SELECT * FROM Template WHERE name=:1",template_name)
			exists = template_q.get()
			if exists:
				return self.redirect('/?ecode=400')

			# if it doesn't exist, put in session variable
			session['template'] = template_name

			# create a new template in the datastore
			template = Template(parent=template_key())
			template.name = template_name
			# URLencode template name, so (for example) spaces become %20
			template.short = urllib.quote_plus(template.name)
			template.school = self.request.get('school-name')

			# Split input file by lines
			person_file = re.split('[\r\n]',self.request.get('template-file'))
			alums = [ line.strip() for line in person_file ]
			logging.info(len(alums))
			# If there is zero or one lines in the resulting parsed list, there is a problem with the input file
			if len(alums) < 2:
				return self.redirect('/?ecode=401')
			#logging.info(new_alums)
			# put list into session variable to be parsed in "parsefile function"
			session['person_file'] = alums
			# put info about input file into template in datastore
			template.N = len(alums)
			template.N_loaded = 0
			template.N_crawled = 0
			# save changes to template in datastore
			template.put()
			logging.info("New template: " + template.name)
			# return to MainPage with loadfile=True
			return self.redirect('/?loadfile=True')

		if func == 'parsefile':
			# Default values (would restart if it all went wrong)
			response = {'offset':0,'complete':'false'}
			# get template
			template_name = session['template']
			template_q = db.GqlQuery("SELECT * FROM Template WHERE name=:1",template_name)
			template = template_q.get()
			if template:
				# make sure session variable has input file, otherwise send back to main with error
				if not session.has_key('person_file'):
					return self.redirect('/?ecode=402')
				# get list of alums from session variable
				alums = session['person_file']
				#logging.info("number of lines: " + str(len(alums)))
				#logging.info(alums)
				response['N'] = len(alums)

				# See if any loaded so far, and start from there.  Otherwise,
				# get starting point and chunk size from alumni.js:parseFile
				offset = int(self.request.get('offset'))
				limit = int(self.request.get('limit'))
				response['offset'] = offset + limit

				# If end of chunk is past # of people to parse, set complete to true
				if response['offset'] > len(alums):
					response['offset'] = len(alums)
					response['complete'] = 'true'

				logging.info('Parsing lines ' + str(offset) + ' to ' + str(response['offset']))
				for line in alums[offset:response['offset']]:
					alum_input = line.split(',')
					if len(alum_input) < 2 or len(alum_input) > 3:
						logging.error("Bad length")
						continue

					lname_group = re.search('[A-Za-z]+',alum_input[0])
					fname_group = re.search('[A-Z][a-z]+',alum_input[1])

					# Create a new Person entry in the datastore with loaded template as parent
					alum = Person(parent=template)
					alum.first_name = fname_group.group(0)
					alum.last_name = lname_group.group(0)
					alum.is_crawled = False
					logging.debug("New alum: " + alum.last_name)

					# Save changes to person in datastore
					alum.put()
					# increment the number of alumni loaded into datastore
					template.N_loaded += 1
				# save changes to template (number loaded)
				template.put()
				self.response.out.write(json.dumps(response))
			else:
				logging.error("Template not found")

			
# Send user to LinkedIn to authenticate
class InitOAuth(webapp2.RequestHandler):
	def post(self):
		session = get_current_session()
		# set session variable to template to be crawled
		session['template'] = self.request.get('template-to-load')

		request_token_url = "https://www.linkedin.com/uas/oauth2/authorization?response_type=code&client_id=" + API_KEY 
		request_token_url += "&scope=r_basicprofile%20r_network"
		request_token_url += "&state=" + RANDSTRING
		request_token_url += '&redirect_uri=' 
		request_token_url += "%s/oauth" % self.request.host_url
		
		self.redirect(request_token_url)

class HandleOAuth(webapp2.RequestHandler):
	def get(self):
		session = get_current_session()
		# verify token
		#if self.request.get('access_token'):
		if self.request.get('code'):
			if self.request.get('state') == RANDSTRING:
				auth_url = "https://www.linkedin.com/uas/oauth2/accessToken?grant_type=authorization_code"
				auth_url += "&code=" + self.request.get('code')
				auth_url += "&redirect_uri=" 
				auth_url += "%s/oauth" % self.request.host_url
				auth_url += "&client_id=" + API_KEY
				auth_url += "&client_secret=" + API_SECRET

				h = httplib2.Http()
				resp, content = h.request(auth_url, "POST")
				if resp['status'] != '200':
					logging.error("Invalid response %s." % resp['status'])
					self.redirect('/?crawled=error')
				logging.info(content)
				try:
					access_obj = json.loads(content)
				except:
					logging.error("Invalid response %s." % content)
					self.redirect('/?crawled=error')

				access_token = access_obj["access_token"]
				user_info = api_fetch(access_token,"/v1/people/~:(id,first-name,last-name)")
				if user_info.has_key('error'):
					logging.error(user_info)
					self.redirect('/?crawled=error')

				logging.info(user_info)
				session['uid'] = user_info['id']

				# put user in db (with their authentication information to make requests)
				user_key = db.Key.from_path('User', session['uid'])
				user = User(parent=user_key)
				user.userid = user_info['id']
				user.uname = user_info['firstName'] + " " + user_info['lastName']
				user.utoken = access_token
				# TODO: could put expiration date for token into user, do check for renewal
				#user.utoken = user_info['token']
				#user.usecret = user_info['secret']
				user.put()

				#self.response.out.write(user_info)
				# Send user to MainPage with crawled=True, to start crawling in chunks with alumni.js:doCrawl
				self.redirect('/?crawled=True')
			else:
				self.redirect('/?crawled=error')
		else:
			self.redirect('/?crawled=error')

# do crawl
class DoCrawl(webapp2.RequestHandler):
	def post(self):
		# create default response object
		robj = {'ncrawled':0,'N':0}

		session = get_current_session()
		if not session.has_key('uid'):
			robj['error'] = 'ERR 401 Session User ID missing'
			return self.response.out.write(json.dumps(robj))

		# get school name
		if session['template']:
			template_q = db.GqlQuery("SELECT * FROM Template WHERE short=:1",session['template'])
			template = template_q.get()
			if template:
				school = template.school
				robj['N'] = template.N
				robj['ncrawled'] = template.N_crawled
			else:
				robj['error'] = "ERR 400 Template db error, DoCrawl: " + session['template']
				return self.response.out.write(json.dumps(robj))
		else:
			robj['error'] = "ERR 400 Template session error, DoCrawl"
			return self.response.out.write(json.dumps(robj))

		logging.info("Template loaded:" + template.short)

		# TODO: get ncrawled
		# robj['ncrawled'] = int(self.request.get('ncrawled')) or 0

		user_q = db.GqlQuery("SELECT * FROM User WHERE userid=:1",session['uid'])
		user = user_q.get()
		if user:
			# iterate through people in Template
			person_q = Person.all()
			person_q.filter("is_crawled !=",True)
			person_q.ancestor(template)
			npeople = int(self.request.get('limit')) or 10
			for person in person_q.run(limit=npeople):
			#for person in person_q.run(limit=1):
				params = {'first-name':person.first_name,'last-name':person.last_name,'school-name':school,'format':'json'}
				#params = {'first-name':'stephen','last-name':'denton','format':'json'}
				logging.info("Alum loaded: " + person.last_name)
				request_url = "/v1/people-search"
				request_url += ":(people:(id,first-name,last-name,industry,location,positions:(title,company)),num-results)"
				li_person = api_fetch(user.utoken,request_url,params)
				if li_person.has_key('error'):
					if li_person['error'] == 'Throttled':
						robj['throttled'] = 'true'
						return self.response.out.write(json.dumps(robj))
					else:
						robj['error'] = "ERR 401, bad response: " + li_person['error']
						return self.response.out.write(json.dumps(robj))
				else:
					person.n_results = li_person['people']['_total']
					if person.n_results == 1:
						alum = li_person['people']['values'][0]
						person.crawled_first_name = 'firstName' in alum and alum['firstName'] or fname
						person.crawled_last_name = 'lastName' in alum and alum['lastName'] or lname
						logging.info(person.crawled_first_name + " " + person.crawled_last_name)
						if 'location' in alum:
							person.location = 'name' in alum['location'] and alum['location']['name'] or 'NA'
							if 'country' in alum['location']:
								person.country = 'code' in alum['location']['country'] and alum['location']['country']['code'] or 'NA'
						else:
							person.location = 'NA'
							person.country = 'NA'
						person.industry = 'industry' in alum and alum['industry'] or 'NA'
						if 'positions' in alum:
							for i in range(0,alum['positions']['_total']):
								position = Position(parent=person)
								position.title = 'title' in alum['positions']['values'][i] and alum['positions']['values'][i]['title'] or 'NA'
								position.company_name = 'name' in alum['positions']['values'][i]['company'] and alum['positions']['values'][i]['company']['name'] or 'NA'
								position.put()
					person.is_crawled = True
					person.put()    
					robj['ncrawled'] += 1
					template.N_crawled += 1
					template.put()

		else:
			robj['error'] = "ERR 402 No user!"
			return self.response.out.write(json.dumps(robj))

		# no errors, return response object (robj)
		return self.response.out.write(json.dumps(robj))
		
# get data for visualizations
class DoViz(webapp2.RequestHandler):
	def post(self):
		robj = {}
		session = get_current_session()

		# get template
		if session['template']:
			template_q = db.GqlQuery("SELECT * FROM Template WHERE short=:1",session['template'])
			template = template_q.get()
			if not template:
				robj['error'] = "ERR 400 Template db error, DoCrawl: " + session['template']
				return self.response.out.write(json.dumps(robj))
		else:
			robj['error'] = "ERR 400 Template session error, DoCrawl"
			return self.response.out.write(json.dumps(robj))

		logging.info("Template loaded for viz:" + template.short)

		viz = self.request.get('viz')
		if viz == 'pctmatch':
			ncrawled = 0
			nmatch = 0
			# iterate through crawled people in Template
			person_q = Person.all()
			person_q.filter("is_crawled =",True)
			person_q.ancestor(template)
			for person in person_q.run():
				ncrawled += 1
				if person.n_results == 1:
					nmatch += 1
			if ncrawled > 0:
				robj['pctmatch'] = round(100*nmatch/ncrawled,2)
			else:
				robj['pctmatch'] = 0
				logging.error('ncrawled = 0')
			return self.response.out.write(json.dumps(robj))

		if viz == 'piecountry':
			countries = {}
			total = 0
			# iterate through crawled people in Template
			person_q = Person.all()
			person_q.filter("is_crawled =",True)
			person_q.ancestor(template)
			for person in person_q.run():
				if person.n_results == 1 and person.country != "NA" :
					total += 1
					if person.country in countries:
						countries[person.country] += 1
					else:
						countries[person.country] = 1
			clist = [{'country':short2long.getCountryName(c),'freq':v} for c,v in countries.iteritems()]
			clist.sort(key=lambda tup: tup['freq'],reverse=True) 
			robj = {'clist':clist,'pdata': [{'country':'US','freq':countries['us']},{'country':'Other','freq':total-countries['us']}]}
			return self.response.out.write(json.dumps(robj))

		if viz == 'histregion':
			regions = {}
			total = 0
			# iterate through crawled people in Template
			person_q = Person.all()
			person_q.filter("is_crawled =",True)
			person_q.ancestor(template)
			for person in person_q.run():
				if person.n_results == 1 and person.location != "NA" :
					total += 1
					if person.location in regions:
						regions[person.location] += 1
					else:
						regions[person.location] = 1
			rlist = [{'region':r,'freq':round(float(v)/float(total),4)} for r,v in regions.iteritems()]
			rlist.sort(key=lambda tup: tup['freq'],reverse=True) 
			logging.debug(rlist)
			return self.response.out.write(json.dumps(rlist))

		if viz == 'histindustry':
			industries = {}
			total = 0
			# iterate through crawled people in Template
			person_q = Person.all()
			person_q.filter("is_crawled =",True)
			person_q.ancestor(template)
			for person in person_q.run():
				if person.n_results == 1 and person.industry != "NA" :
					total += 1
					if person.industry in industries:
						industries[person.industry] += 1
					else:
						industries[person.industry] = 1
			ilist = [{'industry':r,'freq':round(float(v)/float(total),4)} for r,v in industries.iteritems()]
			ilist.sort(key=lambda tup: tup['freq'],reverse=True) 
			logging.debug(ilist)
			return self.response.out.write(json.dumps(ilist))

		if viz == 'titlecloud':
			titles = {}
			total = 0
			# iterate through positions
			position_q = Position.all()
			for position in position_q.run():
				for word in position.title.split(' '):
					if word.strip() in titles:
						titles[word.strip()] += 1
					else:
						titles[word.strip()] = 1
			tlist = [{'text':t,'size':v} for t,v in titles.iteritems()]
			tlist.sort(key=lambda tup: tup['size'],reverse=True) 
			logging.debug(tlist)
			return self.response.out.write(json.dumps(tlist))

app = webapp2.WSGIApplication([('/', MainPage), 
	('/loadcontent', LoadContent), 
	('/initoauth', InitOAuth),  
	('/oauth', HandleOAuth), 
	('/crawl', DoCrawl),
	('/viz', DoViz)], 
	debug=True)






