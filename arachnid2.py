def find_anchor_urls(raw_html):
	soup = BeautifulSoup(raw_html)

	for x in soup.findAll('a'):
		pass

def crawler(url):
	r = requests.get(url)

	page_links = find_anchor_urls(r.content)


