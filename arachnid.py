"""
Arachnid is a web crawler that is going to be awesome.

Arachnid will go through a given domain and find all resources that is hosted within it and generate a network graph data structure. 

Each function should be short, simple, and do one thing well.

"""


import os
import requests
import sys
import urlparse 


from BeautifulSoup import BeautifulSoup
from requests import async

import networkx as nx



class Resource():
	"""
	This class will (hopefully) handle a single URL resource aka a web page, image, css file, etc.
	"""
	def __init__(url, content, **kwargs):
		self.url = url
		self.content = content
		for x,y in kwargs: 
			self.__setattr__(x,y) 

class Web():
	"""Main Web class that will handle just about everything that has to do with the crawled web"""
	def __init__(self):
		self.web = create_web()

	def create_web(): 
		"""This function creates the networkx graph object

			Put this into a function as I'm not sure if there are other variables we might want or options 
			depending on certain situations

		"""	
		G = nx.Graph()

		return G

	def create_node(resource_object):
		"""This function will create a node where the node data is the resource object for that resource

			AKA : http://example.com/index.html 

			self.web.create_node(Resource('http://example.com/index.html'))

		"""
		self.web.add_node(resource_object)
		return True

	def find_anchor_urls(raw_html):
		"""
		This function pulls the links out of anchor tags which have an 'href' attribute
		"""
		#"Soups" the html
		soup = BeautifulSoup(raw_html)

		#Uses BeautifulSoup to go through the page and grab all the hrefs if the tag has the attribute and the scheme is 'http'
		#page_links = [x['href'] for x in soup.findAll('a') if x.has_key('href') and urlparse(x['href']).scheme == 'http']
		page_links = []

		#For each anchor tag found in the html
		for x in soup.findAll('a'):
			#If the tag has the attr 'href' and the scheme of the url is 'http'  
			if x.has_key('href') and urlparse(x['href']).scheme == 'http':
				#Append the url to the list
				page_links.append(x['href'])

		return page_links

	def find_src_urls(raw_html):
		"""
		This function will go through link tags, img tags (and others?) to find tags which have the 'src' attribute
		"""
		return 

	def crawler(url):
		"""The main crawler function that will do the requests"""

		r = requests.get(url)

		#Need to check for redirect somewhere in here
		page = Resource(r.url, r.content)

		self.create_node(page)

		#Exits currently if the status code returns a 404. 
		if r.status_code != 200:
			print 'Need to handle other responses'
			sys.exit()

		page_links = find_anchor_urls(page.content)

		#This line creates a list of get requests objects (objects not yet sent)
		rs = [async.get(u) for u in page_links]

		#now we have a list of response objects, the data has gone and been collected
		responses = async.map(rs)

	







) __name__ == '__main__':
	if sys.argv[1]: 
		crawler(sys.argv[1])

