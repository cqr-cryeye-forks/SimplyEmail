#!/usr/bin/env python

# Class will have the following properties:
# 1) name / description
# 2) main name called "ClassName"
# 3) execute function (calls everything it needs)
# 4) places the findings into a queue
import urllib.parse as urlparse
import configparser
import time
import logging
from Helpers import Download, helpers, Parser
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleCsvSearch:
    def __init__(self, domain, verbose=False):
        self.name = "Google CSV Search for Emails"
        self.description = "Uses Google Dorking to search for emails"
        self.domain = domain
        self.verbose = verbose
        self.url_list = []
        self.text = ""
        self.user_agent = {'User-Agent': helpers.get_user_agent()}

        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.quantity = int(config['GoogleCsvSearch']['StartQuantity'])
            self.limit = int(config['GoogleCsvSearch']['QueryLimit'])
            self.counter = int(config['GoogleCsvSearch']['QueryStart'])
            self.sleep = int(config['SleepConfig']['QuerySleep'])
            self.jitter = int(config['SleepConfig']['QueryJitter'])
        except KeyError as e:
            logger.error(f"Major settings for GoogleCsvSearch are missing: {e}")
            raise SystemExit(f"Major settings for GoogleCsvSearch are missing: {e}")

    def execute(self):
        self.search()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def search(self):
        dl = Download.Download(self.verbose)
        while self.counter <= self.limit and self.counter <= 100:
            time.sleep(1)
            if self.verbose:
                logger.info(f"Google CSV Search on page: {self.counter}")
            try:
                url = f"https://www.google.com/search?q=site:{self.domain}+filetype:csv&start={self.counter}"
                raw_html = dl.requesturl(url, useragent=self.user_agent)
                dl.GoogleCaptchaDetection(raw_html)
                soup = BeautifulSoup(raw_html, 'lxml')
                for a in soup.find_all('a'):
                    try:
                        l = urlparse.parse_qs(urlparse.urlparse(a['href']).query)['q'][0]
                        if l.startswith('http') or l.startswith('www'):
                            if "webcache.googleusercontent.com" not in l:
                                self.url_list.append(l)
                    except KeyError:
                        pass
            except Exception as e:
                logger.error(f"Major issue with Google Search: {e}")
                break
            self.counter += 10
            helpers.mod_sleep(self.sleep, jitter=self.jitter)

        self.download_files(dl)

    def download_files(self, dl):
        for url in self.url_list:
            if self.verbose:
                logger.info(f"Google CSV search downloading: {url}")
            try:
                filetype = ".csv"
                file_name, file_download = dl.download_file2(url, filetype)
                if file_download:
                    if self.verbose:
                        logger.info(f"Google CSV file was downloaded: {url}")
                    with open(file_name) as f:
                        self.text += f.read()
                dl.delete_file(file_name)
            except Exception as e:
                logger.error(f"Issue with opening CSV Files: {e}")
        if not self.url_list:
            logger.info("No CSV to download from Google!")

    def get_emails(self):
        parser = Parser.Parser(self.text)
        parser.generic_clean()
        parser.url_clean()
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        return final_output, html_results, json_results
