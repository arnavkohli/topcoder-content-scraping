import sys
import time
from datetime import datetime

import os
import json
import pandas as pd

import requests

from bs4 import BeautifulSoup as bs

import threading

import asyncio
import aiohttp

from proxy_scraper import ProxyScraper

import random

class HpScrapingBot:
	def __init__(self, use_random_proxies=False, given_proxy=False, proxy_https=False):
		self.use_random_proxies=use_random_proxies
		self.given_proxy = given_proxy
		self.proxy_https = proxy_https
		if self.given_proxy:
			print (f"Using proxy: {self.given_proxy}")
		elif self.use_random_proxies:
			try:
				self._proxy_list = iter(ProxyScraper.get_proxy_list())
			except:
				print ('Error getting fresh proxies, retrieving from cache.')
				try:
					self._proxy_list = iter(json.loads(open(os.path.join(os.getcwd(), 'proxy-cache.json'), 'rb').read()))
				except Exception as err:
					print (f'Error retrieving proxies from proxy-cache.json : {err}')
					exit(0)

		self._user_agent_list = json.loads(open(os.path.join(os.getcwd(), 'user-agents-list.json'), 'rb').read())
		self._headers = {
			'User-Agent' : random.choice(self._user_agent_list),
			'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
			'Cache-Control' : 'max-age=0',
			'Accept-Language': 'en-US,en;q=0.5',
			'Accept-Encoding': 'gzip, deflate, br',
			'Connection': 'keep-alive',
			'Referer' : 'https://apps.topcoder.com/forums/?module=Thread&threadID=955087&start=0',
			'sec-fetch-dest' : 'document',
			'sec-fetch-mode' : 'navigate',
			'sec-fetch-site' : 'same-origin',
			'sec-fetch-user' : '?1',
			'upgrade-insecure-requests' : '1'
		}
		self._finder_base_url = "https://store.hp.com/us/en/Finder?storeId=10151&catalogId=10051&categoryId=88340&searchTerm=&searchType=&searchTermScope=&pageSize=50&isAjax=true&beginIndex={}&pagingOnly=true"
		self._hpservices_base_url_multiple = "https://store.hp.com/us/en/HPServices?&action=pids&catentryId={}&modelId=&langId=-1&storeId=10151&catalogId=10051"
		self._hpservices_base_url_single = "https://store.hp.com/us/en/HPServices?&action=dip&catentryId={}&modelId=&langId=-1&storeId=10151&catalogId=10051"
		self._base = "https://store.hp.com/"

		self._product_ids = []
		self._products = []
		self._products_one_by_one = []

		self._id_to_url_map = {}

	def rotate_user_agent(self):
		self._headers['User-Agent'] = random.choice(self._user_agent_list)

	def next_proxy(self):
		return next(self._proxy_list)

	def get_products_data(self):
		scriptRunStart = datetime.now()

		url = self._hpservices_base_url_multiple.format('%2C'.join(self._product_ids))

		self.rotate_user_agent()
		kwargs = {"url" : url, "headers" : self._headers}

		if self.use_random_proxies:
			proxy = self.next_proxy()['proxy']
			kwargs['proxies'] = {'http' : proxy, 'https' : proxy}
		elif self.given_proxy:
			kwargs['proxies'] = {'http' : self.given_proxy, 'https' : self.given_proxy}

		try:
			all_data = requests.get(**kwargs).json()

			prices = all_data['priceData']
			inventory = all_data['inventoryData']
		except:
			print (f"There was an error in retrieving data from the API")
			return 

		total = len(inventory)

		count = 0
		while count < total:
			eyed = inventory[count]['productId']
			self._products.append({
				"productName" : inventory[count]['prodName'],
				"productURL" : self._base + self._id_to_url_map[eyed],
				"productPrice" : prices[count]['price'],
				"productID" : eyed
			})

			count += 1

		self._run_time_to_get_all_products = (datetime.now() - scriptRunStart).seconds
		print (f"\nTotal time to get all product data: {self._run_time_to_get_all_products} seconds\nProducts: {count}")


	def get_product_ids_and_urls(self, url):

		scriptRunStart = datetime.now()


		start_index = 0
		while True:

			self.rotate_user_agent()
			kwargs = {"url" : self._finder_base_url.format(start_index), "headers" : self._headers}
			if self.use_random_proxies:
				proxy = self.next_proxy()['proxy']
				kwargs['proxies'] = {'http' : proxy, 'https' : proxy}
			elif self.given_proxy:
				kwargs['proxies'] = {'http' : self.given_proxy, 'https' : self.given_proxy}

			try:

				html = requests.get(**kwargs).text
			except requests.exceptions.ProxyError:
				print ('Proxy connection error.')
				if self.use_random_proxies:
					print ('Trying again...')
					proxy = self.next_proxy()['proxy']
					kwargs['proxies'] = {'http' : proxy, 'https' : proxy}
					continue
				else:
					print ('Try another proxy or use random proxies option.')
					exit(0)
			#print (html)
			soup = bs(html, 'html.parser')
	
			productCards = soup.find_all('div', attrs = {'class' : 'productCard'})
			if len(productCards) == 0: break
			for pc in productCards:
				eyed = pc['id'].split('_')[-1]
				url = pc.find('h3').find('a')['href']
				self._product_ids.append(eyed)
				self._id_to_url_map[eyed] = url

			start_index += 50

		self._run_time_to_get_product_ids = (datetime.now() - scriptRunStart).seconds
		print (f"Total time to get product IDs & URLS: {self._run_time_to_get_product_ids} seconds\nTotal Ids extracted: {len(self._product_ids)}")

	async def get_product_json(self, client, id):
		url = self._hpservices_base_url_single.format(id)

		self.rotate_user_agent()
		kwargs = {"url" : url, "headers" : self._headers}
		if self.use_random_proxies:
			proxy_data = self.next_proxy()
			if proxy_data['is_https']:
				kwargs['proxy'] = f"https://{proxy_data['proxy']}"
			else:
				kwargs['proxy'] = f"http://{proxy_data['proxy']}"
		elif self.given_proxy:
			if self.proxy_https:
				kwargs['proxy'] = f"https://{self.given_proxy}"
			else:
				kwargs['proxy'] = f"http://{self.given_proxy}"

		resp = await client.request('GET', **kwargs)
		data = await resp.json(content_type='text/html')

		price = all_data['priceData'][0]
		inventory = all_data['inventoryData'][0]

		return {
			"productName" : inventory['prodName'],
			"productURL" : self._base + self._id_to_url_map[eyed],
			"productPrice" : price['price'],
			"productID" : eyed
		}


	async def get_product_listings(self):
		scriptRunStart = datetime.now()

		async with aiohttp.ClientSession() as session:
			product_listings = await asyncio.gather(
				*[self.get_product_json(client=session, id=pid) for pid in self._product_ids], 
				return_exceptions=True
			)
			self._products_one_by_one = product_listings


		self._run_time_to_get_products_one_by_one = (datetime.now() - scriptRunStart).seconds
		print (f"\nTotal time to get data one by one: {self._run_time_to_get_products_one_by_one} seconds\nProducts : {len(self._products_one_by_one)}")

	def run(self, url):
		scriptRunStart = datetime.now()

		self.get_product_ids_and_urls(url)
		if len(self._product_ids) == 0:
			print ('There was an error in retrieving data from the API. Your IP may have been blocked. Try again in sometime or run script with proxy options.')
			exit(0)

		self.get_products_data()
		asyncio.run(self.get_product_listings())
		print (f"\nTotal run time: {(datetime.now() - scriptRunStart).seconds}")

		df = pd.DataFrame(self._products)
		df.to_excel('productListings.xlsx')
		print (f"\nCreated `productListings.xlsx`")

		df = pd.DataFrame(self._products_one_by_one)
		df.to_excel('products.xlsx')
		print (f"Created `products.xlsx`")

if __name__ == '__main__':
	url = "https://store.hp.com/us/en/vwa/printers"
	args = sys.argv[1:]
	kwargs = {}
	for arg in args:
		if arg.startswith('--use-proxy='):
			kwargs['given_proxy'] = arg.split('--use-proxy=')[-1].strip()
			if kwargs['given_proxy'] == '':
				print (f"\nInvalid argument: {arg}\nValid args: --use-random-proxies || --use-proxy=<PROXY_HERE> || --use-https (only use if HTTPS available for proxy; default is HTTP)\n")
		elif arg == '--use-https':
			kwargs['proxy_https'] = True
		elif arg == '--use-random-proxies':
			kwargs['use_random_proxies'] = True
		else:
			print (f"\nInvalid argument: {arg}\nValid args: --use-proxy=<PROXY_HERE> || --use-https (only use if HTTPS available for proxy; default is HTTP)\n")
			exit(0)
	if 'given_proxy' in kwargs and 'use_random_proxies' in kwargs:
		print (f"Provide only one: `--use-proxy=<PROXY_HERE>` or `--use-random-proxies`")
		exit(0)
	elif 'given_proxy' not in kwargs and 'proxy_https' in kwargs:
		print ("Ignoring `--use-https` as no proxy is provided")

	bot = HpScrapingBot(**kwargs)
	bot.run(url)
	
