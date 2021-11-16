import argparse
import csv
from abc import ABC, abstractmethod, abstractproperty

from ebay import Ebay

scraper_map = {'ebay': Ebay}


class ScraperFactory:

    @staticmethod
    def create_scraper(name, keywords):
        return scraper_map[name](keywords)
