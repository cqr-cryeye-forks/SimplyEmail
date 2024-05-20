#!/usr/bin/env python

import requests
from urllib.parse import urlparse, parse_qs
import configparser
import time
from Helpers.Download import Download
from Helpers.Converter import Converter
from Helpers.helpers import get_user_agent, mod_sleep
from Helpers.Parser import Parser
from bs4 import BeautifulSoup
import logging


class ClassName:

    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "Google DOC Search for Emails"
        self.description = "Uses Google Dorking to search for emails"
        self.verbose = verbose

        self._load_config()
        self.domain = domain
        self.url_list = []
        self.text = ""

    def _load_config(self):
        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.quanity = int(config['GoogleDocSearch']['StartQuantity'])
            self.user_agent = {'User-Agent': get_user_agent()}
            self.limit = int(config['GoogleDocSearch']['QueryLimit'])
            self.counter = int(config['GoogleDocSearch']['QueryStart'])
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
        convert = Converter(verbose=self.verbose)

        while self.counter <= self.limit and self.counter <= 100:
            time.sleep(1)
            if self.verbose:
                logging.info('Google DOC Search on page: %d', self.counter)

            urly = f"https://www.google.com/search?q=site:{self.domain}+filetype:doc&start={self.counter}"
            try:
                r = requests.get(urly)
                r.raise_for_status()
            except requests.RequestException as e:
                logging.error("Request to Google failed: %s", e)
                continue

            raw_html = r.content
            if dl.GoogleCaptchaDetection(raw_html):
                logging.warning("Captcha detected, stopping search")
                break

            self._parse_google_results(raw_html)
            self.counter += 10
            mod_sleep(self.sleep, jitter=self.jitter)

        self._download_files(dl, convert)

    def _parse_google_results(self, raw_html):
        soup = BeautifulSoup(raw_html, 'html.parser')
        for a in soup.find_all('a'):
            try:
                l = parse_qs(urlparse(a['href']).query).get('q', [None])[0]
                if l and (l.startswith('http') or l.startswith('www')) and "webcache.googleusercontent.com" not in l:
                    self.url_list.append(l)
            except Exception as e:
                logging.debug("Error parsing URL from Google results: %s", e)

    def _download_files(self, dl, convert):
        for url in self.url_list:
            if self.verbose:
                logging.info('Google DOC search downloading: %s', url)
            try:
                filetype = ".doc"
                file_name, file_download = dl.download_file(url, filetype)
                if file_download:
                    logging.info('Google DOC file downloaded: %s', url)
                    self.text += convert.convert_doc_to_txt(file_name)
                dl.delete_file(file_name)
            except Exception as e:
                logging.error("Error handling file %s: %s", url, e)

    def get_emails(self):
        parse = Parser(self.text)
        parse.generic_clean()
        parse.url_clean()
        final_output = parse.grep_find_emails()
        html_results = parse.build_results(final_output, self.name)
        json_results = parse.build_json(final_output, self.name)
        return final_output, html_results, json_results
