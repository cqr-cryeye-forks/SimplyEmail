#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import logging

from bs4 import BeautifulSoup
from Helpers import Download, helpers, Parser, Converter


class ClassName(object):
    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "Exalead DOC Search for Emails"
        self.description = "Uses Exalead Dorking to search DOCs for emails"
        self.domain = domain
        self.verbose = verbose
        self.Text = ""
        self.urlList = []

        config = configparser.ConfigParser()
        config.read('Common/SimplyEmail.ini')

        self.logger = logging.getLogger("SimplyEmail.ExaleadDOCSearch")

        try:
            self.Quanity = int(config['ExaleadDOCSearch']['StartQuantity'])
            self.UserAgent = {'User-Agent': helpers.get_user_agent()}
            self.Limit = int(config['ExaleadDOCSearch']['QueryLimit'])
            self.Counter = int(config['ExaleadDOCSearch']['QueryStart'])
        except KeyError as e:
            self.logger.critical(f"ExaleadDOCSearch module failed to __init__: {e}")
            print(helpers.color("[*] Major Settings for Exalead are missing, EXITING!\n", warning=True))

    def execute(self):
        self.logger.debug("ExaleadDOCSearch module started")
        self.search()
        return self.get_emails()

    def search(self):
        dl = Download.Download(self.verbose)
        convert = Converter.Converter(verbose=self.verbose)

        while self.Counter <= self.Limit and self.Counter <= 10:
            helpers.mod_sleep(1)
            if self.verbose:
                p = f' [*] Exalead DOC Search on page: {self.Counter}'
                self.logger.info(f'ExaleadDOCSearch on page: {self.Counter}')
                print(helpers.color(p, firewall=True))

            url = f'http://www.exalead.com/search/web/results/?q="%40{self.domain}"+filetype:word&elements_per_page={self.Quanity}&start_index={self.Counter}'
            try:
                raw_html = dl.requesturl(url, useragent=self.UserAgent)
                self.Text += raw_html
                soup = BeautifulSoup(raw_html, "lxml")
                self.urlList.extend([h2.a["href"] for h2 in soup.find_all('h4', class_='media-heading')])
            except Exception as e:
                self.logger.error('ExaleadDOCSearch could not request / parse HTML')
                error = f" [!] Fail during parsing result: {e}"
                print(helpers.color(error, warning=True))

            self.Counter += 30

        self.download_files(dl, convert)

    def download_files(self, dl, convert):
        for url in self.urlList:
            if self.verbose:
                p = f' [*] Exalead DOC search downloading: {url}'
                self.logger.info(f'ExaleadDOCSearch downloading: {url}')
                print(helpers.color(p, firewall=True))

            try:
                filetype = ".doc"
                file_name, file_download = dl.download_file(url, filetype)
                if file_download:
                    if self.verbose:
                        p = f' [*] Exalead DOC file was downloaded: {url}'
                        self.logger.info(f'ExaleadDOCSearch downloaded: {p}')
                        print(helpers.color(p, firewall=True))
                    ft = helpers.get_file_type(file_name).lower()
                    if 'word' in ft:
                        self.Text += convert.convert_doc_to_txt(file_name)
                    else:
                        self.logger.warning(f'Downloaded file is not a DOC: {ft}')
            except Exception as e:
                error = f" [!] Issue with opening DOC Files: {e}"
                print(helpers.color(error, warning=True))

            try:
                dl.delete_file(file_name)
            except Exception as e:
                self.logger.error(f'Error deleting file: {e}')

        if self.verbose:
            p = ' [*] Searching DOC from Exalead Complete'
            print(helpers.color(p, status=True))

    def get_emails(self):
        parser = Parser.Parser(self.Text)
        parser.generic_clean()
        parser.url_clean()
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        self.logger.debug('ExaleadDOCSearch completed search')
        return final_output, html_results, json_results
