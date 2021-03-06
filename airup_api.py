# coding=utf-8
"""API implemented using Google Cloud Endpoints.

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
import worker

package = 'Airup'


class Report(db.Model):
    name = db.StringProperty()
    report = db.TextProperty()

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
    pm25 = messages.FloatField(9)
    o3 = messages.FloatField(10)

class Records(messages.Message):
    records = messages.MessageField(Record, 1, repeated=True)

class Station(messages.Message):
    sourceId = messages.StringField(1)
    position = messages.StringField(2)

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

class Breakpoints(messages.Message):
    breakpointType = messages.StringField(1)
    category = messages.MessageField(IndexCategory, 2, repeated=True)
    unit = messages.StringField(3)
    minValue = messages.FloatField(4)
    maxValue = messages.FloatField(5)

class HistoricDate(messages.Message):
    date = messages.StringField(1)
    index = messages.FloatField(2)

"""
    Class that represents a stored ZoneDetail
"""
class ZoneDetailData(messages.Message):
    co = messages.FloatField(1)
    pm10 = messages.FloatField(2)
    no2 = messages.FloatField(3)
    index = messages.FloatField(4)
    pm25 = messages.FloatField(5)
    o3 = messages.FloatField(6)

class ZoneDetail(messages.Message):
    title = messages.StringField(1)
    max24Hr = messages.FloatField(5)
    min24Hr = messages.FloatField(6)
    timestamp = messages.FloatField(7)
    id = messages.FloatField(8)
    subtitle = messages.StringField(9)
    history = messages.MessageField(HistoricDate, 10, repeated=True)
    location = messages.MessageField(Location, 11, repeated=False)
    zoneKey = messages.StringField(12)
    numberOfMeasurements = messages.FloatField(13)
    stations = messages.MessageField(Station, 14, repeated=True)
    position = messages.StringField(15)
    data = messages.MessageField(ZoneDetailData, 16, repeated=False)


# Class used to wrap a list of reporta and other
# stuff sucha as best, worst, index labels, etc.
class ZoneMessage(messages.Message):
    key = messages.StringField(1)
    zones = messages.MessageField(ZoneDetail, 2, repeated=True)
    today = messages.MessageField(TodayType, 3, repeated=False)
    breakpoints = messages.MessageField(Breakpoints, 4, repeated=True)
    timestamp = messages.FloatField(5)
    facts = messages.MessageField(FactMessage, 6, repeated=True)

def getRawData(offset,prefix):

    try:
        offset = str(int(offset)*int(300))
        dataArr = []
        dataResult = db.GqlQuery("SELECT * FROM Records ORDER BY timestamp DESC LIMIT 300 OFFSET " + offset)
        for d in dataResult:
            # datetime.strptime("2015-12-16 21:10:22.670000"[0:19],"%Y-%m-%d %H:%M:%S")
            # time.strptime(str(d.timestamp),"%Y-%m-%d %H:%M:%S.%f")
            #print str(d.timestamp)[0:19]
            #print "123456789"[2:5]

            dataArr.append(
                Record(
                    timestamp = str(d.timestamp),

                    pm10 = d.pm10,
                    co = d.co,
                    no2 = d.no2,
                    pm25 = d.pm25,
                    o3 = d.o3,
                    index = d.index,
                    position = str(d.position),
                    positionLabels = d.positionLabels,
                    sourceId = d.sourceId
                )
            )

        return Records(
            records=dataArr
        )

    except (IndexError, TypeError):
        raise endpoints.NotFoundException(IndexError)



def generateZoneMessage(zone):
    """Return all zones or only specified zones"""
    numberOfCategories = 7
    ic = []
    for x in range(0, numberOfCategories):
        ic.append(IndexCategory(upTo=(worker.tableAqiIndex[x][-1]+1)/1.0,label=str(worker.indexLables[x])))

    coBreakpoints = []
    for x in range(0, numberOfCategories):
        coBreakpoints.append(IndexCategory(upTo=(worker.tableCo[x][-1]+1)/10.0,label=str(worker.indexLables[x])))

    pm10Breakpoints = []
    for x in range(0, numberOfCategories):
        pm10Breakpoints.append(IndexCategory(upTo=float(worker.tablePm10[x][-1]+1),label=str(worker.indexLables[x])))

    no2Breakpoints = []
    for x in range(0, numberOfCategories):
        no2Breakpoints.append(IndexCategory(upTo=(worker.tableNo2[x][-1]+1)/1000.0,label=str(worker.indexLables[x])))

    pm25Breakpoints = []
    for x in range(0, numberOfCategories):
        pm25Breakpoints.append(IndexCategory(upTo=float(worker.tablePm25[x][-1]+1),label=str(worker.indexLables[x])))

    o3Breakpoints = []
    for x in range(0, numberOfCategories):
        o3Breakpoints.append(IndexCategory(upTo=float(worker.tableO3[x][-1]+1),label=str(worker.indexLables[x])))


    try:

        factArr = []
        factResult = db.GqlQuery("SELECT * FROM Fact")
        for f in factResult:
            factArr.append(FactMessage(body=f.body))

        if len(zone) > 0:
            qArr = []
            for z in zone:
                qArr.append("KEY('Report','" + z + "')")
            res = db.GqlQuery("SELECT * FROM Report WHERE __key__ IN (" + ", ".join(qArr) + ")")
        else:
            res = db.GqlQuery("SELECT * FROM Report")

        zonesArr = []
        for r in res:
            j = json.loads(r.report)
            loc = j.get('location', None)
            zonesArr.append(
                ZoneDetail(
                    title=j['title'],
                    subtitle=j.get('subtitle', None),
                    data=ZoneDetailData(co=j.get('co', None), no2=j.get('no2', None),pm10=j.get('pm10', None),pm25=j.get('pm25', None),o3=j.get('o3', None),index=j.get('index', None)),
                    zoneKey=j.get('zoneKey', None),
                    min24Hr=j.get('min24hr', None),
                    max24Hr=j.get('max24hr', None),
                    position=j.get('position'),
                    history=j.get('history'),
                    stations=j.get('stations'),
                    location=Location(country=j["location"]["country"],language="en"),
                    numberOfMeasurements = float(j.get('numberOfMeasurements',None))
                    )
                )

        return ZoneMessage(
            breakpoints = [
                Breakpoints(breakpointType="index",category=ic, unit="AQI", minValue=0.0, maxValue=(worker.tableAqiIndex[numberOfCategories-1][-1]+1)/1.0),
                Breakpoints(breakpointType="co",category=coBreakpoints, unit="ppm", minValue=0.0, maxValue=(worker.tableCo[numberOfCategories-1][-1]+1)/10.0),
                Breakpoints(breakpointType="pm10",category=pm10Breakpoints, unit="µg/m³".decode('utf-8'), minValue=0.0, maxValue=float(worker.tablePm10[numberOfCategories-1][-1]+1)),
                Breakpoints(breakpointType="pm25",category=pm25Breakpoints, unit="µg/m³".decode('utf-8'), minValue=0.0, maxValue=float(worker.tablePm25[numberOfCategories-1][-1]+1)),
                Breakpoints(breakpointType="o3",category=o3Breakpoints, unit="µg/m³".decode('utf-8'), minValue=0.0, maxValue=float(worker.tableO3[numberOfCategories-1][-1]+1)),
                Breakpoints(breakpointType="no2",category=no2Breakpoints, unit="ppm", minValue=0.0, maxValue=(worker.tableNo2[numberOfCategories-1][-1]+1)/1000.0)
            ],
            timestamp=float(time.time()),
            today= TodayType(best=TodayDetail(index=3.0, location="Antartica"), worst=TodayDetail(index=425.0, location="Beijing")),
            zones = zonesArr,
            facts = factArr
            )

        return ZoneMessage()
    except (IndexError, TypeError):
        raise endpoints.NotFoundException(IndexError)



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
        recPayload["pm25"] = None
        recPayload["o3"] = None
        recPayload["sourceId"] = None

        recPayload["co"] = request.co
        recPayload["pm10"] = request.pm10
        recPayload["pm25"] = request.pm25
        recPayload["o3"] = request.o3
        recPayload["no2"] = request.no2
        recPayload["sourceId"] = request.sourceId
        taskqueue.add(queue_name='recordQueue', url='/worker', params=recPayload)
        return Record(timestamp=request.timestamp,position=request.position,sourceId=request.sourceId)


    """
    Returnera en ZoneDetail för en viss lat/lng
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
    LATLNG_RESOURCE = endpoints.ResourceContainer(message_types.VoidMessage,lat=messages.StringField(1, variant=messages.Variant.STRING),lng=messages.StringField(2, variant=messages.Variant.STRING))
    @endpoints.method(LATLNG_RESOURCE, ZoneMessage, path='location/lat/{lat}/lng/{lng}', http_method='GET', name='report.getLocation')
    def location_get(self, request):
        """
        Find the zone for current location...
        """
        latlng = request.lat + "," + request.lng

        try:
            context = worker.getLocationContext(latlng)
            zoneKey = context.get("zoneKey")
            return generateZoneMessage([zoneKey])
        except Exception, e:
            return ZoneMessage()

    LOCATIONS_RESOURCE = endpoints.ResourceContainer(message_types.VoidMessage,zone=messages.StringField(1,repeated=True))
    @endpoints.method(LOCATIONS_RESOURCE, ZoneMessage, path='zones', http_method='GET', name='zones.getRequestedZones')
    def locations_get(self, request):
        """
        API that returns specified zones or all zones...
        """
        return generateZoneMessage(request.zone)

    RAWDATA_RESOURCE = endpoints.ResourceContainer(message_types.VoidMessage,offset=messages.StringField(1,variant=messages.Variant.STRING),prefix=messages.StringField(2,variant=messages.Variant.STRING))
    @endpoints.method(RAWDATA_RESOURCE, Records, path='rawdata', http_method='GET', name='data.getRawData')
    def rawdata_get(self, request):
        """
        API that returns Raw data...
        """
        return getRawData(request.offset, "EAA")


APPLICATION = endpoints.api_server([AirupApi])
