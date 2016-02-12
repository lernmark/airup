#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
import os
import logging
import jinja2
import webapp2
import json
from google.appengine.api import taskqueue
from google.appengine.ext import db
from random import randrange
from datetime import datetime

JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),extensions=['jinja2.ext.autoescape'],autoescape=True)

class Records(db.Model):
    """Models an individual Record entry with content and date."""
    timestamp = db.StringProperty()
    pm10 = db.IntegerProperty()
    pm25 = db.IntegerProperty()
    O3 = db.IntegerProperty()
    co = db.IntegerProperty()
    no2 = db.IntegerProperty()
    index = db.IntegerProperty()
    indexLabel = db.StringProperty()
    position = db.GeoPtProperty()
    positionLabels = db.StringProperty()
    sourceId = db.StringProperty()

# http://data.goteborg.se/AirQualityService/v1.0/LatestMeasurement/4abad3dd-5d24-4c9c-9d17-79a946abe6c2?format=json
# data = {'ids': [12, 3, 4, 5, 6]}
# req = urllib2.Request('http://abc.com/api/posts/create')
# req.add_header('Content-Type', 'application/json')
# response = urllib2.urlopen(req, json.dumps(data))

class MainPage(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		self.response.write('Hello, World!')

app = webapp2.WSGIApplication([('/g', MainPage)], debug=True)
