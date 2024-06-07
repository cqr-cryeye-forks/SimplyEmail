#!/usr/bin/env python
# -*- coding: utf-8 -*-
import configparser
import logging
from bs4 import BeautifulSoup
from Helpers import Download
from Helpers import Parser
from Helpers import helpers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClassName:
    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "Searching GitHub Code"
        self.description = "Search GitHub code for emails using a large pool of code searches"
        self.domain = domain
        self.html = ""
        self.verbose = verbose
        self.user_agent = {'User-Agent': helpers.get_user_agent()}

        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.depth = int(config['GitHubSearch']['PageDepth'])
            self.counter = int(config['GitHubSearch']['QueryStart'])
        except KeyError as e:
            logger.error(f"Major settings for GitHubSearch are missing: {e}")
            raise SystemExit(f"Major settings for GitHubSearch are missing: {e}")

    def execute(self):
        self.process()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def process(self):
        dl = Download.Download(verbose=self.verbose)
        url_list = []

        while self.counter <= self.depth:
            if self.verbose:
                logger.info(f"GitHub Code Search on page: {self.counter}")
            try:
                url = f"https://github.com/search?p={self.counter}&q={self.domain}+&ref=searchresults&type=Code&utf8=✓"
                response = dl.requesturl(url, useragent=self.user_agent, raw=True, timeout=10)
                if response.status_code != 200:
                    break
            except Exception as e:
                logger.error(f"Major issue with GitHub Search: {e}")
                break

            raw_html = response.content
            soup = BeautifulSoup(raw_html, 'lxml')
            for a in soup.find_all('a', href=True):
                href = a['href']
                if href.startswith('/'):
                    url_list.append(href)
            self.counter += 1

        for url in url_list:
            try:
                full_url = f"https://github.com{url}"
                html = dl.requesturl(full_url, useragent=self.user_agent, timeout=10)
                self.html += html
            except Exception as e:
                logger.error(f"Connection Timed out on GitHub Search: {e}")

    def get_emails(self):
        parser = Parser.Parser(self.html)
        parser.generic_clean()
        parser.url_clean()
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        return final_output, html_results, json_results
