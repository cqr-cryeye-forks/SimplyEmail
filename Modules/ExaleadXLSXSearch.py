#!/usr/bin/env python

import requests
import configparser
import time
from Helpers import Download
from Helpers import helpers
from Helpers import Parser
from Helpers import Converter
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExaleadXLSXSearch:
    def __init__(self, domain, verbose=False):
        self.name = "Exalead XLSX Search for Emails"
        self.description = "Uses Exalead Dorking to search XLSXs for emails"
        self.domain = domain
        self.verbose = verbose
        self.url_list = []
        self.text = ""

        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.quantity = int(config['ExaleadXLSXSearch']['StartQuantity'])
            self.user_agent = {'User-Agent': helpers.get_user_agent()}
            self.limit = int(config['ExaleadXLSXSearch']['QueryLimit'])
            self.counter = int(config['ExaleadXLSXSearch']['QueryStart'])
        except KeyError as e:
            logger.error(f"Major settings for ExaleadXLSXSearch are missing: {e}")
            raise SystemExit(f"Major settings for ExaleadXLSXSearch are missing: {e}")

    def execute(self):
        self.search()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def search(self):
        dl = Download.Download(verbose=self.verbose)
        convert = Converter.Converter(verbose=self.verbose)
        while self.counter <= self.limit:
            time.sleep(1)
            if self.verbose:
                logger.info(f"Exalead XLSX Search on page: {self.counter}")

            url = (f'http://www.exalead.com/search/web/results/?q="%40{self.domain}"+filetype:xlsx'
                   f'&elements_per_page={self.quantity}&start_index={self.counter}')
            try:
                response = requests.get(url, headers=self.user_agent)
                response.raise_for_status()
                raw_html = response.content
                self.text += raw_html
                soup = BeautifulSoup(raw_html, "lxml")
                self.url_list.extend(h4.a["href"] for h4 in soup.find_all('h4', class_='media-heading'))
            except requests.RequestException as e:
                logger.error(f"Fail during request to Exalead: {e}")
            except Exception as e:
                logger.error(f"Fail during parsing result: {e}")

            self.counter += 30

        try:
            for url in self.url_list:
                if self.verbose:
                    logger.info(f"Exalead XLSX search downloading: {url}")
                try:
                    filetype = ".xlsx"
                    file_name, file_download = dl.download_file(url, filetype)
                    if file_download:
                        if self.verbose:
                            logger.info(f"Exalead XLSX file was downloaded: {url}")
                        self.text += convert.convert_xlsx_to_csv(file_name)
                except Exception as e:
                    logger.error(f"Issue with opening XLSX files: {e}")
                try:
                    dl.delete_file(file_name)
                except Exception as e:
                    logger.error(f"Error deleting file: {e}")
        except Exception as e:
            logger.error(f"No XLSXs to download from Exalead: {e}")

        if self.verbose:
            logger.info("Searching XLSX from Exalead Complete")

    def get_emails(self):
        parser = Parser.Parser(self.text)
        parser.generic_clean()
        parser.url_clean()
        final_output = parser.grep_find_emails()
        html_results = parser.build_results(final_output, self.name)
        json_results = parser.build_json(final_output, self.name)
        return final_output, html_results, json_results
