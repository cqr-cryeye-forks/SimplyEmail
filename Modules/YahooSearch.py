#!/usr/bin/env python

import configparser
import requests
import time
import logging
from Helpers import helpers, Parser


class ClassName:
    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "Yahoo Search for Emails"
        self.description = "Uses Yahoo to search for emails, parses them out of the HTML"
        self.domain = domain
        self.verbose = verbose
        self.html = ""

        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.logger = logging.getLogger("SimplyEmail.YahooSearch")
            self.quantity = int(config['YahooSearch']['StartQuantity'])
            self.user_agent = {'User-Agent': helpers.get_user_agent()}
            self.limit = int(config['YahooSearch']['QueryLimit'])
            self.counter = int(config['YahooSearch']['QueryStart'])
            self.sleep = int(config['SleepConfig']['QuerySleep'])
            self.jitter = int(config['SleepConfig']['QueryJitter'])
        except KeyError as e:
            self.logger.critical(f'YahooSearch module failed to load: {e}')
            print(helpers.color("[*] Major Settings for YahooSearch are missing, EXITING!\n", warning=True))

    def execute(self):
        self.logger.debug("YahooSearch Started")
        self.search()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def search(self):
        while self.counter <= self.limit and self.counter <= 1000:
            time.sleep(self.sleep)
            if self.verbose:
                msg = f' [*] Yahoo Search on page: {self.counter}'
                self.logger.info(f"YahooSearch on page: {self.counter}")
                print(helpers.color(msg, firewall=True))

            url = f'https://search.yahoo.com/search?p={self.domain}&b={self.counter}&pz={self.quantity}'
            try:
                self.logger.debug(f"YahooSearch starting request on: {url}")
                response = requests.get(url, headers=self.user_agent)
                response.raise_for_status()
                self.html += response.content.decode('utf-8')
            except requests.RequestException as e:
                error_msg = f" [!] Fail during Request to Yahoo (Check Connection): {e}"
                self.logger.error("YahooSearch failed to request (Check Connection)")
                print(helpers.color(error_msg, warning=True))

            self.counter += 100
            # helpers.mod_sleep(self.sleep, jitter=self.jitter)

    def get_emails(self):
        parser = Parser.Parser(self.html)
        parser.generic_clean()
        parser.url_clean()
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        self.logger.debug('YahooSearch completed search')
        return final_output, html_results, json_results
