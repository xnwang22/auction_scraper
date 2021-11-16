# This is a sample Python script.

import argparse
from pprint import pprint
from traceback import format_exc

import requests
import unicodecsv as csv
from lxml import html
import certifi
import urllib3
import datetime

from scraper_factory import ScraperFactory

http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where()
)


def parse(brand, low, high, bids, time_left):
    #23h 46m left
    #31 bids · Time left1d 22h left
    url = f'https://www.ebay.com/sch/i.html?_nkw={brand}&_sacat=0&_udlo={low}&_udhi={high}&_oaa=1&Original%252FReproduction=Antique%2520Original&_dcat=37933&_stpos=19403&_sadis=2000&LH_PrefLoc=99&_fspt=1&rt=nc&LH_Auction=1'
    # https://www.ebay.com/sch/i.html?_nkw=kangxi&_sacat=0&Original%252FReproduction=Antique%2520Original&_dcat=37933&LH_Auction=1&rt=nc&_udlo=5&_udhi=500
    # https://www.ebay.com/sch/i.html?_nkw=kangxi&_sacat=0&_udlo=5&_udhi=500&_oaa=1&Original%252FReproduction=Antique%2520Original&_dcat=37933&_stpos=19403&_sadis=2000&LH_PrefLoc=99&_fspt=1&rt=nc&LH_All=1
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
    failed = False

    # Retries for handling network errors
    for _ in range(5):
        print("Retrieving %s" % (url))
        response = http.request('GET', url, headers=headers)
        parser = html.fromstring(response.data)
        print("Parsing page")

        if response.status != 200:
            failed = True
            continue
        else:
            failed = False
            break

    if failed:
        return []

    product_listings = parser.xpath('//li[contains(@class,"s-item")]')
    raw_result_count = parser.xpath("//h1[contains(@class,'count-heading')]//text()")
    result_count = ''.join(raw_result_count).strip()
    print("Found {0} for {1}".format(result_count, brand))
    scraped_products = []

    new_product_list = []
    for product in product_listings:
        raw_url = product.xpath('.//a[contains(@class,"s-item__link")]/@href')
        raw_title = product.xpath('.//h3[contains(@class,"s-item__title")]//text()')
        raw_product_type = product.xpath('.//h3[contains(@class,"s-item__title")]/span[@class="LIGHT_HIGHLIGHT"]/text()')
        raw_price = product.xpath('.//span[contains(@class,"s-item__price")]//text()')
        if not raw_price:
             continue
        price = ' '.join(' '.join(raw_price).split())
        if float(price.split('$')[1]) > high:
            continue
        title = ' '.join(' '.join(raw_title).split())
        product_type = ''.join(raw_product_type)
        title = title.replace(product_type, '').strip()
        raw_bids = product.xpath('.//span[contains(@class,"s-item__bids")]//text()')
        num_bids = ' '.join(' '.join(raw_bids).split())
        if not num_bids:
            continue
        num_bids = int(num_bids.replace(' bids', '').replace(' bid', ''))
        if num_bids > bids:
            continue
        time_remaining = product.xpath('.//span[contains(@class,"s-item__time-left")]//text()')
        time_remaining = time_remaining[0]
        time_remaining = time_remaining.replace(' left', '')
        time_end = product.xpath('.//span[contains(@class,"s-item__time-end")]//text()')
        time_end = time_end[0]

        days, hours, minutes=0,0,0

        if 'today' not in time_end:
            continue
        try:

            hours = int(time_remaining.split('h')[0])
            minutes = int(time_remaining.split('h')[1].split('m')[0].strip())
        except ValueError:
                #  no hours
            minutes = int(time_remaining.split('m')[0].strip())
        tm = datetime.timedelta(days=days, hours=hours, minutes=minutes)

        if 'd' in time_left:
            continue

        elif 'h' in time_left:
            tl = datetime.timedelta(hours=hours)
        else:
            tl = datetime.timedelta(minutes=int(time_left.split('m')[0]))
        if tm > tl:
            continue
        data = {
            'url': raw_url[0],
            'title': title,
            'price': price,
            'time_left': tm,
            'bids': bids
        }
        scraped_products.append(data)
    return scraped_products


if __name__ == "__main__":

    argparser = argparse.ArgumentParser()
    argparser.add_argument('-s', '--site', help = 'site to scrap', default='ebay')
    argparser.add_argument('-k', '--keyword', help='search keyword')
    argparser.add_argument('-lo', '--low', type=int, required=False, default=0, help='low price')
    argparser.add_argument('-hi', '--high', type=int, required=False, default=1000, help='high price')
    argparser.add_argument('-b', '--bids', type=int, required=False, default=0, help='number bids')
    argparser.add_argument('-t', '--time', type=str, required=False, default='1d', help='time left')

    args = argparser.parse_args()
    site = args.site
    if site not in ['ebay', 'ebth', 'ctbids', 'maxsold']:
        raise ValueError(f'{site} not supported')
    search_keyword = args.keyword
    low = args.low
    high = args.high
    bids = args.bids
    time_left = args.time
    scraper_kw={'site':site, 'search_keyword': search_keyword, 'low':low, 'high':high, 'bids':bids, 'time_left':time_left}
    print(scraper_kw)
    scraper = ScraperFactory.create_scraper(site, scraper_kw)
    scraped_data = scraper.parse()
    scraper.report_csv(scraped_data)
