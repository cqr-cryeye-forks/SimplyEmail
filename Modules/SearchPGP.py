#!/usr/bin/env python
import requests
import configparser
import logging
from Helpers import Parser, helpers

class ClassName:
    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "Searching PGP"
        self.description = "Search the PGP database for potential emails"
        self.domain = domain
        self.results = ""
        self.verbose = verbose
        self.logger = logging.getLogger("SimplyEmail.SearchPGP")
        self.load_config()

    def load_config(self):
        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.server = config['SearchPGP']['KeyServer']
            self.hostname = config['SearchPGP']['Hostname']
            self.user_agent = config['GlobalSettings']['UserAgent']
        except KeyError as e:
            self.logger.critical(f'SearchPGP module failed to load: {e}')
            print(helpers.color("[*] Major Settings for SearchPGP are missing, EXITING!\n", warning=True))
            raise e

    def execute(self):
        self.logger.debug("SearchPGP started")
        self.process()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def process(self):
        url = f"http://{self.server}/pks/lookup?search={self.domain}&op=index"
        headers = {'User-Agent': self.user_agent}
        try:
            self.logger.info("Requesting PGP keys")
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            self.results = response.content
            if self.verbose:
                print(helpers.color(' [*] Searching PGP Complete', firewall=True))
                self.logger.info("SearchPGP Completed search")
        except requests.RequestException as e:
            error = f" [!] Major issue with PGP Search: {e}"
            self.logger.error(error)
            print(helpers.color(error, warning=True))

    def get_emails(self):
        parser = Parser.Parser(self.results)
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        self.logger.debug("SearchPGP completed search")
        return final_output, html_results, json_results
