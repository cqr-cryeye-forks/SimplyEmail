#!/usr/bin/env python

import configparser
import requests
import time
import logging
from Helpers import Download, helpers, Parser
from bs4 import BeautifulSoup


class ClassName:
    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "PasteBin Search for Emails"
        self.description = "Uses pastebin to search for emails, parses them out of the"
        self.domain = domain
        self.verbose = verbose
        self.logger = logging.getLogger("SimplyEmail.PasteBinSearch")
        self.url_list = []
        self.text = ""
        self.load_config()

    def load_config(self):
        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.quantity = int(config['GooglePasteBinSearch']['StartQuantity'])
            self.user_agent = {'User-Agent': helpers.get_user_agent()}
            self.limit = int(config['GooglePasteBinSearch']['QueryLimit'])
            self.counter = int(config['GooglePasteBinSearch']['QueryStart'])
        except Exception as e:
            self.logger.critical(f'PasteBinSearch module failed to initialize: {e}')
            print(helpers.color("[*] Major Settings for PasteBinSearch are missing, EXITING!\n", warning=True))
            raise e

    def execute(self):
        self.logger.debug("PasteBinSearch started")
        self.search()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def search(self):
        dl = Download.Download(self.verbose)
        while self.counter <= self.limit and self.counter <= 100:
            time.sleep(1)
            if self.verbose:
                p = f' [*] Google Search for PasteBin on page: {self.counter}'
                self.logger.info(f"GooglePasteBinSearch on page: {self.counter}")
                print(helpers.color(p, firewall=True))
            url = f"http://www.google.com/search?num={self.quantity}&start={self.counter}&hl=en&meta=&q=site:pastebin.com+%40{self.domain}"
            try:
                response = requests.get(url, headers=self.user_agent)
                response.raise_for_status()
                raw_html = response.content
                dl.GoogleCaptchaDetection(raw_html)
                soup = BeautifulSoup(raw_html, "lxml")
                self.url_list.extend(a['href'] for a in soup.select('.r a') if "/u/" not in a['href'])
            except requests.RequestException as e:
                error = f" [!] Issue with Google Search for PasteBin: {e}"
                self.logger.error(error)
                print(helpers.color(error, warning=True))
            except Exception as e:
                error = f" [!] Fail during parsing result: {e}"
                self.logger.error(f"PasteBinSearch Fail during parsing result: {e}")
                print(helpers.color(error, warning=True))
            self.counter += 100
        self.gather_raw_content()

    def gather_raw_content(self):
        for url in self.url_list:
            try:
                raw_url = f"http://pastebin.com/raw/{url.split('/')[3]}"
                data = requests.get(raw_url, timeout=2)
                data.raise_for_status()
                self.text += data.content.decode('utf-8')
            except requests.RequestException as e:
                error = f"[!] Connection Timed out on PasteBin Search: {e}"
                self.logger.error(f"Connection Timed out on PasteBin raw download: {e}")
                print(helpers.color(error, warning=True))
        if self.verbose:
            p = ' [*] Searching PasteBin Complete'
            self.logger.info("Searching PasteBin Complete")
            print(helpers.color(p, firewall=True))

    def get_emails(self):
        parser = Parser.Parser(self.text)
        parser.generic_clean()
        parser.url_clean()
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        self.logger.debug("PasteBinSearch completed search")
        return final_output, html_results, json_results
