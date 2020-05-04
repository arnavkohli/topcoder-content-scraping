import requests

from bs4 import BeautifulSoup as bs

from pprint import pprint

import os
import json

class ProxyScraper:

	base = "https://free-proxy-list.net/"

	@classmethod
	def get_proxy_list(self):
		response = requests.get(url=self.base)
		page = response.text
		soup = bs(page, 'html.parser')

		proxy_list = []
		tr_elements = soup.find('table', attrs = {'id' : 'proxylisttable'}).find_all('tr')

		for tr in tr_elements[1:]:
			tds = tr.find_all('td')

			try:
				ip, port, is_https = tds[0].text, tds[1].text, tds[6].text
			except:
				continue

			if is_https == 'yes':
				proxy_list.append({
					"proxy" : f"{ip}:{port}","is_https" : True})
			else:
				proxy_list.append({"proxy" : f"{ip}:{port}","is_https" : False})

		with open(os.path.join(os.getcwd(), 'proxy-cache.json'), 'w') as f:
			json.dump(proxy_list, f, indent=4)
		
		return proxy_list

if __name__ == '__main__':
	proxy_list = ProxyScraper.get_proxy_list()
	pprint (proxy_list)
