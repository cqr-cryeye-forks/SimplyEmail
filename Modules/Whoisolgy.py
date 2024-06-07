#!/usr/bin/env python
import requests
import configparser
import logging
from Helpers import Parser, helpers


class ClassName:
    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "Searching Whoisology"
        self.logger = logging.getLogger("SimplyEmail.Whoisology")
        self.description = "Search the Whoisology database for potential POC emails"
        self.domain = domain
        self.verbose = verbose
        self.results = ""

        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.user_agent = {'User-Agent': helpers.get_user_agent()}
        except KeyError as e:
            self.logger.critical(f'Whoisology module failed to __init__: {e}')
            print(helpers.color("[*] Major Settings for Search Whoisology are missing, EXITING!\n", warning=True))

    def execute(self):
        self.logger.debug("Whoisology Started")
        self.process()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def process(self):
        try:
            if self.verbose:
                self.logger.info("Whoisology request started")
                msg = ' [*] Whoisology request started'
                print(helpers.color(msg, firewall=True))
            url = f"https://whoisology.com/archive_11/{self.domain}"
            response = requests.get(url, headers=self.user_agent)
            response.raise_for_status()
            self.results = response.content.decode('utf-8')  # Декодирование байтов в строку
        except requests.RequestException as e:
            error_msg = f"[!] Major issue with Whoisology Search: {e}"
            self.logger.error("Whoisology could not download source (Check Connection)")
            print(helpers.color(error_msg, warning=True))

    def get_emails(self):
        parser = Parser.Parser(self.results)
        parser.generic_clean()
        parser.url_clean()
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        self.logger.debug('Whoisology completed search')
        return final_output, html_results, json_results
