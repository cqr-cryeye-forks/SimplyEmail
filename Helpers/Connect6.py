#!/usr/bin/env python
import requests
import configparser
import urllib.parse as urlparse
import logging
from bs4 import BeautifulSoup


class Connect6Scraper:
    '''
    A simple class to scrape names from connect6.com
    '''

    def __init__(self, domain, verbose=False):
        config = configparser.ConfigParser()
        self.logger = logging.getLogger("SimplyEmail.Connect6")
        try:
            config.read('Common/SimplyEmail.ini')
            self.user_agent = {
                'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                               'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')}
            self.domain = domain
            self.final_answer = ''
            self.verbose = verbose
        except Exception as e:
            self.logger.error(f"Error during initialization: {e}")

    def connect6_auto_url(self):
        '''
        Try to find the connect6 URL for the domain you are targeting.
        '''
        urllist = []
        try:
            domain = self.domain.split('.')[0]
            url = f"https://www.google.com/search?q=site:connect6.com+{domain}"
            r = requests.get(url, headers=self.user_agent)
            r.raise_for_status()
        except requests.RequestException as e:
            error = f"[!] Major issue with Google Search for Connect6 URL: {e}"
            self.logger.error(error)
            return urllist

        try:
            soup = BeautifulSoup(r.content, 'html.parser')
            for a in soup.find_all('a', href=True):
                try:
                    l = urlparse.parse_qs(urlparse.urlparse(a['href']).query).get('q')
                    if l and 'site:connect6.com' not in l[0]:
                        l = l[0].split(":")
                        urllist.append(l[2])
                except Exception:
                    continue

            # Prioritize URLs containing '/c'
            urllist.sort(key=lambda x: 0 if '/c' in x else 1)
            return urllist
        except Exception as e:
            self.logger.error(f"Error parsing URL list: {e}")
            return urllist

    def connect6_download(self, url):
        '''
        Downloads raw source of Connect6 page.
        '''
        namelist = []
        try:
            if not url.startswith(('http', 'https')):
                url = 'http://' + url
            if self.verbose:
                self.logger.info(f"[*] Now downloading Connect6 Source: {url}")
            r = requests.get(url, headers=self.user_agent)
            r.raise_for_status()
        except requests.RequestException as e:
            error = f"[!] Major issue with Downloading Connect6 source: {e}"
            self.logger.error(error)
            return namelist

        try:
            soup = BeautifulSoup(r.content, 'html.parser')
            for utag in soup.find_all("ul", {"class": "directoryList"}):
                for litag in utag.find_all('li'):
                    namelist.append(litag.text)
                    if self.verbose:
                        self.logger.info(f"[*] Connect6 Name Found: {litag.text}")
            return namelist
        except Exception as e:
            self.logger.error(f"Error parsing Connect6 source: {e}")
            return namelist

    def connect6_parse_name(self, raw):
        '''
        Takes a raw non-parsed name from connect6.com.
        Returns a list of the name [first, last].
        '''
        try:
            if raw.strip():
                raw = raw.split('(')[0].split(',')[0].split('/')[0].strip()
                if raw.endswith(".") or len(raw) == 1 or "LinkedIn" in raw or '"' in raw:
                    return None

                parts = raw.split()
                if len(parts) > 2:
                    if "(" in parts[1]:
                        return [parts[0].strip(), parts[2].strip()]
                    elif len(parts[2]) < 4:
                        return [parts[0].strip(), parts[1].strip()]
                    else:
                        return [parts[0].strip(), parts[2].strip()]
                elif len(parts) == 2:
                    return [parts[0].strip(), parts[1].strip()]
        except Exception as e:
            self.logger.error(f"[!] Failed to parse name: {e}")
            return None
