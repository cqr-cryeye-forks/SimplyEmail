#!/usr/bin/env python

import requests
from urllib.parse import urlparse, parse_qs
import configparser
import time
import logging
from Helpers.Download import Download
from Helpers.helpers import get_user_agent, mod_sleep, get_file_type
from Helpers.Parser import Parser
from Helpers.Converter import Converter
from bs4 import BeautifulSoup


class ClassName(object):

    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "Google XLSX Search for Emails"
        self.description = "Uses Google Dorking to search for emails"
        self.verbose = verbose
        self.logger = logging.getLogger("SimplyEmail.GoogleXlsxSearch")

        self._load_config()
        self.domain = domain
        self.url_list = []
        self.text = ""

    def _load_config(self):
        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.quantity = int(config['GoogleXlsxSearch']['StartQuantity'])
            self.user_agent = {'User-Agent': get_user_agent()}
            self.limit = int(config['GoogleXlsxSearch']['QueryLimit'])
            self.counter = int(config['GoogleXlsxSearch']['QueryStart'])
            self.sleep = int(config['SleepConfig']['QuerySleep'])
            self.jitter = int(config['SleepConfig']['QueryJitter'])
        except KeyError as e:
            self.logger.error("Missing config setting: %s", e)
            raise

    def execute(self):
        self.logger.debug("GoogleXlsxSearch Started")
        self.search()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def search(self):
        convert = Converter(verbose=self.verbose)
        dl = Download(self.verbose)

        while self.counter <= self.limit and self.counter <= 100:
            time.sleep(1)
            if self.verbose:
                self.logger.info("Google XLSX Search on page: %d", self.counter)

            url = f"https://www.google.com/search?q=site:{self.domain}+filetype:xlsx&start={self.counter}"
            try:
                r = requests.get(url, headers=self.user_agent)
                r.raise_for_status()
            except requests.RequestException as e:
                self.logger.error("Fail during request to Google: %s", e)
                continue

            raw_html = r.content
            soup = BeautifulSoup(raw_html, 'html.parser')
            self._parse_google_results(soup)
            self.counter += 10
            mod_sleep(self.sleep, jitter=self.jitter)

        self._download_files(dl, convert)

    def _parse_google_results(self, soup):
        for a in soup.find_all('a'):
            try:
                l = parse_qs(urlparse(a['href']).query).get('q', [None])[0]
                if l and (l.startswith('http') or l.startswith('www')) and "webcache.googleusercontent.com" not in l:
                    self.url_list.append(l)
            except Exception as e:
                self.logger.debug("Error parsing URL from Google results: %s", e)

    def _download_files(self, dl, convert):
        for url in self.url_list:
            if self.verbose:
                self.logger.info('Google XLSX search downloading: %s', url)
            try:
                file_name, file_download = dl.download_file(url, '.xlsx')
                if file_download:
                    self.logger.info('Google XLSX file downloaded: %s', url)
                    ft = get_file_type(file_name).lower()
                    if 'excel' in ft:
                        self.text += convert.convert_Xlsx_to_Csv(file_name)
                    else:
                        self.logger.warning('Downloaded file is not a XLSX: %s', ft)
                dl.delete_file(file_name)
            except Exception as e:
                self.logger.error("Error handling file %s: %s", url, e)

    def get_emails(self):
        parse = Parser(self.text)
        parse.generic_clean()
        parse.url_clean()
        final_output = parse.grep_find_emails()
        html_results = parse.build_results(final_output, self.name)
        json_results = parse.build_json(final_output, self.name)
        self.logger.debug('GoogleXlsxSearch completed search')
        return final_output, html_results, json_results
