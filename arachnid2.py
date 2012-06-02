#!/usr/bin/env Python
import requests
import re
import sys
import time
import json

from datetime import datetime
from urlparse import urlparse, urljoin, urlunparse, urldefrag
from rq import use_connection, Queue
import Queue as Cue

from BeautifulSoup import BeautifulSoup
import matplotlib.pyplot as plt
import networkx as nx
from networkx.readwrite import json_graph

# regex to just pull out the content type for html documents
html_content = re.compile('text/html')

def link_list_cleaner(link_list):
    """
    Cleaning link function
    """
    link_list = set(link_list)
    #Cleaning
    for link in link_list:
        
        plink = urlparse(link)
        
        #Strip off the query string and fragment
        link = urlunparse(plink[:]).replace("?"+plink[4], "")

        #Strips the anchor fragment if it is found
        # if '#' in link:
        #     link = link[:link.find('#')]
        link = urldefrag(link)[0]

        #Remove the relative pathing
        if link.find('../') != -1:
            link = link.replace('../','')

    link_list = set(link_list)

    return link_list

def crawler(url, first_url = None):
    """
    New function for crawling a url

    * Need to reintegrate the crawler method into this function
    * Commented out most of the node-ing and edge-ing 
    """
    print "Crawling:", url

    page_links = []

    r = requests.get(url)

    content_type = r.headers['content-type']

    if 'text/html' in html_content.findall(content_type):
        page_links = find_anchor_urls(r.content, root_url = first_url)

        return (r.headers, r.content, page_links)
    else:
        return (r.headers, r.content, [])


def find_anchor_urls(raw_html, root_url=None):
    """
    This function pulls the links out of anchor tags which have an 'href' attribute
    """
    #Solves "expected string or buffer" error
    if not raw_html: 
        return []

    #"Soups" the html, try except statement in case html is badly formed
    try:
        soup = BeautifulSoup(raw_html)
    except:
        print "Shoddy html found"
        return []

    #Uses BeautifulSoup to go through the page and grab all 
    #the hrefs if the tag has the attribute and the scheme is 'http'
    #page_links = [x['href'] for x in soup.findAll('a') if 
    #x.has_key('href') and urlparse(x['href']).scheme == 'http']
    page_links = []
    _base = urlparse(root_url).netloc
    link = ''
    for x in soup.findAll('a'):
        #Check if it has an href
        if x.has_key('href') and not any(z in x['href'] for z in ['javascript', 'mailto']): 

            parsed_link = urlparse(x['href'])

            if parsed_link.scheme == '' or parsed_link.netloc == '':

                if '../' in x['href']:

                    link = urljoin(root_url, x['href'].replace('../',''))
                else:
                    link = urljoin(root_url, x['href'])
                    
                page_links.append(link)

            elif parsed_link.netloc == urlparse(root_url).netloc:
                link = x['href']

                #Append the url to the list
                page_links.append(link)

    #Remove query strings and anchor fragments and '../'
    page_links = link_list_cleaner(page_links)     

    return page_links

class Web(object):
    """
    Our Web Object
    """
    def __init__(self, url):
        self.first_url = url
        self.url_list = []
        self.web = nx.Graph()
        self.q = Queue() 
        self.queue = Cue.Queue()
        self.init_graph()

    def init_graph(self):

        first_headers, first_content, first_links = crawler(self.first_url, self.first_url)

        for link in first_links:
            #First links is the set of links found on the first page crawled
            #This adds a tuple into the queue that contains the link in the first index
            #And the crawler job created to crawl that link in the second index.

            if not self.web.has_node(link):
                self.web.add_node(link, parent='False')

                print "Adding link to queue", link

                self.queue.put( (link, self.q.enqueue(crawler, link, self.first_url)) )

            self.web.add_edge(self.first_url, link)
            
        while not self.queue.empty():

            task = self.queue.get() #Pull the topmost tuple on the queue. 

            link = task[0] #The link string in the first index of the tuple
            job = task[1] #The crawler object in the second index of the tuple

            # There should already be a node created if it got this far, but just in case
            # lets check and create one
            if not self.web.has_node(link):
                self.web.add_node(link)
            # Change parent flag to true
            self.web.node[link]['parent'] = 'True'

            print "queue length", self.queue.qsize()

            if job.return_value == None: #Job hasn't completed therefore return_value == None
                print "Not yet!", job.id 
                self.queue.put(task) #Put the tuple back into the list because it hasn't been processed yet
                time.sleep(0.10) #Wait a tenth of a second so we don't kill the computer

            else: #Job has completed, let's deal with the return_value
                print "Now mapping through a new set of links"

                headers = job.return_value[0] #These are the headers from the current value of the variable 'link'
                content = job.return_value[1] #This is the content from the current value of the variable 'link'

                if len(found_links) != 0: #The crawler returned links and therefore it was a text/html page

                    #Gets only unique urls
                    found_links = set(job.return_value[2])
                    #Removes the anchor tags
                    found_links = [urldefrag(x)[0] for x in found_links]
                    #Reduces to unique
                    found_links = set(found_links)
                    #Removes links that are not in the url_list or don't have a node already
                    found_links = [x for x in found_links if x not in self.url_list]
                
                    for flink in found_links:
                        if not self.web.has_node(flink):
                            self.web.add_node(flink, parent='False')
                            # THIS IS WHERE WE WILL SEND EACH LINK TO THE QUEUE
                            print "Adding link to queue", flink
                            self.queue.put( (link, self.q.enqueue(crawler, flink, self.first_url)) ) 
                        
                        self.web.add_edge(link, flink)

                else: 
                    #The crawler returned no links from the page meaning it was either an html page 
                    #with no links, or it wasn't text/html

                    #Adding nodes/edges for non-html pages should go in this else statement

                    
                #Add the urls found into a master list that can easily be checked to see
                #that we aren't duplicating a request for a URL we have already crawled
                map(self.url_list.append, found_links)
                
                #Print the length of the list of urls we have already crawled.
                print "URL list length", len(self.url_list)


    def draw_web(self, iterations = 10, color='b'):
        """
        Method which draws the Graph
        """
        pos = nx.spring_layout(self.web, iterations = iterations)
        nx.draw_networkx_nodes(self.web, pos, node_color=color, node_size=10)
        nx.draw_networkx_edges(self.web, pos)
        d = json_graph.node_link_data(self.web)
        json.dump(d, open('force/force.json','w'))
        plt.axis('off')
        plt.savefig("graph-"+str(datetime.time(datetime.now()))+".png")

if __name__ == '__main__':
    use_connection() #Connects to locally hosted Redis Server
    if sys.argv[1]:
        test = Web(sys.argv[1])
        test.draw_web()
    else:
        test = Web('http://penny-arcade.com')
        test.draw_web()