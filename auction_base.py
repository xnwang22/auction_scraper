import argparse
import csv
from abc import ABC, abstractmethod, abstractproperty
from datetime import datetime, date


class AuctionBase:

    def __init__(self, *kwargs):
        pass
        # headers = {
        #     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
        # self.__dict__.update(kwargs)

    @abstractmethod
    def parse(self):
        raise NotImplementedError

    def report_csv(self, scraped_data):
        if scraped_data:
            time_now = date.today().isoformat()
            fn = f"{self.scraper_kw['site']}-{self.scraper_kw['search_keyword']}-scraped-{time_now}"
            csv_fn = fn+'.csv'
            print(f"Writing scraped data to {csv_fn}" )
            with open(csv_fn, 'w') as csvfile:
                fieldnames = ["title", "price", "url", "time_left", "bids"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                writer.writeheader()
                for data in scraped_data:
                    writer.writerow(data)
        else:
            print("No data scraped")

    def report_html(self):
        pass

    @classmethod
    def run(cls):
        argparser = argparse.ArgumentParser()
        argparser.add_argument('brand', help='search keyword')
        argparser.add_argument('-l', '--low', type=int, required=False, default=0, help='low price')
        argparser.add_argument('-hi', '--high', type=int, required=False, default=1000, help='high price')
        argparser.add_argument('-b', '--bids', type=int, required=False, default=0, help='number bids')
        argparser.add_argument('-t', '--time', type=str, required=False, default='1d', help='time left')
        args = argparser.parse_args()
        brand = args.brand
        low = args.low
        high = args.high
        bids = args.bids
        time_left = args.time

        scraped_data = cls.parse(brand, low, high, bids, time_left)

