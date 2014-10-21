#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
import os
import ast
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
    index = db.FloatProperty()
    indexLabel = db.StringProperty()
    position = db.GeoPtProperty()
    positionLabels = db.StringProperty()
    sourceId = db.StringProperty()

class Goteborg(webapp2.RequestHandler):

    def get(self):
		self.response.write("OK GBG start")
		url = "http://data.goteborg.se/AirQualityService/v1.0/LatestMeasurement/4abad3dd-5d24-4c9c-9d17-79a946abe6c2?format=json"
		response = urllib2.urlopen(url);
		data = json.loads(response.read())
		postdata = {}
		try:
			pm10 = data['AirQuality']['PM10']['Value']
			postdata['pm10'] = str(pm10)
		except Exception, e:
			print "no pm10"
			#postdata['pm10'] = 0

		try:
			no2 = data['AirQuality']['NO2']['Value']
			postdata['no2'] = str(((no2/1000.0000)*24.4500)/46.0100) #Convert mg/m3 to ppm
		except Exception, e:
			print "No no2"
			#postdata['no2'] = 0		

		try:
			co = data['AirQuality']['CO']['Value']
			postdata['co'] = str(((co/1000.0000)*24.4500)/28.0100) #Convert mg/m3 to ppm
		except Exception, e:
			print "No co"
			#postdata['co'] = 0
		
		postdata['sourceId'] = 'GBG1'
		postdata['position'] = '57.708870,11.974560'
		
		self.response.write(postdata)

		#req = urllib2.Request('https://bamboo-zone-547.appspot.com/_ah/api/airup/v1/queueIt')
		req = urllib2.Request('http://localhost:8888/_ah/api/airup/v1/queueIt')
		req.add_header('Content-Type', 'application/json')
		response = urllib2.urlopen(req, json.dumps(postdata))


class Umea(webapp2.RequestHandler):
    def get(self):
		logging.info("UMEA")
		url = "http://ckan.openumea.se/api/action/datastore_search?resource_id=27fb8bcc-23cb-4e85-b5b4-fde68a8ef93a&limit=1&sort=M%C3%A4ttidpunkt%20desc"
		response = urllib2.urlopen(url);
		data = json.loads(response.read())

		postdata = {}
		try:
			pm10 = data['result']['records'][0]['PM10']
			postdata['pm10'] = str(float(pm10))
		except Exception, e:
			pm10 = 0

		try:
			no2 = data['result']['records'][0]['NO2']
			postdata['no2'] = str(((no2/1000.0000)*24.4500)/46.0100) #Convert mg/m3 to ppm
		except Exception, e:
			no2 = 0		

		postdata['sourceId'] = 'UMEA1'
		postdata['position'] = '63.827743,20.256825'

		#req = urllib2.Request('https://bamboo-zone-547.appspot.com/_ah/api/airup/v1/queueIt')
		req = urllib2.Request('http://localhost:8888/_ah/api/airup/v1/queueIt')
		req.add_header('Content-Type', 'application/json')
		response = urllib2.urlopen(req, json.dumps(postdata))
		self.response.write(postdata)

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


tableAqiIndex = [ range(0, 50, 1),range(51, 100, 1),range(101, 150, 1),range(151, 200, 1),range(201, 300, 1),range(301, 400, 1),range(401, 500, 1) ]
tableCo = [ range(0, 44, 1),range(45, 94, 1),range(95, 124, 1),range(125, 154, 1),range(155, 304, 1),range(305, 404, 1),range(405, 504, 1) ] 
tableNo2 = [ range(0, 53, 1),range(54, 100, 1),range(101, 360, 1),range(361, 640, 1),range(650, 1240, 1),range(1250, 1640, 1),range(1650, 2040, 1) ] 
tablePm10 = [ range(0, 54, 1),range(55, 154, 1),range(155, 254, 1),range(255, 354, 1),range(355, 424, 1),range(425, 504, 1),range(505, 604, 1) ] 

def index(table, v, fac):

    row = [i for i,l in enumerate(table) if int(v*fac) in l][0]
    bpLow = float(table[row][0])/fac
    bpHigh = (float(table[row][len(table[row])-1]+1)/fac)
    iLow = tableAqiIndex[row][0]
    iHigh = tableAqiIndex[row][len(tableAqiIndex[row])-1]+1
    index = (
        (float(iHigh) - float(iLow)) / 
        (float(bpHigh) - float(bpLow))
        ) * (float(v)-(float(bpLow))) + float(iLow)
    return int(index)

def aqi(values):

    co=values["co"]
    pm10=values["pm10"]
    no2=values["no2"]

    f = 0
    coIndex = 0
    pm10Index = 0
    no2Index = 0

    try:
        coIndex = index(tableCo, float(co), 10)
        f = f+1
    except Exception, e:
    	print e

    try:
        pm10Index = index(tablePm10, float(pm10), 1)
        f = f+1
    except Exception, e:
    	print e
	
    try:
        no2Index = index(tableNo2, float(no2), 1)
        f = f+1
    except Exception, e:
    	print e
		
	
    if f > 0:
        return float((coIndex+pm10Index+no2Index)/f)


class RegisterRecord(webapp2.RequestHandler):
    def post(self): # should run at most 1/s
		# Only needs timestamp, pm10, co, no2, position and sourceId as input. 
		# The rest should be calculated here.
		pm10=self.request.get('pm10')
		co=self.request.get('co')
		no2=self.request.get('no2')

		index=aqi({"co":co,"pm10":pm10,"no2":no2})
		
		if ast.literal_eval(co) is None:
			co = None
		else:
			co = float(co)

		if ast.literal_eval(pm10) is None:
			pm10 = None
		else:
			pm10 = float(pm10)

		if ast.literal_eval(no2) is None:
			no2 = None
		else:
			no2 = float(no2)
		
		rec = Records(
			# timestamp=float(self.request.get('timestamp')),
			timestamp=datetime.datetime.fromtimestamp(float(self.request.get('timestamp'))),
			pm10=pm10,
			co=co,
			no2=no2,
			# The index should be calculated here
			#index=self.request.get('index'),
			index=index,
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