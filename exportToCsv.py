import urllib2, base64, json, tablib
apikey = 'AIzaSyA1WnmUgVJtsGuWoyHh-U8zlKRcGlSACXU'
url1 = 'https://www.googleapis.com/fusiontables/v2/tables/1KxVV0wQXhxhMScSDuqr-0Ebf0YEt4m4xzVplKd4/columns?key=%s'
urlImportOld = 'https://www.googleapis.com/fusiontables/v2/tables/1VQ8VQZwKY7zjrTqAxQTtlYdt18bjsbU7Gx4_nyK7/import?key=%s'
urlImport = 'https://www.googleapis.com/upload/fusiontables/v2/tables/1VQ8VQZwKY7zjrTqAxQTtlYdt18bjsbU7Gx4_nyK7/import?key=%s'
print "FUSION TABLES: "

# Here is your client ID
# 100188396996-ek7lisaie6p3oo7g2r9frdjb2rn7gr1c.apps.googleusercontent.com
# Here is your client secret
# Lza2SyGUozyg9BbCloaKlzaC


#payload = {'username': 'bob', 'email': 'bob@bob.com'}
#r = requests.put("http://somedomain.org/endpoint", data=payload)


data = "asdasd,2015-12-22"
request = urllib2.Request(urlImport % apikey, data=data)
request.add_header("Content-Type", "application/octet-stream")
request.get_method = lambda: "POST"
response = urllib2.urlopen(request)
print response.read()
