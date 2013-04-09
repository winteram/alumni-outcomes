import cgi
import webapp2
import json
import jinja2
import os

from google.appengine.ext import db

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

# crawling jobs
class Template(db.Model):
	name = db.StringProperty()
	short = db.StringProperty()
	filename = db.StringProperty()
	created = db.DateTimeProperty(auto_now_add=True)

# people crawled / to be crawled
class Person():
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
class Position():
	title = db.StringProperty()
	company_name = db.StringProperty()

# Constructor for template
def template_key():
  """Constructs a Datastore key for a Template entity with default_template."""
  return db.Key.from_path('Template', 'default_template')


class MainPage(webapp2.RequestHandler):
	def get(self):
		template_values = {
			'greetings': 'hello world'
		}

		template = jinja_environment.get_template('index.html')
		self.response.out.write(template.render(template_values))

class LoadContent(webapp2.RequestHandler):
	def post(self):
		func = self.request.get('func')
		robj = {'ecode':400}
		if func == 'init':
			robj['ecode'] = 300
			robj['n_templates'] = 0
			robj['templates'] = []
			template_q = db.GqlQuery("SELECT * FROM Template WHERE ANCESTOR IS :1",template_key())
			for template in template_q:
				temp = {'name':template.name,'short':template.short}
				robj['templates'].append(temp)
				robj['n_templates'] += 1
			self.response.out.write(json.dumps(robj))




app = webapp2.WSGIApplication([('/', MainPage), ('/extras', LoadContent)], debug=True)