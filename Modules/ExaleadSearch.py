#!/usr/bin/env python

import configparser
import requests
import time
from Helpers import helpers
from Helpers import Parser
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClassName:
    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "Exalead Search for Emails"
        self.description = "Uses Exalead to search for emails and parses them out of the HTML"
        self.domain = domain
        self.verbose = verbose
        self.url_list = []
        self.text = ""

        config = configparser.ConfigParser()
        config.read('Common/SimplyEmail.ini')

        try:
            self.quantity = int(config['ExaleadSearch']['StartQuantity'])
            self.user_agent = {'User-Agent': helpers.get_user_agent()}
            self.limit = int(config['ExaleadSearch']['QueryLimit'])
            self.counter = int(config['ExaleadSearch']['QueryStart'])
        except KeyError as e:
            logger.error(f"Major settings for Exalead are missing: {e}")
            raise SystemExit(f"Major settings for Exalead are missing: {e}")

    def execute(self):
        self.search()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def search(self):
        while self.counter <= self.limit:
            time.sleep(1)
            if self.verbose:
                logger.info(f"Exalead Search on page: {self.counter}")

            url = (f'http://www.exalead.com/search/web/results/?q="%40{self.domain}"'
                   f'&elements_per_page={self.quantity}&start_index={self.counter}')
            try:
                response = requests.get(url, headers=self.user_agent)
                response.raise_for_status()
                raw_html = response.content
                self.text += raw_html
                soup = BeautifulSoup(raw_html, "lxml")
                self.url_list.extend(h2.a["href"] for h2 in soup.find_all('h4', class_='media-heading'))
            except requests.RequestException as e:
                logger.error(f"Fail during request to Exalead: {e}")
            except Exception as e:
                logger.error(f"Fail during parsing result: {e}")

            self.counter += 30

        for url in self.url_list:
            try:
                data = requests.get(url, timeout=2)
                data.raise_for_status()
                self.text += data.content
            except requests.RequestException as e:
                logger.error(f"Connection timed out on Exalead Search: {e}")

        if self.verbose:
            logger.info("Searching Exalead Complete")

    def get_emails(self):
        parser = Parser.Parser(self.text)
        parser.generic_clean()
        parser.url_clean()
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        return final_output, html_results, json_results
