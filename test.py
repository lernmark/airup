import requests, base64, json
print "wow"

urlLogin = 'https://api.foobot.io/v2/user/lars@wattsgard.se/login/'
urlDevice = 'https://api.foobot.io/v2/owner/lars@wattsgard.se/device/'
urlData = 'https://api.foobot.io/v2/device/%s/datapoint/2015-10-10T00:00:00/2015-10-30T00:00:00/0/'

base64string = base64.encodestring('%s:%s' % ("lars@wattsgard.se", "AirUp123")).replace('\n', '')
resp = requests.get(urlLogin,headers={'Authorization': "Basic %s" % base64string})
resp2 = requests.get(urlLogin, auth=('lars@wattsgard.se', 'AirUp123'))
#token = resp.headers['X-AUTH-TOKEN']
#print token
print resp.headers
print resp2

print resp2.getcode()