#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
import os
import logging
import jinja2
import webapp2
import json
import urllib2
from google.appengine.api import taskqueue
from google.appengine.ext import db
from random import randrange
import datetime
import csv
import StringIO
import json
from google.appengine.ext import db


JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),extensions=['jinja2.ext.autoescape'],autoescape=True)

class AirReport(): pass
class HoodReport(): pass

class JsonProperty(db.TextProperty):
	def validate(self, value):
		return value

	def get_value_for_datastore(self, model_instance):
		result = super(JsonProperty, self).get_value_for_datastore(model_instance)
		#result = json.dumps(result)
		result = json.dumps(result, default=lambda o: o.__dict__)
		return db.Text(result)

	def make_value_from_datastore(self, value):
		try:
			value = json.loads(str(value))
		except:
			pass

		return super(JsonProperty, self).make_value_from_datastore(value)

class Report(db.Model):
	name = db.StringProperty()
	report = JsonProperty()


class ZoneDetailPersist(db.Model):
    """Models an individual Record entry with content and date."""
    timestamp = db.DateTimeProperty()
    title = db.StringProperty()
    subtitle = db.StringProperty()
    max24Hr = db.FloatProperty()
    min24Hr = db.FloatProperty()
    co = db.FloatProperty()
    no2 = db.FloatProperty()
    index = db.FloatProperty()
    #id = db.FloatProperty()


class Records(db.Model):
    """Models an individual Record entry with content and date."""
    timestamp = db.DateTimeProperty()
    pm10 = db.FloatProperty()
    co = db.FloatProperty()
    no2 = db.FloatProperty()
    index = db.IntegerProperty()
    indexLabel = db.StringProperty()
    position = db.GeoPtProperty()
    positionLabels = db.StringProperty()
    sourceId = db.StringProperty()

class Goteborg(webapp2.RequestHandler):
    def get(self):
		#logging.info("OK")
		url = "http://data.goteborg.se/AirQualityService/v1.0/LatestMeasurement/4abad3dd-5d24-4c9c-9d17-79a946abe6c2?format=json"
		response = urllib2.urlopen(url);
		data = json.loads(response.read())
		pm10 = data['AirQuality']['PM10']['Value']
		no2 = data['AirQuality']['NOx']['Value']
		co = data['AirQuality']['CO']['Value']
		postdata = {
			'sourceId':'GBG1',
			'no2':str(no2),
			'pm10':str(pm10),
			'co':str(co),
			'position':'57.708870,11.974560',
		}
		req = urllib2.Request('https://bamboo-zone-547.appspot.com/_ah/api/airup/v1/queueIt')
		#req = urllib2.Request('http://localhost:8888/_ah/api/airup/v1/queueIt')
		req.add_header('Content-Type', 'application/json')
		response = urllib2.urlopen(req, json.dumps(postdata))
		self.response.write("OK")

class Umea(webapp2.RequestHandler):
    def get(self):
		#logging.info("OK")
		url = "http://ckan.openumea.se/api/action/datastore_search?resource_id=27fb8bcc-23cb-4e85-b5b4-fde68a8ef93a&limit=1&sort=M%C3%A4ttidpunkt%20desc"
		response = urllib2.urlopen(url);
		data = json.loads(response.read())
		print data['result']['records'][0]['PM10']
		pm10 = data['result']['records'][0]['PM10']
		no2 = data['result']['records'][0]['NO2']
		co = 0
		postdata = {
			'sourceId':'UMEA1',
			'no2':str(no2),
			'pm10':str(pm10),
			'co':str(co),
			'position':'63.827743,20.256825',
		}
		req = urllib2.Request('https://bamboo-zone-547.appspot.com/_ah/api/airup/v1/queueIt')
		#req = urllib2.Request('http://localhost:8888/_ah/api/airup/v1/queueIt')
		req.add_header('Content-Type', 'application/json')
		response = urllib2.urlopen(req, json.dumps(postdata))
		self.response.write("OK")

class Sthlm(webapp2.RequestHandler):
	def get(self):
		url = "http://slb.nu/cgi-bin/airweb.gifgraphic.cgi?format=txt&zmacro=lvf/air/timdatabas//lvf-kvavedioxd_flera.ic&from=130507&to=130508&path=/usr/airviro/data/sthlm/&lang=swe&rsrc=Halter.4.MainPage&st=lvf&regionPath="
		response = urllib2.urlopen(url);
		cr = csv.reader(response)
		for row in cr:
			print "z".join(row)
			#for col in row:
				#if col[:1] <> "#":
					#print col


class RegisterRecord(webapp2.RequestHandler):
    def post(self): # should run at most 1/s
		# Only needs timestamp, pm10, co, no2, position and sourceId as input. 
		# The rest should be calculated here.
		rec = Records(
			# timestamp=float(self.request.get('timestamp')),
			timestamp=datetime.datetime.fromtimestamp(float(self.request.get('timestamp'))),
			pm10=float(self.request.get('pm10')),
			co=float(self.request.get('co')),
			no2=float(self.request.get('no2')),
			# The index should be calculated here
			index=0,
			indexLabel='GOOD',

			# TODO: Do a lookup to google
			position=self.request.get('position'),

			positionLabels="---",
			sourceId=self.request.get('sourceId'),
		)
		rec.put()


class RegisterZone(webapp2.RequestHandler):
	def post(self): # should run at most 1/s
		r = ZoneDetailPersist(
			timestamp=datetime.datetime.fromtimestamp(float(self.request.get('timestamp'))),
			co=float(self.request.get('co')),
			no2=float(self.request.get('no2')),
			index=float(self.request.get('index')),
			max24Hr=float(self.request.get('max24Hr')),
			min24Hr=float(self.request.get('min24Hr')),
			title=self.request.get('title'),
			subtitle=self.request.get('subtitle')
		)
		r.put()

class Index(webapp2.RequestHandler):
    def get(self):
		template_values = {
			'greetings': 'zxc',
		}
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))

app = webapp2.WSGIApplication([('/worker', RegisterRecord),('/zoneWworker', RegisterZone),('/gbg1', Goteborg),('/umea1', Umea),('/sthlm', Sthlm),('/index.html', Index)], debug=True)