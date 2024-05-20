#!/usr/bin/env python

import configparser
import time
import logging
from Helpers import Download, helpers, Parser


class ClassName:
    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "RedditPost Search for Emails"
        self.description = "Uses RedditPosts to search for emails, and parse the raw results ATM"
        self.domain = domain
        self.verbose = verbose
        self.html = ""
        self.logger = logging.getLogger("SimplyEmail.RedditPostSearch")
        self.load_config()

    def load_config(self):
        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.user_agent = {'User-Agent': helpers.get_user_agent()}
            self.limit = int(config['RedditPostSearch']['QueryLimit'])
            self.counter = int(config['RedditPostSearch']['QueryStart'])
        except KeyError as e:
            self.logger.critical(f"RedditPostSearch module failed to load: {e}")
            print(helpers.color(" [*] Major Settings for RedditPostSearch are missing, EXITING!\n", warning=True))
            raise e

    def execute(self):
        self.logger.debug("RedditPostSearch started")
        self.search()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def search(self):
        dl = Download.Download(self.verbose)
        while self.counter <= self.limit and self.counter <= 1000:
            time.sleep(1)
            if self.verbose:
                p = f' [*] RedditPost Search on result: {self.counter}'
                self.logger.debug(f"RedditPost Search on result: {self.counter}")
                print(helpers.color(p, firewall=True))
            try:
                url = (f"https://www.reddit.com/search?q=%40{self.domain}"
                       f"&restrict_sr=&sort=relevance&t=all&count={self.counter}&after=t3_3mkrqg")
                raw_html = dl.requesturl(url, useragent=self.user_agent)
                self.html += raw_html
            except Exception as e:
                error = f" [!] Fail during Request to Reddit (Check Connection): {e}"
                self.logger.error(f"Fail during Request to Reddit (Check Connection): {e}")
                print(helpers.color(error, warning=True))
            self.counter += 25

    def get_emails(self):
        parser = Parser.Parser(self.html)
        parser.generic_clean()
        parser.url_clean()
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        self.logger.debug("RedditPostSearch completed search")
        return final_output, html_results, json_results
