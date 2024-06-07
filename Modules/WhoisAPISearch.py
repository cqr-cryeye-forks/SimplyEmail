#!/usr/bin/env python

import requests
import configparser
import logging
from Helpers import Parser, helpers


class ClassName:
    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "Searching Whois"
        self.description = "Search the Whois database for potential POC emails"
        self.domain = domain
        self.verbose = verbose
        self.results = ""

        config = configparser.ConfigParser()
        self.logger = logging.getLogger("SimplyEmail.WhoisAPISearch")
        try:
            config.read('Common/SimplyEmail.ini')
            self.user_agent = config['GlobalSettings']['UserAgent']
        except KeyError as e:
            self.logger.critical(f'WhoisAPISearch module failed to __init__: {e}')
            print(helpers.color(" [*] Major Settings for Search Whois are missing, EXITING!\n", warning=True))

    def execute(self):
        self.logger.debug("WhoisAPISearch Started")
        self.process()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def process(self):
        try:
            if self.verbose:
                msg = ' [*] Requesting API on HackerTarget whois'
                self.logger.info("Requesting API on HackerTarget whois")
                print(helpers.color(msg, firewall=True))
            url = f"http://api.hackertarget.com/whois/?q={self.domain}"
            response = requests.get(url)
            response.raise_for_status()
            self.results = response.content
        except requests.RequestException as e:
            error_msg = f" [!] Major issue with Whois Search: {e}"
            self.logger.error(f"Failed to request URL (Check Connection): {e}")
            print(helpers.color(error_msg, warning=True))

    def get_emails(self):
        parser = Parser.Parser(self.results)
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        self.logger.debug('WhoisAPISearch completed search')
        return final_output, html_results, json_results
