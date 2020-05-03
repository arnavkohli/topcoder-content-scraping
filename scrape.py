import time
from datetime import datetime

import json
import pandas as pd

import requests

from bs4 import BeautifulSoup as bs


class HpScrapingBot:
	def __init__(self):

		self._product_ids = []
		self._products = []
		self._products_one_by_one = []

		self._id_to_url_map = {}

		self._headers = {
			'User-Agent' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
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


	def get_products_data(self):
		scriptRunStart = datetime.now()

		url = self._hpservices_base_url_multiple.format('%2C'.join(self._product_ids))
		all_data = requests.get(
			url=url,
			headers = self._headers
		).json()

		prices = all_data['priceData']
		inventory = all_data['inventoryData']

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

	def get_product_listings(self):
		scriptRunStart = datetime.now()

		for pid in self._product_ids:
			url = self._hpservices_base_url_single.format(pid)
			all_data = requests.get(
				url=url,
				headers = self._headers
			).json()

			price = all_data['priceData'][0]
			inventory = all_data['inventoryData'][0]

			eyed = inventory['productId']
			self._products_one_by_one.append({
				"productName" : inventory['prodName'],
				"productURL" : self._base + self._id_to_url_map[eyed],
				"productPrice" : price['price'],
				"productID" : eyed
			})


		self._run_time_to_get_products_one_by_one = (datetime.now() - scriptRunStart).seconds
		print (f"\nTotal time to get data one by one: {self._run_time_to_get_products_one_by_one} seconds\nProducts : {len(self._product_ids)}")




	def get_product_ids_and_urls(self, url):
		scriptRunStart = datetime.now()

		start_index = 0
		while True:
			html = requests.get(
				url=self._finder_base_url.format(start_index),
				headers = self._headers
			).text

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

	def run(self, url):
		self.get_product_ids_and_urls(url)
		self.get_products_data()
		self.get_product_listings()

		df = pd.DataFrame(self._products)
		df.to_excel('productListings.xlsx')
		print (f"\nCreated `productListings.xlsx`")

		df = pd.DataFrame(self._products_one_by_one)
		df.to_excel('products.xlsx')
		print (f"Created `products.xlsx`")
		print (f"\nTotal run time: {self._run_time_to_get_product_ids + self._run_time_to_get_all_products + self._run_time_to_get_products_one_by_one}")

if __name__ == '__main__':
	url = "https://store.hp.com/us/en/vwa/printers"
	bot = HpScrapingBot()
	bot.run(url)
	
