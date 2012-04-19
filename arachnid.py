"""
Arachnid is a web crawler that is going to be awesome.

Arachnid will go through a given domain and find all resources that is hosted within it and generate a network graph data structure. 

Each function should be short, simple and do one thing well.

"""


import os
import requests
import sys

from datetime import datetime
from urlparse import urlparse
from BeautifulSoup import BeautifulSoup
from requests import async

import matplotlib.pyplot as plt
import networkx as nx



class Resource(object):
	"""
	This class will (hopefully) handle a single URL resource aka a web page, image, css file, etc.
	"""
	def __init__(self, url, content, **kwargs):
		self.url = url
		self.content = content
		for key in kwargs: 
			self.__setattr__(key,kwargs[key]) 
	def __repr__(self):
		return "<Resource | %s>" % (self.url)

class Web(object):
	"""Main Web class that will handle just about everything that has to do with the crawled web"""
	
	def __init__(self, first_url):
		self.first_url = first_url
		self.web = self.init_web(first_url)
		self.url_list = []

		#To finalize the initialization process, run crawler function with each anchor tag link found on the first_url given.
		map(self.crawler, self.find_anchor_urls(self.web.nodes()[0].content))

	def init_web(self, first_url): 
		"""This function creates the networkx graph object

			Put this into a function as I'm not sure if there are other variables we might want or options 
			depending on certain situations

		"""	
		G = nx.Graph()

		r = requests.get(first_url)

		print r.url
		print r.__dict__

		res = Resource(r.url,r.content, response_dict=r.__dict__)

		G.add_node(res)

		return G	

	def create_node(self,resource_object):
		"""This function will create a node where the node data is the resource object for that resource

			AKA : http://example.com/index.html 

			self.web.create_node(Resource('http://example.com/index.html'))

		"""
		self.web.add_node(resource_object)
		return True

	def find_anchor_urls(self,raw_html):
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

			#Check if it has an href, if the scheme is http, and then if the domain is the same as the first link used to init Web.
			if x.has_key('href') and urlparse(x['href']).scheme == 'http' and urlparse(x['href']).netloc == urlparse(self.first_url).netloc:
				#Append the url to the list
				page_links.append(x['href'])

		return page_links

	def find_src_urls(self,raw_html):
		"""
		This function will go through link tags, img tags (and others?) to find tags which have the 'src' attribute
		"""
		return 

	def create_show_graph(self):
		pos=nx.spring_layout(self.web)
		nx.draw_networkx_nodes(self.web,pos,node_size=1000)
		nx.draw_networkx_edges(self.web,pos)
		plt.axis('off')
		plt.savefig("test_web"+str(datetime.time(datetime.now()))+".png")

	def crawler(self,url):
		"""The main crawler function that will do the requests"""

		r = requests.get(url)

		#Need to check for redirect somewhere in here
		page = Resource(r.url, r.content)

		self.create_node(page)

		#Exits currently if the status code returns a 404. 
		if r.status_code != 200:
			print 'Need to handle other responses'
			sys.exit()

		page_links = self.find_anchor_urls(page.content)

		#This line creates a list of get requests objects (objects not yet sent)
		rs = [async.get(u) for u in page_links]

		#now we have a list of response objects, the data has gone and been collected
		responses = async.map(rs, size=6)

		for resp in responses:
			if resp.url not in self.url_list:
				resource = Resource(resp.url, resp.__dict__)
				self.url_list.append(resp.url)
				print resource
				self.create_node(resource)
			 
		#map(self.crawler, [r.url for r in responses])
	


if __name__ == '__main__':
	if sys.argv[1]: 
		crawler(sys.argv[1])

