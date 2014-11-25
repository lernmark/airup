#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Data sources:
# http://www.ehp.qld.gov.au/cgi-bin/air/xml.php?category=1&region=ALL
# http://campodenno.taslab.eu/stazioni/json?id=CMD001
import os
import ast
import logging
import jinja2
import webapp2
import json
import urllib2
from google.appengine.api import taskqueue
from google.appengine.ext import db
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from random import randrange
import datetime
import csv
import StringIO
import json
from google.appengine.ext import db
import hashlib


JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),extensions=['jinja2.ext.autoescape'],autoescape=True)


class AirReport(): pass
class HoodReport(): pass

class Report(db.Model):
    zoneKey = db.StringProperty()
    name = db.StringProperty()
    report = db.TextProperty()


class ZoneDetailPersist(db. Model):
    """Models an individual Record entry with content and date."""
    timestamp = db.DateTimeProperty()
    title = db.StringProperty()
    subtitle = db.StringProperty()
    max24Hr = db.FloatProperty()
    min24Hr = db.FloatProperty()
    co = db.FloatProperty()
    no2 = db.FloatProperty()
    index = db.FloatProperty()
    location = db.StringProperty(multiline=True)
    history = db.StringProperty(multiline=True)
    #id = db.FloatProperty()


class Records(db.Model):
    """Models an individual Record entry with content and date."""
    timestamp = db.DateTimeProperty()
    pm10 = db.FloatProperty()
    co = db.FloatProperty()
    no2 = db.FloatProperty()
    index = db.FloatProperty()
    position = db.GeoPtProperty()
    positionLabels = db.StringProperty()
    sourceId = db.StringProperty()
    zoneKey = db.StringProperty()


class Hamburg1(webapp2.RequestHandler):
	#http://hamburg.luftmessnetz.de/station/68HB/data.csv?componentgroup=pollution&componentperiod=1h&searchperiod=currentday
	def get(self):
		# Data from http://luft.hamburg.de/
		#http://hamburg.luftmessnetz.de/station/68HB/data.csv?componentgroup=pollution&componentperiod=1h&searchperiod=currentday
		url = "http://hamburg.luftmessnetz.de/station/70MB/data.csv?componentgroup=pollution&componentperiod=1h&searchperiod=currentday"
		response = urllib2.urlopen(url);
		cr = csv.reader(response)
		postdata = {}
		rlista = list(cr)[5]
		co = rlista[1]

		try:
			co = rlista[1]
			postdata['co'] = str(((float(co))*24.4500)/28.0100) #Convert mg/m3 to ppm
		except Exception, e:
			print "No co"

		try:
			no2 = rlista[3]
			postdata['no2'] = str(((float(no2)/1000.0000)*24.4500)/46.0100) #Convert mg/m3 to ppm
		except Exception, e:
			print "No no2"

		postdata['sourceId'] = 'Hamburg1'
		postdata['position'] = '53.555555,9.943407'
		
		req = urllib2.Request('https://bamboo-zone-547.appspot.com/_ah/api/airup/v1/queueIt')
		#req = urllib2.Request('http://localhost:8888/_ah/api/airup/v1/queueIt')
		req.add_header('Content-Type', 'application/json')
		response = urllib2.urlopen(req, json.dumps(postdata))

		self.response.write("<br/><code>DONE Hamburg1<code><br/>")
		
		
class Goteborg(webapp2.RequestHandler):

    def get(self):
		self.response.write("GBG start Now...")
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

		req = urllib2.Request('https://bamboo-zone-547.appspot.com/_ah/api/airup/v1/queueIt')
		#req = urllib2.Request('http://localhost:8888/_ah/api/airup/v1/queueIt')
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

		req = urllib2.Request('https://bamboo-zone-547.appspot.com/_ah/api/airup/v1/queueIt')
		#req = urllib2.Request('http://localhost:8888/_ah/api/airup/v1/queueIt')
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

    if ast.literal_eval(co) is not None:
		coIndex = index(tableCo, float(co), 10)
		f = f+1

    if ast.literal_eval(pm10) is not None:
    	pm10Index = index(tablePm10, float(pm10), 1)
    	f = f+1

    if ast.literal_eval(no2) is not None:
    	no2Index = index(tableNo2, float(no2), 1)
    	f = f+1

    if f > 0:
        return float((coIndex+pm10Index+no2Index)/f)



class cache(object):
    def __init__(self, fun):
        print "init cache"
        self.fun = fun
        self.cache = {}

    def __call__(self, *args, **kwargs):
        key  = str(args) + str(kwargs)
        #print "call cache"

        try:
            #print "return cache " + key
            return self.cache[key]
        except KeyError:
            self.cache[key] = rval = self.fun(*args, **kwargs)
            return rval
        except TypeError: # incase key isn't a valid key - don't cache
            return self.fun(*args, **kwargs)

@cache
def get_geolocation_url_src(url):
    return urllib2.urlopen(url).read()

def getGeoValue(latlng, keys, valueType):

    url="https://maps.googleapis.com/maps/api/geocode/json?language=en&key=AIzaSyA1WnmUgVJtsGuWoyHh-U8zlKRcGlSACXU&latlng=%s" % latlng
    data = json.loads(get_geolocation_url_src(url))

    def getGeoValueForAddress(res):
        for key1 in keys:
            for ac in res["address_components"]:
                if key1 in ac["types"]:
                    return ac[valueType]
        return None
    for key in keys:
        for res in data["results"]:
            if key in res["types"]:
                returnVal = getGeoValueForAddress(res)
                #print returnVal + " - key=" + key
                return returnVal
    return None

"""
Stores the actual measurement data from the different sources.
TODO:
    1. Should store the position labels.
    2. Should not have to store the indexLabel. A dictionary will be included in the ZoneMessage.
"""
class RegisterRecord(webapp2.RequestHandler):


    def post(self): # should run at most 1/s
        # print "#1. Worker is registering "
        # Only needs timestamp, pm10, co, no2, position and sourceId as input.
        # The rest should be calculated here.
        pm10=self.request.get('pm10')
        co=self.request.get('co')
        no2=self.request.get('no2')
        aqiValue=aqi({"co":co,"pm10":pm10,"no2":no2})

        if aqiValue is None:
            print "No AQI"
        else:
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

            latlng = self.request.get('position')
            #url="https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyA1WnmUgVJtsGuWoyHh-U8zlKRcGlSACXU&result_type=sublocality_level_1|sublocality_level_2|neighborhood&location_type=APPROXIMATE&latlng=%s" % latlng
            keyList = ["neighborhood","sublocality_level_2","sublocality_level_1","administrative_area_level_3","postal_code"]
            zoneTitle = getGeoValue(latlng, keyList, "long_name")
            zoneSubTitleArr = []
            zoneSubTitleArr.append(getGeoValue(latlng, ["locality","postal_town"], "long_name"))
            zoneSubTitleArr.append(getGeoValue(latlng, ["administrative_area_level_1"], "long_name"))

            #zoneSubTitle =  ", ".join(list(set(zoneSubTitleArr)))
            zoneSubTitle =  ", ".join(zoneSubTitleArr)
            country = getGeoValue(latlng, ["country"], "short_name")
            #country = data["results"][0]["address_components"][-1]["short_name"]
            zoneKeyInputString = zoneTitle + zoneSubTitle + country
            idhash= hashlib.md5(zoneKeyInputString.encode('ascii', 'ignore').decode('ascii')).hexdigest()
            #idhash= zoneKeyInputString.md5(zoneKeyInputString.encode('ascii', 'ignore').decode('ascii')).hexdigest()

            rec=Records(
                timestamp=datetime.datetime.fromtimestamp(float(self.request.get('timestamp'))),
                pm10=pm10,
                co=co,
                no2=no2,
                zoneKey=idhash,
                # The index should be calculated here
                #index=self.request.get('index'),
                index=aqiValue,
                # TODO: Do a lookup to google
                position=self.request.get('position'),
                positionLabels=zoneTitle,
                sourceId=self.request.get('sourceId'),
            )

            rec.put()

            """
            Now, generate the report...
            1. Hitta ytterligare poster i samma zone
            2. Rakna ut medeltal for index och de olika gaserna.
            3. Kolla om det finns en rapport sedan tidigare.
            4. spara historiska data
            5. Berakna min24hr och max 24hr
            """

            res = db.GqlQuery("SELECT * FROM Records WHERE zoneKey='" + idhash + "'")
            avrIndex = 0
            for r in res:
                avrIndex = avrIndex + r.index

            class Location(): pass
            location = Location()
            location.country=country.lower()
            location.language="EN"

            historyArr = []
            class HistoricDate():
                def __init__(self, dict):
                    self.__dict__ = dict

            historyArr.append(HistoricDate({'date' : '2014-11-10', 'index':11.0}))
            historyArr.append(HistoricDate({'date' : '2014-11-11', 'index':13.0}))

            class ZoneDetail():
                def to_JSON(self):
                    return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

            zd = ZoneDetail()
            zd.zoneKey=idhash
            zd.title=zoneTitle
            zd.subtitle=zoneSubTitle
            if res.count() > 0:
                zd.index=avrIndex/res.count()
            else:
                zd.index=float(r.index)
            zd.co=co
            zd.no2=no2
            zd.location=location
            zd.history=historyArr
            zd.min24Hr=1.0
            zd.max24Hr=1.0

            rec = Report(
                name=zoneSubTitle,
                key_name=idhash,
                zoneKey=idhash,
                report=zd.to_JSON()
            )

            rec.put()

            myKey = db.Key.from_path('Report', idhash)
            rec = db.get(myKey)
            rec.report = zd.to_JSON()
            rec.put()


class RegisterZone(webapp2.RequestHandler):
    def post(self):
        jsonstr = self.request.body
        r = ZoneDetailPersist(
            timestamp=datetime.datetime.fromtimestamp(float(self.request.get('timestamp'))),
            co=float(self.request.get('co')),
            no2=float(self.request.get('no2')),
            index=float(self.request.get('index')),
            max24Hr=float(self.request.get('max24Hr')),
            min24Hr=float(self.request.get('min24Hr')),
            title=self.request.get('title'),
            location=self.request.get('location'),
            history=self.request.get('history'),
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

class GenerateReport(webapp2.RequestHandler):
    def get(self):
        self.response.write("OK")

        zd = ZoneDetail(
            id=111111111111111.0,
            title="",
            subtitle="",
            index="",
            co="",
            no2="",
            min24Hr="",
            max24Hr="",
            history="",
            location=Location(country="sv",language="SE")
        )
        rec = Report(
            name="dddd",
            report="{}"
        )
        rec.put()

app = webapp2.WSGIApplication([
        ('/worker', RegisterRecord),
        ('/zoneWworker', RegisterZone),
        ('/gbg1', Goteborg),
        ('/umea1', Umea),
        ('/hamburg1', Hamburg1),
        ('/sthlm', Sthlm),
        ('/generateReport', GenerateReport),
        ('/index.html', Index)
    ], debug=True)
