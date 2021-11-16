# This is a sample Python script.

import argparse
import re
from pprint import pprint
from traceback import format_exc

import requests
import unicodecsv as csv
from lxml import html
import certifi
import urllib3
import datetime

from auction_base import AuctionBase

http = urllib3.PoolManager(
    cert_reqs='CERT_REQUIRED',
    ca_certs=certifi.where()
)


class Ebay(AuctionBase):
    def __init__(self, kwargs):
        self.scraper_kw = kwargs
        self.url = f"https://www.ebay.com/sch/i.html?_nkw={self.scraper_kw['search_keyword']}&_sacat=0&_udlo={self.scraper_kw['low']}&_udhi={self.scraper_kw['high']}" \
                   f"&_oaa=1&Original%252FReproduction=Antique%2520Original&_dcat=37933&_stpos=19403&_sadis=2000&LH_PrefLoc=99&_fspt=1&rt=nc&LH_Auction=1"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}

    def parse(self):
        # 23h 46m left
        # 31 bids · Time left1d 22h left
        # url = f'https://www.ebay.com/sch/i.html?_nkw={search_key}&_sacat=0&_udlo={low}&_udhi={high}&_oaa=1&Original%252FReproduction=Antique%2520Original&_dcat=37933&_stpos=19403&_sadis=2000&LH_PrefLoc=99&_fspt=1&rt=nc&LH_Auction=1'
        # https://www.ebay.com/sch/i.html?_nkw=kangxi&_sacat=0&Original%252FReproduction=Antique%2520Original&_dcat=37933&LH_Auction=1&rt=nc&_udlo=5&_udhi=500
        # https://www.ebay.com/sch/i.html?_nkw=kangxi&_sacat=0&_udlo=5&_udhi=500&_oaa=1&Original%252FReproduction=Antique%2520Original&_dcat=37933&_stpos=19403&_sadis=2000&LH_PrefLoc=99&_fspt=1&rt=nc&LH_All=1
        # headers = {
        #     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
        failed = False

        # Retries for handling network errors
        for _ in range(5):
            print("Retrieving %s" % (self.url))
            response = http.request('GET', self.url, headers=self.headers)
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
        print("Found {0} for {1}".format(result_count, self.scraper_kw['search_keyword']))
        scraped_products = []

        new_product_list = []

        for product in product_listings:
            raw_url = product.xpath('.//a[contains(@class,"s-item__link")]/@href')
            raw_title = product.xpath('.//h3[contains(@class,"s-item__title")]//text()')
            raw_product_type = product.xpath(
                './/h3[contains(@class,"s-item__title")]/span[@class="LIGHT_HIGHLIGHT"]/text()')
            raw_price = product.xpath('.//span[contains(@class,"s-item__price")]//text()')
            if not raw_price:
                continue
            price = ' '.join(' '.join(raw_price).split())
            if float(price.split('$')[1]) > self.scraper_kw['high']:
                continue
            title = ' '.join(' '.join(raw_title).split())
            product_type = ''.join(raw_product_type)
            title = title.replace(product_type, '').strip()
            raw_bids = product.xpath('.//span[contains(@class,"s-item__bids")]//text()')
            num_bids = ' '.join(' '.join(raw_bids).split())
            if not num_bids:
                continue
            num_bids = int(num_bids.replace(' bids', '').replace(' bid', ''))
            if num_bids > self.scraper_kw['bids']:
                continue
            time_remaining = product.xpath('.//span[contains(@class,"s-item__time-left")]//text()')
            time_remaining = time_remaining[0]
            time_remaining = time_remaining.replace(' left', '')
            days, hours, minutes = 0, 0, 0
            # time_end = product.xpath('.//span[contains(@class,"s-item__time-end")]//text()')
            # print(f'time-end = {time_end}')
            # if not time_end:
            #     continue

            # time_end = time_end[0]

            days, hours, minutes=0,0,0

            # if 'today' not in time_end:
            #     continue

            m=re.match(r'(\d+d)?\s?(\d+h)?\s?(\d+m)?', time_remaining)
            if m.groups()[0]:
                days=int(m.groups()[0].split('d')[0])
            if m.groups()[1]:
                hours=int(m.groups()[1].split('h')[0])
            if m.groups()[2]:
                minutes=int(m.groups()[2].split('m')[0])

            tm = datetime.timedelta(days=days, hours=hours, minutes=minutes)

            time_frame= self.scraper_kw['time_left']
            if 'd' in time_frame:
                tl = datetime.timedelta(days=int(time_frame.split('d')[0]))

            elif 'h' in time_frame:
                tl = datetime.timedelta(hours=int(time_frame.split('h')[0]))
            else:
                tl = datetime.timedelta(days=int(time_frame.split('m')[0]))
            if tm > tl:
                continue

            data = {
                'url': raw_url[0],
                'title': title,
                'price': price,
                'time_left': tm,
                'bids': num_bids
            }
            scraped_products.append(data)
        # except Exception as e:
        #     print(f'{type(e)}: {str(e)}')
        # finally:
            return scraped_products
