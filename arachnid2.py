#!/usr/bin/env Python

import os
import requests
import sys
import re

from datetime import datetime
from urlparse import urlparse, urljoin, urlunparse

from BeautifulSoup import BeautifulSoup
import matplotlib.pyplot as plt
import matplotlib
import networkx as nx

class Web(object):
	def __init__(self, url, **kargs):
		self.first_url = url
		self.url_list = []
		self.web = nx.Graph()
		self.crawler(url)


	def find_anchor_urls(self,raw_html):
		"""
		This function pulls the links out of anchor tags which have an 'href' attribute
		"""
		#Solves "expected string or buffer" error
		if not raw_html: return []

		#"Soups" the html, try except statement in case html is badly formed
		try:
			soup = BeautifulSoup(raw_html)
		except:
			print "Shoddy html found"
			return []

		#Uses BeautifulSoup to go through the page and grab all the hrefs if the tag has the attribute and the scheme is 'http'
		#page_links = [x['href'] for x in soup.findAll('a') if x.has_key('href') and urlparse(x['href']).scheme == 'http']
		page_links = []
		_base = urlparse(self.first_url).netloc
		link = ''
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

		#Remove query strings and anchor fragments
		page_links = self.link_list_cleaner(page_links)		

		return page_links

	def link_list_cleaner(self,link_list):
		#Cleaning
		for link in link_list:
			
			plink = urlparse(link)
			
			#Strip off the query string and fragment
			link = urlunparse(plink[:]).replace("?"+plink[4], "")

			#Strips the anchor fragment if it is found
			if link.find('#') != -1:
				link = link[:link.find('#')]

		return link_list

	def draw_web(self):
		pos=nx.spring_layout(self.web, scale=100)
		nx.draw_networkx_nodes(self.web,pos,node_size=45)
		nx.draw_networkx_edges(self.web,pos)
		plt.axis('off')
		plt.savefig("test_web"+str(datetime.time(datetime.now()))+".png")

	def crawler(self, url):
		# Check is node has been created already, if so set the parent flag to true, else create node
		if self.web.has_node(url):
			self.web.node[url]['parent'] = 'True'
		else:
			self.web.add_node(url)
			self.web.node[url]['parent'] = 'True'

		# regex to just pull out the content type for html documents
		html_content = re.compile('text/html')
		# create a request for the current page content
		r = requests.get(url)
		# Assign the the content type to a variable so we can use it, as well as attaching it to the node
		content_type = r.headers['content-type']
		self.web.node[url]['content-type'] = html_content.findall(content_type)[0]
		self.web.node[url]['status-code'] = r.status_code
		self.web.node[url]['size'] = len(r.content)
		# Only scan text/html pages and assign the urls to a list
		if 'text/html' in html_content.findall(content_type):
			page_links = self.find_anchor_urls(r.content)

		for link in page_links:
			if self.web.has_node(link):
				self.web.add_edge(url,link)
				page_links.remove(link)
			else:
				self.web.add_node(link)
				self.web.add_edge(url,link)
			# print link

		# print self.web.nodes()
		return page_links

if __name__ == '__main__':
	test = Web('http://penny-arcade.com')
	test.draw_web()




