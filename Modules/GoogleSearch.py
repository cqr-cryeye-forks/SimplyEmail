#!/usr/bin/env python

import configparser
import time
import logging
from Helpers.helpers import get_user_agent, mod_sleep
from Helpers.Parser import Parser
from Helpers.Download import Download


class ClassName(object):

    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "Google Search for Emails"
        self.description = "Uses Google to search for emails, parses them out of the results"
        self.verbose = verbose

        self._load_config()
        self.domain = domain
        self.html = ""

    def _load_config(self):
        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.quantity = int(config['GoogleSearch']['StartQuantity'])
            self.user_agent = {'User-Agent': get_user_agent()}
            self.limit = int(config['GoogleSearch']['QueryLimit'])
            self.counter = int(config['GoogleSearch']['QueryStart'])
            self.sleep = int(config['SleepConfig']['QuerySleep'])
            self.jitter = int(config['SleepConfig']['QueryJitter'])
        except KeyError as e:
            logging.error("Missing config setting: %s", e)
            raise

    def execute(self):
        self.search()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def search(self):
        dl = Download(self.verbose)
        while self.counter <= self.limit and self.counter <= 1000:
            time.sleep(1)
            if self.verbose:
                logging.info('Google Search on page: %d', self.counter)

            url = f"http://www.google.com/search?num={self.quantity}&start={self.counter}&hl=en&meta=&q=%40\"{self.domain}\""
            try:
                results = dl.requesturl(url, useragent=self.user_agent)
            except Exception as e:
                logging.error("Fail during request to Google: %s", e)
                continue

            try:
                dl.GoogleCaptchaDetection(results)
            except Exception as e:
                logging.warning("Captcha detection issue: %s", e)

            self.html += results
            self.counter += 100
            mod_sleep(self.sleep, jitter=self.jitter)

    def get_emails(self):
        parse = Parser(self.html)
        parse.generic_clean()
        parse.url_clean()
        final_output = parse.grep_find_emails()
        html_results = parse.build_results(final_output, self.name)
        json_results = parse.build_json(final_output, self.name)
        return final_output, html_results, json_results
