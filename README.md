# topcoder-content-scraping

### Performance:

- Total Run Time of script: **~8 seconds**
- Scraping URLS: **~5 seconds**
- Step 1 runtime: **~1 second** *(1 API call for all products)*
- Step 2 runtime: **~1 second** *(multiple async API calls for all products)*

### Technology Stack:

- Language: Python3
- Frameworks/Libraries: BeautifulSoup, pandas, requests

### Deployment Guide

- Download zip file and cd into folder
- Create virtual environment (macOS): `python3 -m venv env`
- Activate virtual environment (macOS): `source env/bin/activate`
- Install dependancies: `pip install requirements.txt`
- Run file: `python scrape.py`
- Options: `--use-random-proxies || --use-proxy=<PROXY_HERE> || --use-https (only use if HTTPS available for proxy; default is HTTP)`
- Logs would be displayed on the console and 2 new excels with product infos would be created in the same directory

### Findings:

- Requesting the page, waiting for it to render, scrolling, clicking `Load More` buttons is a very time consuming task. So I got hold of the URL (using dev tools on Chrome) which was accountable for the all the information on the listing page. It returns data with only the relevant information without any designs, hence rendering is quicker.
  - URL Base (without starting index, updated inscript dynamically): https://store.hp.com/us/en/Finder?storeId=10151&catalogId=10051&categoryId=88340&searchTerm=&searchType=&searchTermScope=&pageSize=50&isAjax=true&beginIndex={}&pagingOnly=true

 - Only downside was the URL didn't provide me with products' price details. I had a look at the `Network` console again and voila, there was another endpoint involved which was in charge of feeding in price details. After some more investigation I found out that the product pages also use the same endpoint but with a slight change in the request parameters.
  - EP URL for multiple products: "https://store.hp.com/us/en/HPServices?&action=pids&catentryId={}&modelId=&langId=-1&storeId=10151&catalogId=10051"
    - In the above, `catentryId` would be populated with product IDs in a single string and `action` would be `pid` to get all their info in JSON format and the request would be sent to retrieve all product data (price as well).
  - EP URL for single product: "https://store.hp.com/us/en/HPServices?&action=dip&catentryId={}&modelId=&langId=-1&storeId=10151&catalogId=10051"
     - In the above, `catentryId` param would be the product ID and the `action` would be `dip`

### Strategy

- Now that I had the API responsible for the data, the only thing left was to get hold of the product IDs and call that API
- Calling the first URL in a loop by incrementing `start_index` by `50` till no results retrieved and saving the product Ids listed on the page (`50` is the page limit even if we increase the `pageLimit` param to <50)
- Case 1: Get all products at once (equivalent to Step 1)
  - Call the API once and get all products data
- Case 2: Get products one by one (equivalent to Step 2)
  - As all product pages request the API with `action` param set to `dip`, the script calls the API once for each product ID  asynchronously and saves the product data
- Save data in excels.




 
