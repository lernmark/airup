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
from bs4 import BeautifulSoup

url = "http://slb.nu/slbanalys/luften-idag/"
result = urlfetch.fetch(
    url,
    headers=headers,
    method='GET'
)

print result.content

html_doc = """
<html><head><title>The Dormouse's story</title></head>
<body>
<p class="title"><b>The Dormouse's story</b></p>

<p class="story">Once upon a time there were three little sisters; and their names were
<a href="http://example.com/elsie" class="sister" id="link1">Elsie</a>,
<a href="http://example.com/lacie" class="sister" id="link2">Lacie</a> and
<a href="http://example.com/tillie" class="sister" id="link3">Tillie</a>;
and they lived at the bottom of a well.</p>

<p class="story">...</p>
"""

soup = BeautifulSoup(html_doc, 'html.parser')

print soup.find_all('a')

#print(soup.prettify())
