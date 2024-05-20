#!/usr/bin/env python
import configparser
import mechanize
from bs4 import BeautifulSoup
from Helpers import helpers


class LinkedinScraper:
    """
    A simple class to scrape names from bing.com for LinkedIn names.
    """

    def __init__(self, domain, verbose=False):
        self.domain = domain.split('.')[0]
        self.verbose = verbose
        self.user_agent = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
        }

        self.config = configparser.ConfigParser()
        try:
            self.config.read('Common/SimplyEmail.ini')
        except Exception as e:
            print(f"Error reading configuration: {e}")

    def linked_in_names(self):
        """
        Uses Bing to scrape for LinkedIn names and returns a list of names.
        """
        try:
            br = mechanize.Browser()
            br.set_handle_robots(False)
            query = f'site:"www.linkedin.com/in/" OR site:"www.linkedin.com/pub/" -site:"www.linkedin.com/pub/dir/" "{self.domain}"'
            url = f'http://www.bing.com/search?q={query}&qs=n&form=QBRE'
            response = br.open(url)
            soup = BeautifulSoup(response, 'lxml')
            names_list = self._extract_names(br, soup)

            if names_list:
                return names_list

        except Exception as e:
            error_msg = f"Major issue with downloading LinkedIn source: {e}"
            print(helpers.color(error_msg, warning=True))

        return []

    def _extract_names(self, br, soup):
        """
        Helper function to extract names from the soup object.
        """
        names_list = []
        while True:
            for definition in soup.find_all('h2'):
                content = definition.get_text()
                if "LinkedIn" in content:
                    name = content.split('>')[1].split('|')[0].strip().split(',')[0]
                    name_parts = name.split(' ')
                    if self.verbose:
                        print(helpers.color(f"[*] LinkedIn Name Found: {name_parts}", firewall=True))
                    names_list.append(name_parts)
            if not self._follow_next_page(br, soup):
                break
        return names_list

    def _follow_next_page(self, br, soup):
        """
        Helper function to follow the next page of search results if available.
        """
        link_list = [link.text for link in br.links()]
        if "Next" in link_list:
            response = br.follow_link(text="Next")
            soup = BeautifulSoup(response, 'lxml')
            return True
        return False

    def linked_in_clean(self, raw):
        """
        Cleans raw names by removing unwanted characters.
        """
        if not raw:
            return None

        firstname, lastname = raw[0], raw[1]
        cleaned_firstname = self._clean_name(firstname)
        cleaned_lastname = self._clean_name(lastname)

        if ("@" in cleaned_firstname) or ("@" in cleaned_lastname):
            return None

        if self.verbose:
            print(helpers.color(f"[*] Name Cleaned: {cleaned_firstname} {cleaned_lastname}", firewall=True))

        return [cleaned_firstname, cleaned_lastname]

    def _clean_name(self, name):
        """
        Helper function to remove unwanted characters from a name.
        """
        for char in ["'", "-", " ", ",", "(", ")"]:
            name = name.replace(char, "")
        return name
