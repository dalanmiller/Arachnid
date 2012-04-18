"""
Arachnid is a web crawler that is going to be awesome.

Arachnid will go through a given domain and find all resources that is hosted within it. 

"""


import os
import requests
import sys
import urlparse 


from BeautifulSoup import BeautifulSoup
from requests import async

import networkx as nx



class Resource():
	def __init__(url, **kwargs):
		self.url = url
		for x,y in kwargs: 
			self.__setattr__(x,y) 

GLOBAL_WEB = {}

def crawler(url):


	r = requests.get(url)

	#Exits currently if the status code returns a 404. 
	if r.status_code != 200:
		print 'Need to handle other responses'
		sys.exit()

	#"Soups" the html
	soup = BeautifulSoup(r.content)

	#Uses BeautifulSoup to go through the page and grab all the hrefs if the tag has the attribute and the scheme is 'http'
	page_links = [x['href'] for x in soup.findAll('a') if x.has_key('href') and urlparse(x['href']).scheme == 'http']
	
	for x in page_links:
		if x not in GLOBAL_WEB.keys():

			rs = [async.get(u) for u in page_links]

			responses = async.map(rs)


if __name__ == '__main__':
	if sys.argv[1]: 
		crawler(sys.argv[1])

