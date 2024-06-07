#!/usr/bin/env python

import configparser
import logging
from Helpers import Download, helpers, Parser, Converter
from bs4 import BeautifulSoup


class ClassName:

    def __init__(self, Domain, verbose=False):
        self.apikey = False
        self.name = "Exalead PPTX Search for Emails"
        self.description = "Uses Exalead Dorking to search PPTX for emails"
        self.Domain = Domain
        self.verbose = verbose
        self.urlList = []
        self.Text = ""

        self._setup_logger()
        self._load_config()

    def _setup_logger(self):
        self.logger = logging.getLogger("SimplyEmail.ExaleadPPTXSearch")

    def _load_config(self):
        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.Quanity = int(config['ExaleadPPTXSearch']['StartQuantity'])
            self.UserAgent = {'User-Agent': helpers.get_user_agent()}
            self.Limit = int(config['ExaleadPPTXSearch']['QueryLimit'])
            self.Counter = int(config['ExaleadPPTXSearch']['QueryStart'])
        except Exception as e:
            self.logger.critical(f"ExaleadPPTXSearch module failed to __init__: {e}")
            print(helpers.color(" [*] Major Settings for Exalead are missing, EXITING!\n", warning=True))

    def execute(self):
        self.logger.debug("ExaleadPPTXSearch module started")
        self.search()
        return self.get_emails()

    def search(self):
        dl = Download.Download(self.verbose)
        convert = Converter.Converter(verbose=self.verbose)
        while self.Counter <= self.Limit and self.Counter <= 10:
            helpers.mod_sleep(1)
            if self.verbose:
                p = f' [*] Exalead PPTX Search on page: {self.Counter}'
                self.logger.info(f'ExaleadPPTXSearch on page: {self.Counter}')
                print(helpers.color(p, firewall=True))
            url = self._build_search_url()
            self._perform_search(url)
            self.Counter += 30
        self._download_files(dl, convert)

    def _build_search_url(self):
        try:
            url = (f'http://www.exalead.com/search/web/results/?q="%40{self.Domain}"+filetype:pptx&'
                   f'elements_per_page={self.Quanity}&start_index={self.Counter}')
            return url
        except Exception as e:
            self.logger.error('ExaleadPPTXSearch could not build URL')
            error = f" [!] Major issue with Exalead PPTX Search: {e}"
            print(helpers.color(error, warning=True))

    def _perform_search(self, url):
        dl = Download.Download(self.verbose)
        try:
            RawHtml = dl.requesturl(url, useragent=self.UserAgent)
            self.Text += RawHtml
            soup = BeautifulSoup(RawHtml, "lxml")
            self.urlList = [h2.a["href"] for h2 in soup.findAll('h4', class_='media-heading')]
        except Exception as e:
            self.logger.error('ExaleadPPTXSearch could not request / parse HTML')
            error = f" [!] Fail during parsing result: {e}"
            print(helpers.color(error, warning=True))

    def _download_files(self, dl, convert):
        for url in self.urlList:
            if self.verbose:
                p = f' [*] Exalead PPTX search downloading: {url}'
                self.logger.info(f'ExaleadPPTXSearch downloading: {url}')
                print(helpers.color(p, firewall=True))
            try:
                FileName, FileDownload = dl.download_file(url, ".pptx")
                if FileDownload:
                    if self.verbose:
                        p = f' [*] Exalead PPTX file was downloaded: {url}'
                        self.logger.info(f'ExaleadDOCSearch downloaded: {p}')
                        print(helpers.color(p, firewall=True))
                    ft = helpers.filetype(FileName).lower()
                    if 'powerpoint' in ft:
                        self.Text += convert.convert_zip_to_text(FileName)
                    else:
                        self.logger.warning(f'Downloaded file is not a PPTX: {ft}')
                dl.delete_file(FileName)
            except Exception as e:
                error = f" [!] Issue with opening PPTX Files: {e}"
                print(helpers.color(error, warning=True))
        if not self.urlList and self.verbose:
            print(helpers.color(" [*] No PPTX's to download from Exalead!\n", firewall=True))
        if self.verbose:
            p = ' [*] Searching PPTX from Exalead Complete'
            print(helpers.color(p, status=True))

    def get_emails(self):
        Parse = Parser.Parser(self.Text)
        Parse.generic_clean()
        Parse.url_clean()
        FinalOutput = Parse.grep_find_emails()
        HtmlResults = Parse.build_results(FinalOutput, self.name)
        JsonResults = Parse.build_json(FinalOutput, self.name)
        self.logger.debug('ExaleadPPTXSearch completed search')
        return FinalOutput, HtmlResults, JsonResults
