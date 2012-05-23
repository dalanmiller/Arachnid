#!/usr/bin/env Python

import os
import requests
import sys

from datetime import datetime
from urlparse import urlparse, urljoin, urlunparse

from BeautifulSoup import BeautifulSoup

class Web(object):
	def __init__(self, url, **kargs):
		self.first_url = url
		self.url_list = []
		self.crawler(self.first_url)


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

	def crawler(self, url):
		r = requests.get(url)
		page_links = self.find_anchor_urls(r.content)
		page_links = [x for x in page_links if x not in self.url_list]
		for links in page_links:
			print links

if __name__ == '__main__':
	test = Web('http://penny-arcade.com')




