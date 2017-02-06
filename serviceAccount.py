import json

from httplib2 import Http

from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build

scopes = ['https://www.googleapis.com/auth/fusiontables']

credentials = ServiceAccountCredentials.from_json_keyfile_name('airupBackend-b120f4cbc1a7.json', scopes)

fusiontablesadmin = build('fusiontables', 'v2', credentials=credentials)
# INSERT INTO 1e7y6mtqv892222222222_bbbbbbbbb_CvWhg9gc (Product, Inventory) VALUES ('Red Shoes', 25);
print(fusiontablesadmin.query().sql(sql="INSERT INTO 1VQ8VQZwKY7zjrTqAxQTtlYdt18bjsbU7Gx4_nyK7 ('Source ID','index','Date','Pos') VALUES ('ZZZ', 22, '2015-01-13', '53.592354,10.053774') ").execute())
#print(fusiontablesadmin.query().sql(sql='SELECT * FROM 1VQ8VQZwKY7zjrTqAxQTtlYdt18bjsbU7Gx4_nyK7').execute())