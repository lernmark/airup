import urllib2, base64, json, tablib
urlLogin = 'https://api.foobot.io/v2/user/lars@wattsgard.se/login/'
urlDevice = 'https://api.foobot.io/v2/owner/lars@wattsgard.se/device/'
urlData = 'https://api.foobot.io/v2/device/%s/datapoint/2015-10-10T00:00:00/2015-10-30T00:00:00/0/'
print "test"
# First. Login and get the token
request = urllib2.Request(urlLogin)
base64string = base64.encodestring('%s:%s' % ("lars@wattsgard.se", "AirUp123")).replace('\n', '')
request.add_header("Authorization", "Basic %s" % base64string)
response = urllib2.urlopen(request)
token = response.info().getheader('X-AUTH-TOKEN')
print token
# 2 use the token to get all devices
request = urllib2.Request(urlDevice)
request.add_header("X-AUTH-TOKEN", token)
response = urllib2.urlopen(request)
devices = json.loads(response.read())
firstDevice = devices[0]['uuid']
print firstDevice
# using first device uuid get all data (within the dates)
request = urllib2.Request(urlData % firstDevice)
request.add_header("X-AUTH-TOKEN", token)
response = urllib2.urlopen(request)
fooData = response.read()
headers = ("s",
    "ugm3",
    "C",
    "pc",
    "ppm",
    "ppb",
    "%")
j = json.loads(fooData)
data=tablib.Dataset(*j['datapoints'], headers=headers)
print data.csv
open('people.xls', 'wb').write(data.xls)

# the data come in the format of one never ending string
# [float, float, xx, xx, .... ],[float, float, xx, xx, .... ]
#
# wanted outcome is 
# [float, float, xx, xx, .... ]
# [float, float, xx, xx, .... ]
#
# Possibly then replace the ],[ with a ]\n[
# //Lasse