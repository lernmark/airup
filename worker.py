#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Data sources:
# http://www.ehp.qld.gov.au/cgi-bin/air/xml.php?category=1&region=ALL
# http://campodenno.taslab.eu/stazioni/json?id=CMD001
# coding=utf-8

"""
NY - 40.714224,-73.961452
SP - -23.560057,-46.634334
GBG - 57.70887,11.97456
BER - 52.536958,13.408041
HTULL -
SOFO - 59.312963,18.080363
Harajuku - 35.671628,139.710285
Wellington - -41.296435,174.776527
Sidney - -33.896549,151.179963
Kitazawa - 35.663365,139.668332
Nairobi - -1.282794,36.828232

Barrsatra - 60.620428,16.750116
New Holland/Admiralteysky District St Petersburg - 59.929506,30.289360
Data from http://luft.hamburg.de/
24FL - 53.638128,9.996872
70MB - 53.555555,9.943407
17SM - 53.560899,9.957213
68HB - 53.592354,10.053774
61WB -

EAA
http://fme.discomap.eea.europa.eu/fmedatastreaming/AirQuality/AirQualityUTDExport.fmw?FromDate=2015-03-17&ToDate=2015-03-17&Countrycode=se&InsertedSinceDate=&UpdatedSinceDate=&Pollutant=PM10,SO2,NO2,CO&Namespace=&Format=XML&UserToken=6C2D03D8-04E1-4D07-B856-D92ACE0FA832
"""
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
from xml.dom import minidom
from google.appengine.ext import db
import hashlib

GEOLOCATION_URL = "https://maps.googleapis.com/maps/api/geocode/json?language=en&key=AIzaSyA1WnmUgVJtsGuWoyHh-U8zlKRcGlSACXU&latlng=%s"
#SERVICE_URL = "http://localhost:8080"
SERVICE_URL = "https://bamboo-zone-547.appspot.com"
# http://apis-explorer.appspot.com/apis-explorer/?base=http://localhost:8080/_ah/api#p/

JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),extensions=['jinja2.ext.autoescape'],autoescape=True)


class AirReport(): pass
class HoodReport(): pass

class Report(db.Model):
    zoneKey = db.StringProperty()
    name = db.StringProperty()
    report = db.TextProperty()

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

class Eaa(webapp2.RequestHandler):


    def get(self):

        def regData(country):
            isotoday = datetime.datetime.now().date().isoformat()
            url = "http://fme.discomap.eea.europa.eu/fmedatastreaming/AirQuality/AirQualityUTDExport.fmw?FromDate=" + isotoday + "&ToDate=" + isotoday + "&Countrycode=" + country + "&InsertedSinceDate=&UpdatedSinceDate=&Pollutant=PM10&Namespace=&Format=XML&UserToken=6C2D03D8-04E1-4D07-B856-D92ACE0FA832"
            response = urllib2.urlopen(url)
            xmldoc = minidom.parse(response)
            records = xmldoc.getElementsByTagName('record')
            self.response.write("<br/><code>" + url + " - " + str(len(records)) + " <code><br/>")

            print 

            def getText(nodelist):
                rc = []
                for node in nodelist:
                    if node.nodeType == node.TEXT_NODE:
                        rc.append(node.data)
                return ''.join(rc).encode("utf-8","ignore") 

            for rec in records:
                postdata = {}
                station_code = rec.getElementsByTagName("station_code")[0]
                station_name = rec.getElementsByTagName("station_name")[0]
                pollutant = rec.getElementsByTagName("pollutant")[0]
                samplingpoint_point = rec.getElementsByTagName("samplingpoint_point")[0]
                value_numeric = rec.getElementsByTagName("value_numeric")[0]
                posx = samplingpoint_point.attributes['x'].value
                posy = samplingpoint_point.attributes['y'].value

                postdata['sourceId'] = "EAA-"+getText(station_code.childNodes)
                postdata['position'] = posy + "," + posx
                postdata[getText(pollutant.childNodes).lower()] = str(getText(value_numeric.childNodes))
                postdata['co'] = "0.3"
                postdata['no2'] = "0.4"
                self.response.write(postdata)
                req = urllib2.Request(SERVICE_URL + '/_ah/api/airup/v1/queueIt')
                req.add_header('Content-Type', 'application/json')
                response = urllib2.urlopen(req, json.dumps(postdata))            


        regData("se")
        regData("fi")
        regData("de")
        regData("fr")
        self.response.write("<br/><code>EAA DONE<code><br/>")



class Hamburg1(webapp2.RequestHandler):

    def get(self):
        print "HBG"

        def regData(url, sourceId, position):
            response = urllib2.urlopen(url)
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

            postdata['sourceId'] = sourceId
            postdata['position'] = position

            #req = urllib2.Request('https://bamboo-zone-547.appspot.com/_ah/api/airup/v1/queueIt')
            req = urllib2.Request(SERVICE_URL + '/_ah/api/airup/v1/queueIt')
            req.add_header('Content-Type', 'application/json')
            response = urllib2.urlopen(req, json.dumps(postdata))

            self.response.write("<br/><code>DONE " + sourceId + "<code><br/>")


        """
        Data from http://luft.hamburg.de/
        24FL - 53.638128,9.996872
        70MB - 53.555555,9.943407
        17SM - 53.560899,9.957213
        68HB - 53.592354,10.053774
        61WB - 53.508315,9.990633
        """

        regData("http://hamburg.luftmessnetz.de/station/70MB/data.csv?componentgroup=pollution&componentperiod=1h&searchperiod=currentday","Hamburg-70MB", "53.555555,9.943407")
        regData("http://hamburg.luftmessnetz.de/station/17SM/data.csv?componentgroup=pollution&componentperiod=1h&searchperiod=currentday","Hamburg-17SM", "53.560899,9.957213")
        regData("http://hamburg.luftmessnetz.de/station/68HB/data.csv?componentgroup=pollution&componentperiod=1h&searchperiod=currentday","Hamburg-68HB", "53.592354,10.053774")
        regData("http://hamburg.luftmessnetz.de/station/24FL/data.csv?componentgroup=pollution&componentperiod=1h&searchperiod=currentday","Hamburg-24FL", "53.638128,9.996872")
        regData("http://hamburg.luftmessnetz.de/station/61WB/data.csv?componentgroup=pollution&componentperiod=1h&searchperiod=currentday","Hamburg-61WB", "53.508315,9.990633")
		
		
class Goteborg(webapp2.RequestHandler):

    def get(self):
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

		req = urllib2.Request(SERVICE_URL + '/_ah/api/airup/v1/queueIt')
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

		req = urllib2.Request(SERVICE_URL + '/_ah/api/airup/v1/queueIt')
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
indexLables = ["Good","Moderate","Unhealthy for Sensitive Group","Unhealthy","Very Unhealthy","Hazardous","Hazardous"]


def index(table, v, fac):

    try:
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
    except Exception, e:
        print e
        return 0

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

    # TODO: Check the factor
    if ast.literal_eval(no2) is not None:
    	no2Index = index(tableNo2, float(no2), 1)
    	f = f+1

    if f > 0:
        return float((coIndex+pm10Index+no2Index)/f)



class cache(object):
    def __init__(self, fun):
        #print "init cache"
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

    url=GEOLOCATION_URL % latlng
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
                return returnVal
    return None

def getGeoFormattedAddress(latlng, keys):
    url=GEOLOCATION_URL % latlng
    data = json.loads(get_geolocation_url_src(url))

    for key in keys:
        for res in data["results"]:
            if key in res["types"]:
                return res["formatted_address"]
    return None

def getGeoPosition(latlng, keys):
    url=GEOLOCATION_URL % latlng
    data = json.loads(get_geolocation_url_src(url))

    for key in keys:
        for res in data["results"]:
            if key in res["types"]:
                return str(res["geometry"]["location"]["lat"]) + "," + str(res["geometry"]["location"]["lng"])
    return None


def getLocationContext(latlng):
    context = {}
    keyList = ["neighborhood","sublocality_level_2","sublocality_level_1","administrative_area_level_3","colloquial_area","postal_code"]
    addrString = getGeoFormattedAddress(latlng, keyList).encode("utf-8")
    hoodPosition = getGeoPosition(latlng, keyList)
    addrList = addrString.split(", ")
    zoneTitle = addrList[0].decode("utf-8","ignore")
    addrList.remove(addrList[0])
    addrList.remove(addrList[-1])
    zoneSubTitle = ", ".join(addrList).decode("utf-8")

    country = getGeoValue(latlng, ["country"], "short_name")

    context["zoneTitle"] = zoneTitle
    context["zoneSubTitle"] = zoneSubTitle
    context["country"] = country
    context["zoneKey"] = generateZoneKey(zoneTitle,zoneSubTitle,country)
    context["position"] = hoodPosition
    return context

def generateZoneKey(zoneTitle,zoneSubTitle,country):
    zoneKeyInputString = zoneTitle + zoneSubTitle + country
    zoneKey = hashlib.md5(zoneKeyInputString.encode('ascii', 'ignore').decode('ascii')).hexdigest()
    return zoneKey

def test():
    robj = {}
    robj["country"] = "Sweden"
    return robj

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

            locationContext = getLocationContext(latlng)
            zoneKey = locationContext.get('zoneKey')
            zoneTitle = locationContext.get('zoneTitle')
            zoneSubTitle = locationContext.get('zoneSubTitle')
            country = locationContext.get('country')
            position = locationContext.get('position')


            rec=Records(
                timestamp=datetime.datetime.fromtimestamp(float(self.request.get('timestamp'))),
                pm10=pm10,
                co=co,
                no2=no2,
                zoneKey=zoneKey,
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

            """ Get the data newer than 1 hour """
            #res = db.GqlQuery("SELECT * FROM Records WHERE zoneKey='" + zoneKey + "' AND timestamp >= :1", datetime.datetime.now() - datetime.timedelta(hours = 6))
            res = db.GqlQuery("SELECT * FROM Records WHERE zoneKey='" + zoneKey + "'")


            """ Create a list of all stations and history values """
            avrIndex = 0
            stationsDict = {}
            historyDict = {}
            indexArr = []
            for r in res:
                historyDate = r.timestamp.strftime('%Y-%m-%d')
                indexArr = historyDict.get(historyDate, [0.0])
                indexArr.append(r.index)
                historyDict[historyDate] = indexArr
                avrIndex = avrIndex + r.index
                stationsDict[r.sourceId] = str(r.position)

            stations = []
            for key, value in stationsDict.iteritems():
                temp = {}
                temp["sourceId"] = key
                temp["position"] = value

                stations.append(temp)

            """ Add a proper locale. For now all languages are english """
            class Location(): pass
            location = Location()
            location.country=country.upper()
            location.language="en"


            """ Create a array of history records. Each record contains the date and the index for that date.  """
            historyArr = []
            class HistoricDate():
                def __init__(self, dict):
                    self.__dict__ = dict

            for key, value in historyDict.iteritems():
                historyArr.append(HistoricDate({'date' : key, 'index':reduce(lambda x, y: x + y, value) / (len(value)-1)}))

            """ Create the zone-detail object that will be persisted as a report for use in the zones API """
            class ZoneDetail():
                def to_JSON(self):
                    return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)

            zd = ZoneDetail()
            zd.zoneKey=zoneKey
            zd.title=zoneTitle
            zd.subtitle=zoneSubTitle
            zd.stations=stations
            zd.numberOfMeasurements=str(res.count())
            if res.count() > 0:
                zd.index=avrIndex/res.count()
            else:
                zd.index=float(r[0].index)
            zd.co=co
            zd.no2=no2
            zd.pm10=pm10
            zd.location=location
            zd.position=position
            zd.history=historyArr
            zd.min24Hr=1.0
            zd.max24Hr=1.0

            rec = Report(
                name=zoneTitle + " " + zoneSubTitle,
                key_name=zoneKey,
                zoneKey=zoneKey,
                report=zd.to_JSON()
            )

            rec.put()

            myKey = db.Key.from_path('Report', zoneKey)
            rec = db.get(myKey)
            rec.report = zd.to_JSON()
            rec.put()






class Index(webapp2.RequestHandler):
    def get(self):
		template_values = {
			'greetings': 'zxc',
		}
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
        ('/worker', RegisterRecord),
        ('/gbg1', Goteborg),
        ('/umea1', Umea),
        ('/hamburg1', Hamburg1),
        ('/sthlm', Sthlm),
        ('/eaa',Eaa),
        ('/index.html', Index)
    ], debug=True)
