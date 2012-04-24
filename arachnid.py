"""
Arachnid is a web crawler that is going to be awesome.

Arachnid will go through a given domain and find all resources that is hosted within it and generate a network graph data structure. 

Each function should be short, simple and do one thing well.

"""


import os
import requests
import sys

from datetime import datetime
from urlparse import urlparse, urljoin, urlunparse
from BeautifulSoup import BeautifulSoup
from requests import async

import matplotlib.pyplot as plt
import matplotlib
import networkx as nx




class Resource(object):
	"""
	This class will (hopefully) handle a single URL resource aka a web page, image, css file, etc.
	"""
	def __init__(self, url, content, **kwargs):
		self.url = url
		self.content = content
		print kwargs
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

		#r = redis.StrictRedis(host='localhost', port=6379, db=0)

		print "Getting the content of the first node"
		first_node_content = self.web.nodes()[0].content

		print "Pulling the links from the first node content"
		first_node_links = self.find_anchor_urls(first_node_content)
		print first_node_links

		print "Crawling the first links"
		#To finalize the initialization process, run crawler function with each anchor tag link found on the first_url given.
		map(self.crawler, first_node_links)

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

	def create_edge(self, obj, other_obj):

		self.web.add_edge(obj, other_obj)
		return True

	def find_anchor_urls(self,raw_html):
		"""
		This function pulls the links out of anchor tags which have an 'href' attribute
		"""
		#Solves "expected string or buffer" error
		if not raw_html: return []

		#"Soups" the html
		soup = BeautifulSoup(raw_html)

		#Uses BeautifulSoup to go through the page and grab all the hrefs if the tag has the attribute and the scheme is 'http'
		#page_links = [x['href'] for x in soup.findAll('a') if x.has_key('href') and urlparse(x['href']).scheme == 'http']
		page_links = []

		#For each anchor tag found in the html
		for x in soup.findAll('a'):
			#Check if it has an href
			if x.has_key('href') and not any(z in x['href'] for z in ['javascript', 'mailto']): 

				parsed_link = urlparse(x['href'])

				if parsed_link.scheme == '' or parsed_link.netloc == '':

					link = urljoin(self.first_url, x['href'])
						
					page_links.append(link)

				elif parsed_link.netloc == urlparse(self.first_url).netloc:
					link = x['href']

					#Append the url to the list
					page_links.append(link)

		#Cleaning
		for link in page_links:
			
			plink = urlparse(link)
			
			#Strip off the query string and fragment
			link = urlunparse(plink[:]).replace("?"+plink[4], "")

			#Strips the anchor fragment if it is found
			if link.find('#') != -1:
				link = link[:link.find('#')]

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

	def crawler(self,url, throttle = 5, url_limit = 100):
		"""The main crawler function that will do the requests

		Throttle: Value that limits number of concurrent requests that can be sent at any time

		url_limit: Limits the amount of resources to be added to the web, default 1000 just for
			debugging sake. 

		"""

		r = requests.get(url)

		#Need to check for redirect somewhere in here
		page = Resource(r.url, r.content)

		self.create_node(page)

		page_links = self.find_anchor_urls(page.content)

		#remove links already in the url_list from this list that is about to get crawled
		page_links = [x for x in page_links if x not in self.url_list]

		requests.defaults.defaults['pool_maxsize'] = 50
		requests.defaults.defaults['safe_mode'] = False
		requests.defaults.defaults['max_retries'] = 0

		try:
			#This line creates a list of get requests objects (objects not yet sent)
			rs = [async.get(u, prefetch=True) for u in page_links]

		except:
			#Attempts to recover from broken links within page_links
			print "Trying to recover from broken links"
			for p in page_links:
				pp = urlparse(p)
				if not all([p.scheme, p.netloc]):
					page_links.pop(p)
			print page_links
			rs = [async.get(u) for u in page_links]
		#now we have a list of response objects, the data has gone and been collected
		responses = async.map(rs, size=throttle)

		for resp in responses:
			print "Here is the url | %s" %(resp.url)
			print "And here is the list length | %s" % (self.url_list.__len__())
			if resp.url not in self.url_list:
				resource = Resource(resp.url, resp.__dict__)
				print "Adding %s" % (resp.url)
				self.url_list.append(resp.url)
				self.create_node(resource)

		links = map(self.find_anchor_urls, [r.content for r in responses])

		print "Crawl initiate! \n"
		if self.url_list.__len__() < url_limit: 
			try:
				map(self.crawler, links)
			except:
				print "Error somewhere =("
				for r in links:
					self.crawler(r)



