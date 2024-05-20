#!/usr/bin/env python

import requests
from urllib.parse import urlparse, parse_qs
import configparser
import time
from Helpers.Converter import Converter
from Helpers.Download import Download
from Helpers.helpers import get_user_agent, mod_sleep, get_file_type
from Helpers.Parser import Parser
from bs4 import BeautifulSoup
import logging


class ClassName(object):

    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "Google PPTX Search for Emails"
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
            self.quantity = int(config['GooglePptxSearch']['StartQuantity'])
            self.user_agent = {'User-Agent': get_user_agent()}
            self.limit = int(config['GooglePptxSearch']['QueryLimit'])
            self.counter = int(config['GooglePptxSearch']['QueryStart'])
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
        convert = Converter(self.verbose)
        dl = Download(self.verbose)

        while self.counter <= self.limit and self.counter <= 100:
            time.sleep(1)
            if self.verbose:
                logging.info('Google PPTX Search on page: %d', self.counter)

            url = f"https://www.google.com/search?q={self.domain}+filetype:pptx&start={self.counter}"
            try:
                raw_html = dl.requesturl(url, useragent=self.user_agent)
            except requests.RequestException as e:
                logging.error("Fail during request to Google: %s", e)
                continue

            try:
                dl.GoogleCaptchaDetection(raw_html)
            except Exception as e:
                logging.warning("Captcha detection issue: %s", e)

            self._parse_google_results(raw_html)
            self.counter += 10
            mod_sleep(self.sleep, jitter=self.jitter)

        self._download_files(dl, convert)

    def _parse_google_results(self, raw_html):
        soup = BeautifulSoup(raw_html, 'html.parser')
        for a in soup.find_all('a'):
            try:
                l = parse_qs(urlparse(a['href']).query).get('q', [None])[0]
                if l and (l.startswith('http') or l.startswith('www') or l.startswith(
                        'https')) and "webcache.googleusercontent.com" not in l:
                    self.url_list.append(l)
            except Exception as e:
                logging.debug("Error parsing URL from Google results: %s", e)

    def _download_files(self, dl, convert):
        for url in self.url_list:
            if self.verbose:
                logging.info('Google PPTX search downloading: %s', url)
            try:
                filetype = ".pptx"
                file_name, file_download = dl.download_file2(url, filetype)
                if file_download:
                    logging.info('Google PPTX file downloaded: %s', url)
                    ft = get_file_type(file_name).lower()
                    if 'powerpoint' in ft:
                        self.text += convert.convert_zip_to_text(file_name)
                    else:
                        logging.warning('Downloaded file is not a PPTX: %s', ft)
                dl.delete_file(file_name)
            except Exception as e:
                logging.error("Error handling file %s: %s", url, e)

    def get_emails(self):
        parse = Parser(self.text)
        parse.remove_unicode()
        parse.generic_clean()
        parse.url_clean()
        final_output = parse.grep_find_emails()
        html_results = parse.build_results(final_output, self.name)
        json_results = parse.build_json(final_output, self.name)
        return final_output, html_results, json_results
