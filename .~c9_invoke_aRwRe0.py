#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
Canary Warf, London - 51.501538, -0.015757

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

"""
Deploy:
git add . && git commit -m 'Some stuff' && git push && gcloud -q app deploy --version=primary
"""
import sys
sys.path.insert(0, 'libs')
import os
import ast
import logging
import jinja2
import webapp2
import json
import urllib
import urllib2
import base64
from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from protorpc import messages
from protorpc import message_types
from protorpc import remote
from random import randrange
import datetime
import calendar
import time
import csv
import StringIO
import json
import re
from xml.dom import minidom
from google.appengine.ext import db
import hashlib
import yaml
from bs4 import BeautifulSoup
#from httplib2 import Http
#from oauth2client.service_account import ServiceAccountCredentials
#from apiclient.discovery import build
#import requests

#GEOLOCATION_URL = "https://maps.googleapis.com/maps/api/geocode/json?language=en&key=AIzaSyDTr4jvDt3ZM1Nv68mMR_mcw8TxyQV7x5k&latlng=%s"
GEOLOCATION_URL = "https://maps.googleapis.com/maps/api/geocode/json?language=en&key=AIzaSyAZQS_TBcZ2XNhApQttypDRarDWcy_phG4&latlng=%s"

# http://apis-explorer.appspot.com/apis-explorer/?base=http://localhost:8080/_ah/api#p/

JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),extensions=['jinja2.ext.autoescape'],autoescape=True)
FOOBOT_LOCATIONS = {
  "flintbacken10": "59.310014,18.050748",
  "Bondegatan21-Ugnen": "59.312963,18.080363",
  "HappyWattBot05Bergsunds Strand": "59.316569,18.026894",
  "Peringskioldsvagen58": "59.35111,17.90213",
  "cykelfabriken": "59.311971,18.082123",
  "LBK": "59.313408,18.033371",
  "Pauls_dagis": "59.310029,18.047490",
  "fargfabriken_utebar":"59.314924,18.019890",
  "Peringv58_VerifyPaul":"59.35111,17.90213",
  "Atterbomsvagen":"59.3273015,18.0088859"
}


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
    pm25 = db.FloatProperty()
    o3 = db.FloatProperty()
    co = db.FloatProperty()
    no2 = db.FloatProperty()
    index = db.FloatProperty()
    position = db.GeoPtProperty()
    positionLabels = db.StringProperty()
    sourceId = db.StringProperty()
    zoneKey = db.StringProperty()



class Bot(webapp2.RequestHandler):
    def get(self):
        postdata = {}
        postdata['sourceId'] = "BotFargfabriken"
        postdata['position'] = "59.31472280000001,18.02025470000001"
        postdata['pm10'] = '22' # Should be a bit random
        taskqueue.add(url='/worker', params=postdata)
        self.response.write(postdata)




#http://www.airnowapi.org/aq/data/?startDate=2016-05-15T22&endDate=2016-05-15T23&parameters=O3,PM25,PM10,CO,NO2,SO2&BBOX=-124.205070,28.716781,-75.337882,45.419415&dataType=B&format=application/json&verbose=0&API_KEY=0A8FF804-8227-4C80-A150-A495616F30DB
class Airnow(webapp2.RequestHandler):
    def get(self):
        isonowinUsa = datetime.datetime.now() - datetime.timedelta(hours=1)
        isotoday = isonowinUsa.date().isoformat()
        hour = isonowinUsa.hour
        url = "http://www.airnowapi.org/aq/data/?startDate=" + isotoday + "T" + str(hour) + "&endDate=" + isotoday + "T" + str(hour+1) + "&parameters=O3,PM25,PM10,CO,NO2&BBOX=-124.205070,28.716781,-75.337882,45.419415&dataType=B&format=application/json&verbose=0&API_KEY=0A8FF804-8227-4C80-A150-A495616F30DB"
        #url = "http://www.airnowapi.org/aq/data/?startDate=2016-05-15T22&endDate=2016-05-15T23&parameters=PM25,PM10&BBOX=-116.938171,27.476288,-73.520203,43.154850&dataType=B&format=application/json&verbose=0&API_KEY=0A8FF804-8227-4C80-A150-A495616F30DB"
        print url
        #self.response.write(url)

        headers = {'Accept':'application/json;charset=UTF-8','Content-Type':'application/json'}
        result = urlfetch.fetch(
            url,
            headers=headers,
            method='GET'
        )
        try:
            #hashlib.md5(zoneKeyInputString.encode('ascii', 'ignore').decode('ascii')).hexdigest()
            data = json.loads(result.content)
            for obj in data:
                postdata = {}
                #{u'Category': 1, u'Longitude': -123.64835, u'UTC': u'2016-05-15T22:00', u'Parameter': u'PM2.5', u'AQI': 7, u'Latitude': 42.1617, u'Value': 1.6, u'Unit': u'UG/M3'},
                lat = obj['Latitude']
                lon = obj['Longitude']
                position = str(lat) + "," + str(lon)
                sourceId = "AirNow" + hashlib.md5(position.encode('ascii', 'ignore').decode('ascii')).hexdigest()
                parameter = obj['Parameter']
                if parameter == 'OZONE':
                    parameter = parameter.replace('OZONE', 'o3')
                value = str(obj['Value'])
                postdata['sourceId'] = sourceId
                postdata['position'] = position
                postdata[parameter.lower()] = value
                taskqueue.add(url='/worker', params=postdata)

            self.response.write(data)

        except Exception, e:
            self.response.write(e)

class Linkoping(webapp2.RequestHandler):
    def get(self):
        isotoday = datetime.datetime.now().date().isoformat()
        url = "http://nods.se/rest/air/municipalities/0580?from=" + isotoday + "&minified=true"
        print url
        headers = {'Accept':'application/json;charset=UTF-8','Content-Type':'application/json'}
        result = urlfetch.fetch(
            url,
            headers=headers,
            method='GET'
        )
        try:
            data = json.loads(result.content)
            dataLatest = data['airMeasurements'][0]
            postdata = {}
            time = dataLatest["time"]
            pm = dataLatest["value"]
            postdata['sourceId'] = "Linkoping-hamngatan-nods"
            postdata['position'] = "58.408413,15.631572"
            postdata['pm10'] = str(pm)
            taskqueue.add(url='/worker', params=postdata)
            self.response.write(postdata)

        except Exception, e:
            self.response.write("no data available: " + url)

class Foobot(webapp2.RequestHandler):
    def get(self):
        isotoday = datetime.datetime.now().date().isoformat()
        print isotoday
        #urlLogin = 'https://api.foobot.io/v2/user/lars@wattsgard.se/login/'
        urlLogin = 'http://api-eu-west-1.foobot.io/v2/user/lars%40wattsgard.se/login/'

        urlDevice = 'https://api-eu-west-1.foobot.io/v2/owner/lars%40wattsgard.se/device/'
        urlData = 'https://api-eu-west-1.foobot.io/v2/device/%s/datapoint/'+ isotoday + 'T00:00/' + isotoday + 'T23:59:00/0/'
        urlfetch.set_default_fetch_deadline(60)
        # First. Login and get the token
        base64string = base64.encodestring('%s:%s' % ("lars@wattsgard.se", "AirUp123")).replace('\n', '')
        headers = {'Accept':'application/json;charset=UTF-8','Content-Type':'application/json'}

        payload="{\"password\":\"AirUp123\"}"
        resLogin = urlfetch.fetch(
            urlLogin,
            headers=headers,
            method='POST',
            payload=payload
        )

        if resLogin.status_code == 200:
            token = resLogin.headers['X-AUTH-TOKEN']
            # 2 use the token to get all devices
            headers = {'Accept':'application/json;charset=UTF-8','Content-Type':'application/json','X-AUTH-TOKEN': token}
            responseDev = urlfetch.fetch(
                urlDevice,
                method='GET',
                headers = headers
            )
            devices = json.loads(responseDev.content)
            for dev in devices:
                postdata = {}
                # 3. using each device uuid get all data (within the dates)
                #self.response.write(dev)
                #print dev['uuid']
                responseData = urlfetch.fetch(url=urlData % dev['uuid'], method = urlfetch.GET, headers = {"X-AUTH-TOKEN": token})
                fooData = responseData.content
                #self.response.write(fooData)
                headers = ("s",
                    "ugm3",
                    "C",
                    "pc",
                    "ppm",
                    "ppb",
                    "%")
                j = json.loads(fooData)
                dp = j['datapoints']

                if dp:
                    latest = dp[0]
                    if latest:
                        postdata = {}
                        time = latest[0]
                        pm = latest[1]
                        sourceId = dev['name'].strip()
                        postdata['sourceId'] = sourceId
                        postdata['position'] = FOOBOT_LOCATIONS[sourceId]
                        postdata['pm25'] = str(pm)
                        taskqueue.add(url='/worker', params=postdata)
                        self.response.write(postdata)
        else:
            self.response.write(resLogin.content)

#http://www.stateair.net/web/rss/1/1.xml
class Stateair(webapp2.RequestHandler):

    def get(self):

        def getText(nodelist):
            rc = []
            for node in nodelist:
                if node.nodeType == node.TEXT_NODE:
                    rc.append(node.data)
            return ''.join(rc).encode("utf-8","ignore")

        def regData(url, sourceId, position):

            response = urllib2.urlopen(url, timeout = 90)
            xmldoc = minidom.parse(response)
            items = xmldoc.getElementsByTagName('item')
            latestItem = items[0]
            conc = latestItem.getElementsByTagName("Conc")[0]
            postdata = {}
            postdata['sourceId'] = sourceId
            postdata['position'] = position
            postdata['pm25'] = str(getText(conc.childNodes))
            self.response.write(postdata)
            taskqueue.add(url='/worker', params=postdata)

        regData("http://www.stateair.net/web/rss/1/1.xml", "StateairBeijing", "39.904211,116.407395")
        regData("http://www.stateair.net/web/rss/1/2.xml", "StateairChengdu", "30.572816,104.066801")
        regData("http://www.stateair.net/web/rss/1/3.xml", "StateairGuangzhou", "23.129110,113.264385")
        regData("http://www.stateair.net/web/rss/1/4.xml", "StateairShanghai", "31.230416,121.473701")
        regData("http://www.stateair.net/web/rss/1/5.xml", "StateairShenyang", "41.805699,123.431472")
        regData("https://stateair.mn/rss.xml", "StateairUlanBator", "47.886399,106.905744")



class Eaa(webapp2.RequestHandler):

    def get(self):

        def regData(country):
            isotoday = datetime.datetime.now().date().isoformat()
            url = "http://fme.discomap.eea.europa.eu/fmedatastreaming/AirQuality/AirQualityUTDExport.fmw?FromDate=" + isotoday + "&ToDate=" + isotoday + "&Countrycode=" + country + "&InsertedSinceDate=&UpdatedSinceDate=&Pollutant=PM10&Namespace=&Format=XML&UserToken=6C2D03D8-04E1-4D07-B856-D92ACE0FA832"
            response = urllib2.urlopen(url, timeout = 90)
            xmldoc = minidom.parse(response)
            records = xmldoc.getElementsByTagName('record')
            self.response.write("<br/><code>" + url + " - " + str(len(records)) + " <code><br/>")

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
                self.response.write(postdata)
                taskqueue.add(url='/worker', params=postdata)


        country = self.request.get('country')
        regData(country)
        self.response.write("<br/><code>EAA DONE<code><br/>")



class Hamburg1(webapp2.RequestHandler):

    def get(self):
        #print "HBG"

        def regData(url, sourceId, position):

            response = urllib2.urlopen(url)
            cr = csv.reader(response)
            postdata = {
                'sourceId': sourceId,
                'position': position,
                'pm10': '',
                'pm25': '',
                'o3': '',
                'co': '',
                'no2': ''
            }
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



            #postdata['sourceId'] = sourceId
            #postdata['position'] = position

            self.response.write("<br/><code>DONE " + sourceId + "<code><br/>")
            taskqueue.add(url='/worker', params=postdata)

        """
        Data from http://luft.hamburg.de/
        """
        regData("http://hamburg.luftmessnetz.de/station/70MB.csv?componentgroup=pollution&componentperiod=1h&searchperiod=currentday","Hamburg-70MB", "53.555555,9.943407")
        regData("http://hamburg.luftmessnetz.de/station/17SM.csv?componentgroup=pollution&componentperiod=1h&searchperiod=currentday","Hamburg-17SM", "53.560899,9.957213")
        #regData("http://hamburg.luftmessnetz.de/station/68HB.csv?componentgroup=pollution&componentperiod=1h&searchperiod=currentday","Hamburg-68HB", "53.592354,10.053774")
        regData("http://hamburg.luftmessnetz.de/station/24FL.csv?componentgroup=pollution&componentperiod=1h&searchperiod=currentday","Hamburg-24FL", "53.638128,9.996872")
        regData("http://hamburg.luftmessnetz.de/station/61WB.csv?componentgroup=pollution&componentperiod=1h&searchperiod=currentday","Hamburg-61WB", "53.508315,9.990633")
        regData("http://hamburg.luftmessnetz.de/station/13ST.csv?componentgroup=pollution&componentperiod=1h&searchperiod=currentday","Hamburg-13ST", "53.562087,9.964416")

class Goteborg(webapp2.RequestHandler):

    def get(self):
        url = "http://data.goteborg.se/AirQualityService/v1.0/LatestMeasurement/4abad3dd-5d24-4c9c-9d17-79a946abe6c2?format=json"
        response = urllib2.urlopen(url);
        data = json.loads(response.read())

        postdata = {
            'sourceId': 'GBG1',
            'position': '57.708870,11.974560',
            'pm10': '',
            'pm25': '',
            'o3': '',
            'co': '',
            'no2': ''
        }
        try:
        	pm10 = data['AirQuality']['PM10']['Value']
        	postdata.pm10 = str(pm10)
        except Exception, e:
        	print "no pm10"
        	#postdata['pm10'] = 0

        try:
        	no2 = data['AirQuality']['NO2']['Value']
        	postdata.no2 = str(((no2/1000.0000)*24.4500)/46.0100) #Convert mg/m3 to ppm
        except Exception, e:
        	print "No no2"
        	#postdata['no2'] = 0

        try:
        	co = data['AirQuality']['CO']['Value']
        	postdata.co = str(((co/1000.0000)*24.4500)/28.0100) #Convert mg/m3 to ppm
        except Exception, e:
        	print "No co"
        	#postdata['co'] = 0


        taskqueue.add(url='/worker', params=postdata)

        self.response.write(postdata)



class SubmitToQueue(webapp2.RequestHandler):

    def post(self):

        postdata = {}

        try:
            pm10=self.request.get('pm10')
            postdata['pm10'] = str(pm10)
        except Exception, e:
            print "no pm10"

        try:
            pm25=self.request.get('pm25')
            postdata['pm25'] = str(pm25)
        except Exception, e:
            print "no pm25"

        try:
            o3=self.request.get('o3')
            postdata['o3'] = str(o3)
        except Exception, e:
            print "No o3"

        try:
            no2=self.request.get('no2')
            postdata['no2'] = str(no2)
        except Exception, e:
            print "No no2"

        try:
            co=self.request.get('co')
            postdata['co'] = str(co)
        except Exception, e:
            print "No co"

        try:
            sourceId=self.request.get('sourceId')
            postdata['sourceId'] = sourceId
        except Exception, e:
            print "No sourceId"

        try:
            lat=self.request.get('lat')
            lon=self.request.get('lon')
            postdata['position'] = lat + ',' + lon
        except Exception, e:
            print "No position"


        self.response.write(postdata)

        taskqueue.add(url='/worker', params=postdata)



class Umea(webapp2.RequestHandler):
    def get(self):
        #print "#### UMEA ####"
    	#logging.info("UMEA")
    	url = "http://ckan.openumea.se/api/action/datastore_search?resource_id=27fb8bcc-23cb-4e85-b5b4-fde68a8ef93a&limit=1&sort=M%C3%A4ttidpunkt%20desc"
        try:
            response = urllib2.urlopen(url);
            data = json.loads(response.read())
        except Exception, e:
            print "Error"

    	#postdata = {}
    	try:
    		pm10 = data['result']['records'][0]['PM10']
    		#postdata['pm10'] = str(float(pm10))
    	except Exception, e:
    		pm10 = 0

        pm10str = str(float(pm10))

    	try:
    		no2 = data['result']['records'][0]['NO2']
    		#postdata['no2'] = str(((no2/1000.0000)*24.4500)/46.0100) #Convert mg/m3 to ppm
    	except Exception, e:
    		no2 = 0

        no2str = str(((no2/1000.0000)*24.4500)/46.0100)

        payload = {
            'sourceId': 'UMEA1',
            'position': '63.827743,20.256825',
            'pm10': pm10str,
            'pm25': '',
            'o3': '',
            'no2': no2str
        }

        taskqueue.add(url='/worker', params=payload)
    	self.response.write(payload)

class Sthlm(webapp2.RequestHandler):
    def get(self):
        SLB_LOCATIONS = {
          "Hornsgatan": "59.310014,18.050748",
          "Folkungagatan": "59.312963,18.080363",
          "Lilla Essingen (E4/E20)": "59.316569,18.026894",
          "Södertälje Turingegatan": "59.35111,17.90213",
          "Uppsala Kungsgatan": "59.311971,18.082123",
          "Gävle Södra Kungsgatan": "59.313408,18.033371"
        }
        SLB_POLLUTANT = ["pm10", "pm25", "no2", "o3"]

        def find_between( s, first, last ):
            try:
                start = s.index( first ) + len( first )
                end = s.index( last, start )
                return s[start:end]
            except ValueError:
                return ""

        url = "http://slb.nu/slbanalys/luften-idag/"
        headers = {'Accept':'text/html;charset=UTF-8','Content-Type':'text/html'}
        result = urlfetch.fetch(
            url,
            headers=headers,
            method='GET'
        )
        soup = BeautifulSoup(result.content, 'html.parser')
        scripts = soup.find_all('script')
        start = "var data = google.visualization.arrayToDataTable("
        end = ");"
        slbLocations = {
          "Hornsgatan": {'sourceId': 'SLB-Hornsgatan','position': '59.317242,18.049891','pm10': '','pm25': '','o3': '','no2': ''},
          "Folkungagatan": {'sourceId': 'SLB-Folkungagatan','position': '59.314508,18.075318','pm10': '','pm25': '','o3': '','no2': ''},
          "Lilla Essingen (E4/E20)": {'sourceId': 'SLB-Lilla Essingen','position': '59.325304,18.00296','pm10': '','pm25': '','o3': '','no2': ''},
          "Södertälje Turingegatan": {'sourceId': 'SLB-Sodertalje Turingegatan','position': '59.199148,17.625546','pm10': '','pm25': '','o3': '','no2': ''},
          "Uppsala Kungsgatan": {'sourceId': 'SLB-Uppsala Kungsgatan','position': '59.199148,17.625546','pm10': '','pm25': '','o3': '','no2': ''},
          "Gävle Södra Kungsgatan": {'sourceId': 'SLB-Gavle Sodra Kungsgatan','position': '60.672235,17.146665','pm10': '','pm25': '','o3': '','no2': ''},
        }
        payload = {'sourceId': '','position': '','pm10': '','pm25': '','o3': '','no2': ''}
        j = 0
        for scr in scripts:
            scrStr = str(scr)
            if start in scrStr:
                slbDataJs = str(find_between( scrStr, start, end))
                slbDataJs = slbDataJs.replace("null","None")
                slbData = ast.literal_eval(slbDataJs)
                i = 0
                for locationTitle in slbData[0]:
                    try:
                        position = SLB_LOCATIONS[locationTitle]
                        pass
                    except Exception as e:
                        position = None
                    if position:
                        dataValue = slbData[-1][i]
                        slbLocations[locationTitle][SLB_POLLUTANT[j]] = str(dataValue)
                    i = i + 1
                j = j + 1
        for pl in slbLocations:
            self.response.write("<p>" + str(slbLocations[pl]) + "</p>")
            taskqueue.add(url='/worker', params=slbLocations[pl])

class StateairIndia(webapp2.RequestHandler):
    def get(self):
        # SLB_LOCATIONS = {
        #   "Hornsgatan": "59.310014,18.050748",
        #   "Folkungagatan": "59.312963,18.080363",
        #   "Lilla Essingen (E4/E20)": "59.316569,18.026894",
        #   "Södertälje Turingegatan": "59.35111,17.90213",
        #   "Uppsala Kungsgatan": "59.311971,18.082123",
        #   "Gävle Södra Kungsgatan": "59.313408,18.033371"
        # }
        # SLB_POLLUTANT = ["pm10", "pm25", "no2", "o3"]
        #
        def find_between( s, first, last ):
            try:
                start = s.index( first ) + len( first )
                end = s.index( last, start )
                return s[start:end]
            except ValueError:
                return ""

        url = "http://newdelhi.usembassy.gov/dyn/airqualitydataemb/air-quality-indicator-proxy.html"
        headers = {'Accept':'text/html;charset=UTF-8','Content-Type':'text/html'}
        result = urlfetch.fetch(
            url,
            headers=headers,
            method='GET'
        )
        soup = BeautifulSoup(result.content, 'html.parser')
        scripts = soup.find_all('script')
        scrStr = str(scripts[1])

        start = '$("#HD_Cval").text("';
        end = '");'
        if start in scrStr:
            hyderabad = str(find_between( scrStr, start, end))
            self.response.write(hyderabad)

        indiaLocations = {
          "Hornsgatan": {'sourceId': 'SLB-Hornsgatan','position': '59.317242,18.049891','pm10': '','pm25': '','o3': '','no2': ''},
          "Hyderabad": {'sourceId': 'UsConsulateHyderabad','position': '17.436926,78.489401','pm10': '','pm25': '','o3': '','no2': ''},
          "Lilla Essingen (E4/E20)": {'sourceId': 'SLB-Lilla Essingen','position': '59.325304,18.00296','pm10': '','pm25': '','o3': '','no2': ''},
          "Södertälje Turingegatan": {'sourceId': 'SLB-Sodertalje Turingegatan','position': '59.199148,17.625546','pm10': '','pm25': '','o3': '','no2': ''},
          "Uppsala Kungsgatan": {'sourceId': 'SLB-Uppsala Kungsgatan','position': '59.199148,17.625546','pm10': '','pm25': '','o3': '','no2': ''},
          "Gävle Södra Kungsgatan": {'sourceId': 'SLB-Gavle Sodra Kungsgatan','position': '60.672235,17.146665','pm10': '','pm25': '','o3': '','no2': ''},
        }
        # payload = {'sourceId': '','position': '','pm10': '','pm25': '','o3': '','no2': ''}
        # j = 0
        # for scr in scripts:
        #     scrStr = str(scr)
        #     if start in scrStr:
        #         slbDataJs = str(find_between( scrStr, start, end))
        #         slbDataJs = slbDataJs.replace("null","None")
        #         slbData = ast.literal_eval(slbDataJs)
        #         i = 0
        #         for locationTitle in slbData[0]:
        #             try:
        #                 position = SLB_LOCATIONS[locationTitle]
        #                 pass
        #             except Exception as e:
        #                 position = None
        #             if position:
        #                 dataValue = slbData[-1][i]
        #                 slbLocations[locationTitle][SLB_POLLUTANT[j]] = str(dataValue)
        #             i = i + 1
        #         j = j + 1
        # for pl in slbLocations:
        #     self.response.write("<p>" + str(slbLocations[pl]) + "</p>")
        #     taskqueue.add(url='/worker', params=slbLocations[pl])



tableAqiIndex = [ range(0, 50, 1),range(51, 100, 1),range(101, 150, 1),range(151, 200, 1),range(201, 300, 1),range(301, 400, 1),range(401, 500, 1) ]
tableCo = [ range(0, 44, 1),range(45, 94, 1),range(95, 124, 1),range(125, 154, 1),range(155, 304, 1),range(305, 404, 1),range(405, 504, 1) ]
tableNo2 = [ range(0, 53, 1),range(54, 100, 1),range(101, 360, 1),range(361, 640, 1),range(650, 1240, 1),range(1250, 1640, 1),range(1650, 2040, 1) ]
tableO3 = [ range(0, 53, 1),range(54, 100, 1),range(101, 360, 1),range(361, 640, 1),range(650, 1240, 1),range(1250, 1640, 1),range(1650, 2040, 1) ]
tablePm10 = [ range(0, 54, 1),range(55, 154, 1),range(155, 254, 1),range(255, 354, 1),range(355, 424, 1),range(425, 504, 1),range(505, 604, 1) ]
tablePm25 = [ range(0, 54, 1),range(55, 154, 1),range(155, 254, 1),range(255, 354, 1),range(355, 424, 1),range(425, 504, 1),range(505, 604, 1) ]
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
    pm25=values["pm25"]
    o3=values["o3"]
    no2=values["no2"]

    #print "%%%% AQI %%%%"
    #print values
    #print "ISDIG"
    #print pm10

    f = 0
    coIndex = 0
    pm10Index = 0
    pm25Index = 0
    o3Index = 0
    no2Index = 0

    if co.replace('.','',1).isdigit():
        coIndex = index(tableCo, float(co), 10)
        f = f+1

    if pm10.replace('.','',1).isdigit():
    	pm10Index = index(tablePm10, float(pm10), 1)
    	f = f+1

    if pm25.replace('.','',1).isdigit():
    	pm25Index = index(tablePm25, float(pm25), 1)
    	f = f+1

    if o3.replace('.','',1).isdigit():
    	o3Index = index(tableO3, float(o3), 1)
    	f = f+1

    # TODO: Check the factor
    if no2.replace('.','',1).isdigit():
    	no2Index = index(tableNo2, float(no2), 1)
    	f = f+1

    if f > 0:
        return float((coIndex + pm10Index + pm25Index + o3Index + no2Index)/f)



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
    #"123,123", "[country]", "short_name"

    url=GEOLOCATION_URL % latlng
    data = memcache.get(latlng)
    if data is None:
        print "getGeoValue - Data for " + latlng + " not in cache. Reading from API..."
        data = json.loads(get_geolocation_url_src(url))
        memcache.add(latlng,data)

    results = data["results"]
    def getGeoValueForAddress(res):
        for key1 in keys:
            for ac in res["address_components"]:
                if key1 in ac["types"]:
                    return ac[valueType]
        return None


    for key in keys:
        for res in results:
            if key in res["types"]:
                returnVal = getGeoValueForAddress(res)
                return returnVal
    return None

def getGeoFormattedAddress(latlng, keys):
    url=GEOLOCATION_URL % latlng
    data = memcache.get(latlng)
    if data is None:
        #print "getGeoFormattedAddress - Data for " + latlng + " not in cache. Reading from API..."
        data = json.loads(get_geolocation_url_src(url))
        memcache.add(latlng,data)


    for key in keys:
        for res in data["results"]:
            if key in res["types"]:
                return res["formatted_address"]
    return None

def getGeoPosition(latlng, keys):
    url=GEOLOCATION_URL % latlng
    data = memcache.get(latlng)
    if data is None:
        print "getGeoPosition - Data for " + latlng + " not in cache. Reading from API..."
        data = json.loads(get_geolocation_url_src(url))
        memcache.add(latlng,data)

    for key in keys:
        for res in data["results"]:
            if key in res["types"]:
                return str(res["geometry"]["location"]["lat"]) + "," + str(res["geometry"]["location"]["lng"])
    return None


def getLocationContext(latlng):
    context = {}
    keyList = ["neighborhood","sublocality_level_2","sublocality_level_1","administrative_area_level_3","colloquial_area","postal_code"]
    try:
        addrString = getGeoFormattedAddress(latlng, keyList).encode("utf-8")
        hoodPosition = getGeoPosition(latlng, keyList)
        addrList = addrString.split(", ")
        zoneTitle = addrList[0].decode("utf-8","ignore")
        addrList.remove(addrList[0])
        addrList.remove(addrList[-1])
        zoneSubTitle = ", ".join(addrList).decode("utf-8")
    
        country = getGeoValue(latlng, ["country"], "short_name")
        if country is None:
            return None
    
        context["zoneTitle"] = zoneTitle
        context["zoneSubTitle"] = zoneSubTitle
        context["country"] = country
        context["zoneKey"] = generateZoneKey(zoneTitle,zoneSubTitle,country)
        context["position"] = hoodPosition
        return context
    except Exception, e:
        return None

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
        
        sourceId = self.request.get('sourceId')
        
        logging.info("### RECORD SOURCEID " + sourceId)

        pm10=self.request.get('pm10')
        pm25=self.request.get('pm25')
        o3=self.request.get('o3')
        co=self.request.get('co')
        no2=self.request.get('no2')

        #print "PM10: " + pm10
        #print "CO: " + co
        #print "NO2: " + no2

        aqiValue=aqi({"co":co,"pm10":pm10,"pm25":pm25,"o3":o3,"no2":no2})

        if aqiValue is None:
            print "No AQI"
        else:
            if not co.replace('.','',1).isdigit():
                co = None
            else:
                co = float(co)

            if not pm10.replace('.','',1).isdigit():
                pm10 = None
            else:
                pm10 = float(pm10)

            if not pm25.replace('.','',1).isdigit():
                pm25 = None
            else:
                pm25 = float(pm25)

            if not o3.replace('.','',1).isdigit():
                o3 = None
            else:
                o3 = float(o3)

            if not no2.replace('.','',1).isdigit() is None:
                no2 = None
            else:
                no2 = float(no2)

            latlng = self.request.get('position')

            locationContext = getLocationContext(latlng)
            
            if (locationContext is None):
                return None
                
            zoneKey = locationContext.get('zoneKey')
            zoneTitle = locationContext.get('zoneTitle')
            zoneSubTitle = locationContext.get('zoneSubTitle')
            country = locationContext.get('country')
            position = locationContext.get('position')
            timestamp = self.request.get('timestamp')
            if not timestamp:
                timestamp = calendar.timegm(time.gmtime())

            """
            Now, generate the report...
            1. Hitta ytterligare poster i samma zone
            2. Rakna ut medeltal for index och de olika gaserna.
            3. Kolla om det finns en rapport sedan tidigare.
            4. spara historiska data
            5. Berakna min24hr och max 24hr
            """
            
            reportDbRecord = Report(
                name=zoneTitle + " " + zoneSubTitle,
                key_name=zoneKey,
                zoneKey=zoneKey
            )            

            """ Get the data newer than 1 hour """
            #res = db.GqlQuery("SELECT * FROM Records WHERE zoneKey='" + zoneKey + "' AND timestamp >= :1", datetime.datetime.now() - datetime.timedelta(hours = 6))
            #res = db.GqlQuery("SELECT * FROM Records WHERE zoneKey='" + zoneKey + "'")
            
            recordQuery = Records.all()
            recordQuery.ancestor(reportDbRecord)

            """ Create a list of all stations and history values """
            avrIndex = 0
            resCount = 0
            stationsDict = {}
            historyDict = {}
            indexArr = []
            for r in recordQuery.run():
                #logging.info("### RECORD SOURCEID " + r.sourceId)
                historyDate = r.timestamp.strftime('%Y-%m-%d')
                indexArr = historyDict.get(historyDate, [0.0])
                indexArr.append(r.index)
                historyDict[historyDate] = indexArr
                avrIndex = avrIndex + r.index
                stationsDict[r.sourceId] = str(r.position)
                resCount = resCount + 1

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
            try:
                zd.numberOfMeasurements=str(resCount)
                if resCount > 0:
                    zd.index=avrIndex/resCount
                else:
                    #zd.index=float(res[0].index)
                    zd.index=0
            except Exception, e:
            	print "numberOfMeasurements and index set to 0"
                zd.numberOfMeasurements = 0
                zd.index = 0

            zd.co=co
            zd.no2=no2
            zd.pm10=pm10
            zd.pm25=pm25
            zd.o3=o3
            zd.location=location
            zd.position=position
            zd.history=historyArr
            zd.min24Hr=1.0
            zd.max24Hr=1.0



            
            # recordQuery = Records.all()
            # recordQuery.ancestor(reportDbRecord)
            # for rrr in recordQuery.run(limit=5):
            #     logging.info("### RECORD " + rrr.sourceId)
                    
            reportDbRecord.report=zd.to_JSON()
            reportDbRecord.put()

            rec=Records(
                parent=reportDbRecord,
                timestamp=datetime.datetime.fromtimestamp(float(timestamp)),
                pm10=pm10,
                pm25=pm25,
                o3=o3,
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

            # Save data in fusion table.
            # scopes = ['https://www.googleapis.com/auth/fusiontables']
            #credentials = ServiceAccountCredentials.from_json_keyfile_name('airupBackend-b120f4cbc1a7.json', scopes)
            #credentials = ServiceAccountCredentials.from_json_keyfile_name('airupdata-297e9f1e1562.json', scopes)
            #fusiontablesadmin = build('fusiontables', 'v2', credentials=credentials)
            #fusiontablesadmin.query().sql(sql="INSERT INTO 1VQ8VQZwKY7zjrTqAxQTtlYdt18bjsbU7Gx4_nyK7 ('Source ID','index','Date','Pos') VALUES ('" + self.request.get('sourceId') + "', " + aqiValue + ", '" + datetime.datetime.fromtimestamp(float(timestamp)) + "', '" + self.request.get('position') + "') ").execute()



            # myKey = db.Key.from_path('Report', zoneKey)
            # rec = db.get(myKey)
            # rec.report = zd.to_JSON()
            # rec.put()



class Index(webapp2.RequestHandler):
    def get(self):
		template_values = {
			'greetings': 'zxc',
		}
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))


app = webapp2.WSGIApplication([
        ('/worker', RegisterRecord),
        ('/bot', Bot),
        ('/linkoping', Linkoping),
        ('/airnow', Airnow),
        ('/india', StateairIndia),
        ('/gbg1', Goteborg),
        ('/umea1', Umea),
        ('/hamburg1', Hamburg1),
        ('/sthlm', Sthlm),
        ('/eaa',Eaa),
        ('/foobot',Foobot),
        ('/stateair',Stateair),
        ('/submitToQueue',SubmitToQueue),
        ('/index.html', Index)
    ], debug=True)
