#!/usr/bin/env python

import configparser
from Helpers import Download
from Helpers import Parser
from Helpers import helpers
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlickrSearch:
    def __init__(self, domain, verbose=False):
        self.name = "Searching Flickr"
        self.description = "Search the Flickr top relevant results for emails"
        self.domain = domain
        self.verbose = verbose
        self.results = ""
        self.user_agent = {'User-Agent': helpers.get_user_agent()}

        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.hostname = str(config['FlickrSearch']['Hostname'])
        except KeyError as e:
            logger.error(f"Major settings for FlickrSearch are missing: {e}")
            raise SystemExit(f"Major settings for FlickrSearch are missing: {e}")

    def execute(self):
        self.process()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def process(self):
        dl = Download.Download(verbose=self.verbose)
        try:
            url = f"https://www.flickr.com/search/?text=%40{self.domain}"
            raw_html = dl.requesturl(url, useragent=self.user_agent)
            self.results += raw_html
        except Exception as e:
            logger.error(f"Major issue with Flickr Search: {e}")

        if self.verbose:
            logger.info("FlickrSearch has completed")

    def get_emails(self):
        parser = Parser.Parser(self.results)
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        return final_output, html_results, json_results
