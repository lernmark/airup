# coding=utf-8
"""Hello World API implemented using Google Cloud Endpoints.

Defined here are the ProtoRPC messages needed to define Schemas for methods
as well as those methods defined in an API.
"""

import logging
import endpoints
import urllib2
from google.appengine.ext import db
from google.appengine.api import taskqueue
from google.appengine.api import urlfetch
from protorpc import messages
from protorpc import message_types
from protorpc import remote
import datetime
import time
import json
import random
package = 'Airup'


class Report(db.Model):
    name = db.StringProperty()
    report = db.StringProperty(multiline=True)

"""
Används för att representera mätdata från en mätare
"""
class Record(messages.Message):
    timestamp = messages.StringField(1)
    pm10 = messages.FloatField(2)
    co = messages.FloatField(3)
    no2 = messages.FloatField(4)
    index = messages.FloatField(5)
    position = messages.StringField(6)
    positionLabels = messages.StringField(7)
    sourceId = messages.StringField(8, required=True)

class TodayDetail(messages.Message):
    index = messages.FloatField(1)
    location = messages.StringField(2)

class FactMessage(messages.Message):
    body = messages.StringField(1)

class Fact(db.Model):
    body = db.StringProperty()

class TodayType(messages.Message):
    best = messages.MessageField(TodayDetail, 1, repeated=False)
    worst = messages.MessageField(TodayDetail, 2, repeated=False)

class Location(messages.Message):
    country = messages.StringField(1)
    language = messages.StringField(2)

class IndexCategory(messages.Message):
    upTo = messages.FloatField(1)
    label = messages.StringField(2)

class HistoricDate(messages.Message):
    date = messages.StringField(1)
    index = messages.FloatField(2)

"""
    Class that represents a stored ZoneDetail
"""
class ZoneDetail(messages.Message):
    title = messages.StringField(1)
    index = messages.FloatField(2)
    co = messages.FloatField(3)
    no2 = messages.FloatField(4)
    max24Hr = messages.FloatField(5)
    min24Hr = messages.FloatField(6)
    timestamp = messages.FloatField(7)
    id = messages.FloatField(8)
    subtitle = messages.StringField(9)
    history = messages.MessageField(HistoricDate, 10, repeated=True)
    location = messages.MessageField(Location, 11, repeated=False)
    zoneKey = messages.StringField(12)

# Class used to wrap a list of reporta and other
# stuff sucha as best, worst, index labels, etc.
class ZoneMessage(messages.Message):
    key = messages.StringField(1)
    zones = messages.MessageField(ZoneDetail, 2, repeated=True)
    today = messages.MessageField(TodayType, 3, repeated=False)
    indexCategory = messages.MessageField(IndexCategory, 4, repeated=True)
    timestamp = messages.FloatField(5)
    facts = messages.MessageField(FactMessage, 6, repeated=True)


"""

API STARTS HERE

"""
@endpoints.api(name='airup', version='v1')
class AirupApi(remote.Service):
    """Airup API v1."""


    FACT_RESOURCE = endpoints.ResourceContainer(FactMessage)
    @endpoints.method(FACT_RESOURCE, FactMessage, path='addNewFact', http_method='POST', name='factMessage.addNew')
    def factMessage_addNew(self, request):
        fact = Fact(
            body=request.body
        )
        fact.put()
        return FactMessage(body=request.body)


    """
    Save raw-data-records from stations.
    """
    MULTIPLY_METHOD_RESOURCE = endpoints.ResourceContainer(Record)
    @endpoints.method(MULTIPLY_METHOD_RESOURCE, Record, path='queueIt', http_method='POST', name='records.queueRecord')
    def records_queueRecord(self, request):
        """Use this method to post records"""
        recPayload = {}

        recPayload["timestamp"] = request.timestamp
        if not request.timestamp:
            recPayload["timestamp"] = float(time.time())

        recPayload["position"] = request.position
        if not request.position:
            recPayload["position"] = "52.37, 4.88"

        recPayload["pm10"] = None
        recPayload["co"] = None
        recPayload["no2"] = None
        recPayload["sourceId"] = None
        
        recPayload["co"] = request.co
        recPayload["pm10"] = request.pm10
        recPayload["no2"] = request.no2
        recPayload["sourceId"] = request.sourceId
        taskqueue.add(queue_name='recordQueue', url='/worker', params=recPayload)
        return Record(timestamp=request.timestamp,position=request.position,sourceId=request.sourceId)


    """
    Returnera en ZoneDetail för en viss lat/long
    OBS! Ej klar...
    1. Använd geocode-api för att hitta platsen.
    2. Försök hitta en ZoneDetail som matchar
        a. neighborhood
        b. sublocality_level_2
        c. sublocality_level_1
        d. administrative_area_level_2
        e. administrative_area_level_1
        f. locality
        g. country
    3. Returnera hittad ZoneDetail
    """
    LATLONG_RESOURCE = endpoints.ResourceContainer(message_types.VoidMessage,lat=messages.StringField(1, variant=messages.Variant.STRING),long=messages.StringField(2, variant=messages.Variant.STRING))
    @endpoints.method(LATLONG_RESOURCE, ZoneDetail, path='location/lat/{lat}/long/{long}', http_method='GET', name='report.getLocation')
    def location_get(self, request):
        # Do some reverese geocoding and return the correct Zone
        # http://maps.googleapis.com/maps/api/geocode/json?latlng=59.330979,18.068874&sensor=true
        #print request.lat
        # https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyA1WnmUgVJtsGuWoyHh-U8zlKRcGlSACXU&latlng=59.312963,18.080363&sensor=true&result_type=sublocality_level_2|neighborhood&location_type=APPROXIMATE
        address="1600+Amphitheatre+Parkway,+Mountain+View,+CA"
        latlng = request.lat + "," + request.long
        #url="https://maps.googleapis.com/maps/api/geocode/json?address=%s" % address
        url="https://maps.googleapis.com/maps/api/geocode/json?key=AIzaSyA1WnmUgVJtsGuWoyHh-U8zlKRcGlSACXU&result_type=sublocality_level_2|neighborhood&location_type=APPROXIMATE&latlng=%s" % latlng
        response = urllib2.urlopen(url)
        #jsongeocode = response.read()
        data = json.loads(response.read())
        zone = data["results"][0]["address_components"][0]["long_name"]

        return ZoneDetail(id=4793444555816960.0,title=zone,subtitle='Stockholm, Sweden',index=200.0,co=24.0,no2=111.0,min24Hr=23.0,max24Hr=89.0,timestamp=float(time.time()))


    """
    API that returns specified zones or all zones
    """
    LOCATIONS_RESOURCE = endpoints.ResourceContainer(message_types.VoidMessage,zone=messages.StringField(1,repeated=True))
    @endpoints.method(LOCATIONS_RESOURCE, ZoneMessage, path='zones', http_method='GET', name='zones.getRequestedZones')
    def locations_get(self, request):

        ic = [
            IndexCategory(upTo=50.0,label="Good"),
            IndexCategory(upTo=100.0,label="Moderate"),
            IndexCategory(upTo=150.0,label="Unhealthy for Sensitive Group"),
            IndexCategory(upTo=200.0,label="Unhealthy"),
            IndexCategory(upTo=300.0,label="Very Unhealthy"),
            IndexCategory(upTo=500.0,label="Hazardous")
        ]

        try:

            factArr = []
            factResult = db.GqlQuery("SELECT * FROM Fact")
            for f in factResult:
                factArr.append(FactMessage(body=f.body))

            if len(request.zone) > 0:
                qArr = []
                for z in request.zone:
                    qArr.append("KEY('Report','" + z + "')")
                res = db.GqlQuery("SELECT * FROM Report WHERE __key__ IN (" + ", ".join(qArr) + ")")
            else:
                res = db.GqlQuery("SELECT * FROM Report")

            zonesArr = []
            for r in res:
                j = json.loads(r.report)
                loc = j["location"]["country"]
                zonesArr.append(
                    ZoneDetail(
                        title=j['title'],
                        subtitle=j.get('subtitle', None),
                        index=j.get('index', None),
                        co=j.get('co', None),
                        zoneKey=j.get('zoneKey', None),
                        no2=j.get('no2', None),
                        min24Hr=j.get('min24hr', None),
                        max24Hr=j.get('max24hr', None),
                        history=j.get('history'),
                        location=Location(country=j["location"]["country"],language="DE")
                        )
                    )
            return ZoneMessage(
                indexCategory = ic,
                timestamp=float(time.time()),
                today= TodayType(best=TodayDetail(index=3.0, location="Antartica"), worst=TodayDetail(index=425.0, location="Beijing")),
                zones = zonesArr,
                facts = factArr
                )  

            return ZoneMessage()
        except (IndexError, TypeError):
            raise endpoints.NotFoundException(IndexError)

APPLICATION = endpoints.api_server([AirupApi])
