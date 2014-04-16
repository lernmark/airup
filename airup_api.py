# coding=utf-8
"""Hello World API implemented using Google Cloud Endpoints.

Defined here are the ProtoRPC messages needed to define Schemas for methods
as well as those methods defined in an API.
"""

import logging
import endpoints
from google.appengine.ext import db
from google.appengine.api import taskqueue
from protorpc import messages
from protorpc import message_types
from protorpc import remote
import datetime
import time

package = 'Airup'



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


class RecordCollection(messages.Message):
    """Collection of Records."""
    records = messages.MessageField(Record, 1, repeated=True)    

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

@endpoints.api(name='airup', version='v1')
class AirupApi(remote.Service):
    """Airup API v1."""

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



    MULTIPLY_METHOD_RESOURCE = endpoints.ResourceContainer(Record)
    @endpoints.method(MULTIPLY_METHOD_RESOURCE, Record, path='queueIt', http_method='POST', name='records.queueRecord')
    def records_queueRecord(self, request):
        """Use this method to post records"""
        
        timestamp = request.timestamp
        if not timestamp:
            # now = datetime.datetime.now()
            # timestamp = now.strftime("%Y-%m-%dT%H:%M:%S")
            # timestamp=int(now)
            timestamp = float(time.time())
        pm10 = request.pm10
        co = request.co
        no2 = request.no2
        ttt = datetime.datetime.now()
        #index = request.index
        #indexLabel = request.indexLabel
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

APPLICATION = endpoints.api_server([AirupApi])