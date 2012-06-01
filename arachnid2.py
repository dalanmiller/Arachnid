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

# def url_getter(url, root_url):
#     """
#     Method used to send tasks to the queue
#     """
#     if "#" in url:
#         print '# found!', url
#     r = requests.get(url)

#     if 'text/html' in r.headers['content-type']:
#         return find_anchor_urls(r.content, root_url = root_url)
#     else:
#         return []

def crawler(url, first_url = None):
    """
    New function for crawling a url

    * Need to reintegrate the crawler method into this function
    * Commented out most of the node-ing and edge-ing 
    """
    print "Crawling:", url

    # Check is node has been created already, if so set 
    #the parent flag to true, else create node
    page_links = []
    # if self.web.has_node(url):
    #     self.web.node[url]['parent'] = 'True'
    # else:
    #     self.web.add_node(url)
    #     self.web.node[url]['parent'] = 'True'

    # create a request for the current page content
    r = requests.get(url)

    # Assign the the content type to a variable so we can use it,
    # as well as attaching it to the node
    content_type = r.headers['content-type']

    # self.web.node[url]['content-type'] = content_type

    # self.web.node[url]['status-code'] = r.status_code

    # self.web.node[url]['size'] = len(r.content)

    # Only scan text/html pages and assign the urls to a list
    if 'text/html' in html_content.findall(content_type):
        page_links = find_anchor_urls(r.content, root_url = first_url)


        return page_links
    else:
        return []
            
            # if self.web.has_node(link):
            #     self.web.add_edge(url, link)
            #     page_links.remove(link)
            # else:
            #     self.web.add_node(link, parent='False')
            #     self.web.add_edge(url, link)

                # THIS IS WHERE WE WILL SEND EACH LINK TO THE QUEUE
                #print "Adding link to queue", link
                # self.queue.put(self.q.enqueue(url_getter, link, self.first_url)) # put(self.url_getter(link))


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
        self.q =  Queue() 
        self.queue = Cue.Queue()
        self.init_graph()

    def init_graph(self):

        first_links = crawler(self.first_url, self.first_url)

        for link in first_links:
            #First links is the set of links foudn on the first page crawled
            #This adds a tuple into the queue that contains the link in the first index
            #And the crawler job created to crawl that link in the second index.
            if not self.web.has_node(link):
                self.web.add_node(link, parent='False')
                # THIS IS WHERE WE WILL SEND EACH LINK TO THE QUEUE
                print "Adding link to queue", link
                self.queue.put( (link, self.q.enqueue(crawler, link, self.first_url)) )
            self.web.add_edge(self.first_url, link)
            
        while not self.queue.empty():
            task = self.queue.get() #Pull the topmost tuple on the queue. 
            link = task[0] #The link string in the first index of the tuple
            job = task[1] #The crawler object in the second index of the tuple
            # There should already be a node created if it got this far, but just in case
            # lets check and create on
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

                #Gets only unique urls
                found_links = set(job.return_value)
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


                # found_links = set(found_links)
                
                # #NODE CREATION AND EDGE CREATION SHOULD PROBABLY DONE HERE
                
                # for f in found_links:
                #     #For the list of cleaned links that the job returns after crawling a page, add each one
                #     #into the queue as a tuple ( 'link_url' , crawler_job_object ) 
                #     self.queue.put( (link, self.q.enqueue(crawler, f, self.first_url)) ) 
                    
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

    # def crawler(self, url):
    #     """
    #     Main crawling method
    #     """
    #     print "Crawling:", url

    #     # Check is node has been created already, if so set 
    #     #the parent flag to true, else create node
    #     page_links = []
    #     if self.web.has_node(url):
    #         self.web.node[url]['parent'] = 'True'
    #     else:
    #         self.web.add_node(url)
    #         self.web.node[url]['parent'] = 'True'

    #     # create a request for the current page content
    #     r = requests.get(url)

    #     # Assign the the content type to a variable so we can use it,
    #     # as well as attaching it to the node
    #     content_type = r.headers['content-type']

    #     self.web.node[url]['content-type'] = content_type

    #     self.web.node[url]['status-code'] = r.status_code

    #     self.web.node[url]['size'] = len(r.content)

    #     # Only scan text/html pages and assign the urls to a list
    #     if 'text/html' in html_content.findall(content_type):
    #         page_links = find_anchor_urls(r.content, root_url = self.first_url)

    #         #Only want this loop to run anyway if the content is html? 

    #         for link in page_links:
    #             if not self.web.has_node(link):
    #                 self.web.add_node(link, parent='False')
    #                 # THIS IS WHERE WE WILL SEND EACH LINK TO THE QUEUE
    #                 print "Adding link to queue", link
    #                 self.queue.put(self.q.enqueue(url_getter, link, self.first_url)) # put(self.url_getter(link))
                    
    #             self.web.add_edge(url, link)

if __name__ == '__main__':
    use_connection() #Connects to locally hosted Redis Server
    if sys.argv[1]:
        test = Web(sys.argv[1])
        test.draw_web()
    else:
        test = Web('http://penny-arcade.com')
        test.draw_web()