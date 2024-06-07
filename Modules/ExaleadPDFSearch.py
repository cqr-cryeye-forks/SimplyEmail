#!/usr/bin/env python

import configparser
import requests
import time
from Helpers import Converter, helpers, Parser, Download
from bs4 import BeautifulSoup


class ClassName:

    def __init__(self, Domain, verbose=False):
        self.apikey = False
        self.name = "Exalead PDF Search for Emails"
        self.description = "Uses Exalead Dorking to search PDFs for emails"
        self.Domain = Domain
        self.verbose = verbose
        self.urlList = []
        self.Text = ""

        self._load_config()

    def _load_config(self):
        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.Quanity = int(config['ExaleadPDFSearch']['StartQuantity'])
            self.Limit = int(config['ExaleadPDFSearch']['QueryLimit'])
            self.UserAgent = {'User-Agent': helpers.get_user_agent()}
            self.Counter = int(config['ExaleadPDFSearch']['QueryStart'])
        except Exception as e:
            print(helpers.color(f" [*] Major Settings for ExaleadPDFSearch are missing, EXITING! {e}", warning=True))

    def execute(self):
        self.search()
        return self.get_emails()

    def search(self):
        convert = Converter.Converter(verbose=self.verbose)
        while self.Counter <= self.Limit and self.Counter <= 10:
            time.sleep(1)
            if self.verbose:
                message = f' [*] Exalead Search on page: {self.Counter}'
                print(helpers.color(message, firewall=True))
            url = self._build_search_url()
            self._perform_search(url)
            self.Counter += 30
        self._download_files(convert)

    def _build_search_url(self):
        try:
            url = (f'http://www.exalead.com/search/web/results/?q="%40{self.Domain}"+filetype:pdf&'
                   f'elements_per_page={self.Quanity}&start_index={self.Counter}')
            return url
        except Exception as e:
            error_message = f" [!] Major issue with Exalead PDF Search: {e}"
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
            error_message = f" [!] Fail during parsing result: {e}"
            print(helpers.color(error_message, warning=True))

    def _download_files(self, convert):
        for url in self.urlList:
            if self.verbose:
                message = f' [*] Exalead PDF search downloading: {url}'
                print(helpers.color(message, firewall=True))
            try:
                dl = Download.Download(self.verbose)
                FileName, FileDownload = dl.download_file(url, ".pdf")
                if FileDownload:
                    if self.verbose:
                        message = f' [*] Exalead PDF file was downloaded: {url}'
                        print(helpers.color(message, firewall=True))
                    self.Text += convert.convert_pdf_to_txt(FileName)
                dl.delete_file(FileName)
            except Exception as e:
                print(e)

        if self.verbose:
            message = ' [*] Searching PDF from Exalead Complete'
            print(helpers.color(message, status=True))

    def get_emails(self):
        parser = Parser.Parser(self.Text)
        parser.generic_clean()
        parser.url_clean()
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        return final_output, html_results, json_results
