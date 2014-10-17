# coding=utf-8
"""Hello World API implemented using Google Cloud Endpoints.

Defined here are the ProtoRPC messages needed to define Schemas for methods
as well as those methods defined in an API.
"""

import logging
import endpoints
import urllib
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



class ZoneDetailPersist(db.Model):
    """Models an individual Record entry with content and date."""
    #timestamp = db.FloatProperty()
    title = db.StringProperty()
    subtitle = db.StringProperty()
    max24Hr = db.FloatProperty()
    min24Hr = db.FloatProperty()
    co = db.FloatProperty()
    no2 = db.FloatProperty()
    index = db.FloatProperty()
    #id = db.FloatProperty()


class Record(messages.Message):
    """Record that stores a message."""
    timestamp = messages.StringField(1)
    pm10 = messages.FloatField(2)
    co = messages.FloatField(3)
    no2 = messages.FloatField(4)
    index = messages.IntegerField(5)
    indexLabel = messages.StringField(6)
    position = messages.StringField(7)
    positionLabels = messages.StringField(8)
    sourceId = messages.StringField(9, required=True)

class TodayDetail(messages.Message):
    index = messages.FloatField(1)
    location = messages.StringField(2)

class TodayType(messages.Message):
    best = messages.MessageField(TodayDetail, 1, repeated=False)
    worst = messages.MessageField(TodayDetail, 2, repeated=False)

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


class ZoneMessage(messages.Message):
    key = messages.StringField(1)
    zones = messages.MessageField(ZoneDetail, 2, repeated=True)
    today = messages.MessageField(TodayType, 3, repeated=False)
    timestamp = messages.FloatField(4)


    #{"title": "Hornstull", "min24Hr": "111", "timestamp": "1404916639.81", "max24Hr": "333", "no2": "33", "index": "222", "co": "22"}

class RecordCollection(messages.Message):
    """Collection of Records."""
    records = messages.MessageField(Record, 1, repeated=True)

class ReportCollection(messages.Message):
    """Collection of Records."""
    reports = messages.MessageField(ZoneMessage, 1, repeated=True)

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

class JsonProperty(db.TextProperty):
    def validate(self, value):
        return value

    def get_value_for_datastore(self, model_instance):
        result = super(JsonProperty, self).get_value_for_datastore(model_instance)
        result = json.dumps(result)
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

#Static reference Data.
#
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
    print "---------------------------------"
    co=values["co"]
    pm10=values["pm10"]
    no2=values["no2"]

    f = 0
    coIndex = 0
    pm10Index = 0
    no2Index = 0

    if co:
        coIndex = index(tableCo, co, 10)
        f = f+1
        print coIndex

    if pm10:
        pm10Index = index(tablePm10, pm10, 1)
        f = f+1
        print pm10Index

    if no2:
        no2Index = index(tableNo2, no2, 1000)
        f = f+1
        print no2Index

    if f > 0:
        return (coIndex+pm10Index+no2Index)/f


@endpoints.api(name='airup', version='v1')
class AirupApi(remote.Service):
    """Airup API v1."""

    @endpoints.method(message_types.VoidMessage, ReportCollection,path='reports', http_method='GET',name='reports.listReports')
    def report_list(self, unused_request):
        #Return all stored reports

        entities = Report.all()
        entities = entities.fetch(10)
        rep = []
        for entity in entities:
            #print entity.obj # outputs the dictionary object
            rep.append(
                ZoneMessage(
                    name=entity.name,
                    report=entity.report
                    )
                )
        STORED_REPORTS = ReportCollection(reports=rep)
        return STORED_REPORTS

    @endpoints.method(message_types.VoidMessage, RecordCollection,path='records', http_method='GET',name='records.listRecords')
    def records_list(self, unused_request):
        #Return all stored records
        allRecords = db.GqlQuery("SELECT * FROM Records ORDER BY timestamp DESC")
        req = []
        for e in allRecords:
            req.append(
                Record(
                    sourceId=e.sourceId,
                    timestamp=str(e.timestamp),
                    position=str(e.position),
                    positionLabels=e.positionLabels,
                    index=e.index,
                    indexLabel=e.indexLabel,
                    pm10=e.pm10,
                    co=e.co,
                    no2=e.no2,
                    )
                )

        STORED_RECORDS = RecordCollection(records=req)
        return STORED_RECORDS


    MULTIPLY_METHOD_RESOURCE_ZONEDETAIL = endpoints.ResourceContainer(ZoneDetail)
    @endpoints.method(MULTIPLY_METHOD_RESOURCE_ZONEDETAIL, ZoneDetail, path='zone', http_method='POST', name='zones.saveZone')
    def zones_saveZone(self, request):
        print "Zonesave"
        index = request.index
        co = request.co
        no2 = request.no2
        title = request.title
        subtitle = request.subtitle
        max24Hr = request.max24Hr
        min24Hr = request.min24Hr
        timestamp = request.timestamp
        if not timestamp:
            timestamp = float(time.time())

        taskqueue.add(queue_name='recordQueue', url='/zoneWworker', params={
            'no2':no2,
            'co':co,
            'title':title,
            'subtitle':subtitle,
            'max24Hr':max24Hr,
            'min24Hr':min24Hr,
            'timestamp':timestamp,
            'index':index
            })

        return ZoneDetail()



    MULTIPLY_METHOD_RESOURCE = endpoints.ResourceContainer(Record)
    @endpoints.method(MULTIPLY_METHOD_RESOURCE, Record, path='queueIt', http_method='POST', name='records.queueRecord')
    def records_queueRecord(self, request):
        """Use this method to post records"""

        timestamp = request.timestamp
        if not timestamp:
            timestamp = float(time.time())
        pm10 = request.pm10
        co = request.co
        no2 = request.no2

        index = aqi({"co":co,"pm10":pm10,"no2":no2})

        logging.info("Index: " + index)

        position = request.position
        if not position:
            position = "52.37, 4.88"

        #positionLabels = request.positionLabels
        sourceId = request.sourceId

        taskqueue.add(queue_name='recordQueue', url='/worker', params={
            'sourceId': sourceId,
            'no2':no2,
            'pm10':pm10,
            'co':co,
            'timestamp':timestamp,
            'index':index,
            'position':position
            })
        return Record(timestamp=request.timestamp,position=request.position,sourceId=request.sourceId)


    # MULTIPLY_METHOD_RESOURCE = endpoints.ResourceContainer(Record,times=messages.IntegerField(2, variant=messages.Variant.INT32,required=True))
    # @endpoints.method(MULTIPLY_METHOD_RESOURCE, Record,path='hellogreeting/{times}', http_method='POST',name='records.multiply')
    # def records_multiply(self, request):
        # return Record(timestamp=request.timestamp, pm10=request.pm10)

    ID_RESOURCE = endpoints.ResourceContainer(message_types.VoidMessage,id=messages.IntegerField(1, variant=messages.Variant.INT32))
    @endpoints.method(ID_RESOURCE, Record,path='record/{id}', http_method='GET',name='records.getRecord')
    def record_get(self, request):
        try:
            return STORED_RECORDS.records[request.id]
        except (IndexError, TypeError):
            raise endpoints.NotFoundException('Record %s not found.' %
                                              (request.id,))


    ID_RESOURCE2 = endpoints.ResourceContainer(message_types.VoidMessage,id=messages.StringField(1, variant=messages.Variant.STRING))
    @endpoints.method(ID_RESOURCE2, ZoneMessage,path='zones/{id}', http_method='GET',name='zones.getReport')
    def report_get(self, request):
        try:
            res = db.GqlQuery("SELECT * FROM ZoneDetailPersist")

            zonesArr = []
            for r in res:
                print r.key().id()

                zonesArr.append(
                    ZoneDetail(
                        id=float(r.key().id()),
                        title=r.title,
                        subtitle=r.subtitle,
                        index=r.index + random.randint(0,20),
                        co=r.co + random.randint(0,9),
                        no2=r.no2 + random.randint(0,9),
                        min24Hr=r.min24Hr,
                        max24Hr=r.max24Hr
                        )
                    )

            return ZoneMessage(
                key=request.id,
                timestamp=float(time.time()),
                today= TodayType(best=TodayDetail(index=13.0, location="Antartica"), worst=TodayDetail(index=425.0, location="Beijing")),
                zones = zonesArr
                )            
        except (IndexError, TypeError):
            raise endpoints.NotFoundException('Report %s not found.' % (request.id,))

    LATLONG_RESOURCE = endpoints.ResourceContainer(message_types.VoidMessage,lat=messages.StringField(1, variant=messages.Variant.STRING),long=messages.StringField(2, variant=messages.Variant.STRING))
    @endpoints.method(LATLONG_RESOURCE, ZoneDetail, path='location/lat/{lat}/long/{long}', http_method='GET', name='report.getLocation')
    def location_get(self, request):
        return ZoneDetail(id=4793444555816960.0,title='Hornstull',subtitle='Stockholm, Sweden',index=200.0,co=24.0,no2=111.0,min24Hr=23.0,max24Hr=89.0,timestamp=float(time.time()))


    LOCATIONS_RESOURCE = endpoints.ResourceContainer(message_types.VoidMessage,zone=messages.FloatField(1,repeated=True))
    @endpoints.method(LOCATIONS_RESOURCE, ZoneMessage, path='zones', http_method='GET', name='zones.getRequestedZones')
    def locations_get(self, request):

        try:

            qArr = []
            for z in request.zone:
                qArr.append("KEY('ZoneDetailPersist'," + str(int(z)) + ")")

            res = db.GqlQuery("SELECT * FROM ZoneDetailPersist WHERE __key__ IN (" + ", ".join(qArr) + ")")
            
            zonesArr = []
            for r in res:

                zonesArr.append(
                    ZoneDetail(
                        id=float(r.key().id()),
                        title=r.title,
                        subtitle=r.subtitle,
                        index=r.index + random.randint(0,20),
                        co=r.co + random.randint(0,9),
                        no2=r.no2 + random.randint(0,9),
                        min24Hr=r.min24Hr,
                        max24Hr=r.max24Hr
                        )
                    )

            return ZoneMessage(
                timestamp=float(time.time()),
                today= TodayType(best=TodayDetail(index=13.0, location="Antartica"), worst=TodayDetail(index=425.0, location="Beijing")),
                zones = zonesArr
                )  


            return ZoneMessage()
        except (IndexError, TypeError):
            raise endpoints.NotFoundException(IndexError)



APPLICATION = endpoints.api_server([AirupApi])