#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configparser
import logging
from Helpers import Download
from Helpers import Parser
from Helpers import helpers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClassName:
    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "Searching GitHubUser Search"
        self.description = "Search GitHubUser for emails using the user search function"
        self.domain = domain
        self.verbose = verbose
        self.html = ""
        self.user_agent = {'User-Agent': helpers.get_user_agent()}

        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.depth = int(config['GitHubUserSearch']['PageDepth'])
            self.counter = int(config['GitHubUserSearch']['QueryStart'])
        except KeyError as e:
            logger.error(f"Major settings for GitHubUserSearch are missing: {e}")
            raise SystemExit(f"Major settings for GitHubUserSearch are missing: {e}")

    def execute(self):
        self.search()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def search(self):
        dl = Download.Download(verbose=self.verbose)
        while self.counter <= self.depth and self.counter <= 100:
            helpers.mod_sleep(5)
            if self.verbose:
                logger.info(f"GitHubUser Search on page: {self.counter}")
            try:
                url = (f"https://github.com/search?p={self.counter}&q={self.domain}"
                       f"&ref=searchresults&type=Users&utf8=")
                response = dl.requesturl(url, useragent=self.user_agent, raw=True, timeout=10)
                response.raise_for_status()
                self.html += response.content
            except Exception as e:
                logger.error(f"Major issue with GitHubUser Search: {e}")
                break
            self.counter += 1

    def get_emails(self):
        parser = Parser.Parser(self.html)
        parser.generic_clean()
        parser.url_clean()
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        return final_output, html_results, json_results
