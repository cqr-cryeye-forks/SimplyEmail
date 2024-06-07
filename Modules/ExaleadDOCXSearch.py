#!/usr/bin/env python

import configparser
import requests
import time
import logging
from Helpers import Converter, helpers, Parser, Download
from bs4 import BeautifulSoup


class ClassName:

    def __init__(self, Domain, verbose=False):
        self.apikey = False
        self.name = "Exalead DOCX Search for Emails"
        self.description = "Uses Exalead Dorking to search DOCXs for emails"
        self.Domain = Domain
        self.verbose = verbose
        self.urlList = []
        self.Text = ""

        self._setup_logger()
        self._load_config()

    def _setup_logger(self):
        self.logger = logging.getLogger("SimplyEmail.ExaleadDOCXSearch")

    def _load_config(self):
        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.Quanity = int(config['ExaleadDOCXSearch']['StartQuantity'])
            self.UserAgent = {'User-Agent': helpers.get_user_agent()}
            self.Limit = int(config['ExaleadDOCXSearch']['QueryLimit'])
            self.Counter = int(config['ExaleadDOCXSearch']['QueryStart'])
        except Exception as e:
            self.logger.critical("ExaleadDOCXSearch module failed to __init__: " + str(e))
            error_message = f" [*] Major Settings for ExaleadDOCXSearch are missing, EXITING: {e}"
            print(helpers.color(error_message, warning=True))

    def execute(self):
        self.logger.debug("ExaleadDOCXSearch module started")
        self.search()
        return self.get_emails()

    def download_file(self, url):
        local_filename = url.split('/')[-1]
        r = requests.get(url, stream=True)
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return local_filename

    def search(self):
        convert = Converter.Converter(verbose=self.verbose)
        while self.Counter <= self.Limit:
            time.sleep(1)
            if self.verbose:
                message = f' [*] Exalead Search on page: {self.Counter}'
                self.logger.info(message)
                print(helpers.color(message, firewall=True))
            url = self._build_search_url()
            self._perform_search(url)
            self.Counter += 30
        self._download_files(convert)

    def _build_search_url(self):
        try:
            url = (f'http://www.exalead.com/search/web/results/?q="%40{self.Domain}"+filetype:docx&'
                   f'elements_per_page={self.Quanity}&start_index={self.Counter}')
            return url
        except Exception as e:
            self.logger.error("Issue building URL to search")
            error_message = f" [!] Major issue with Exalead DOCX Search: {e}"
            print(helpers.color(error_message, warning=True))

    def _perform_search(self, url):
        try:
            r = requests.get(url, headers=self.UserAgent)
            self._parse_search_results(r.content)
        except Exception as e:
            error_message = f" [!] Fail during Request to Exalead (Check Connection): {e}"
            print(helpers.color(error_message, warning=True))

    def _parse_search_results(self, raw_html):
        try:
            self.Text += raw_html
            soup = BeautifulSoup(raw_html, "lxml")
            self.urlList = [h2.a["href"] for h2 in soup.findAll('h4', class_='media-heading')]
        except Exception as e:
            self.logger.error("Fail during parsing result: " + str(e))
            error_message = f" [!] Fail during parsing result: {e}"
            print(helpers.color(error_message, warning=True))

    def _download_files(self, convert):
        for url in self.urlList:
            if self.verbose:
                message = f' [*] Exalead DOCX search downloading: {url}'
                self.logger.info(message)
                print(helpers.color(message, firewall=True))
            try:
                filetype = ".docx"
                dl = Download.Download(self.verbose)
                FileName, FileDownload = dl.download_file(url, filetype)
                if FileDownload:
                    if self.verbose:
                        self.logger.info(f"File was downloaded: {url}")
                        message = f' [*] Exalead DOCX file was downloaded: {url}'
                        print(helpers.color(message, firewall=True))
                    self.Text += convert.convert_docx_to_txt(FileName)
                dl.delete_file(FileName)
            except Exception as e:
                self.logger.error("Issue with opening DOCX Files: " + str(e))
                error_message = f" [!] Issue with opening DOCX Files: {e}"
                print(helpers.color(error_message, warning=True))

        if self.verbose:
            message = ' [*] Searching DOCX from Exalead Complete'
            self.logger.info("Searching DOCX from Exalead Complete")
            print(helpers.color(message, status=True))

    def get_emails(self):
        parser = Parser.Parser(self.Text)
        parser.generic_clean()
        parser.url_clean()
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        self.logger.debug('ExaleadDOCXSearch completed search')
        return final_output, html_results, json_results
