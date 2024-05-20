#!/usr/bin/env python
import requests
import os
import configparser
from Helpers import helpers
import logging
import urllib.request
import urllib.error
import time
from bs4 import BeautifulSoup
from random import randint


class Download:

    def __init__(self, verbose=False):
        config = configparser.ConfigParser()
        try:
            self.logger = logging.getLogger("SimplyEmail.Download")
            self.verbose = verbose
            config.read('Common/SimplyEmail.ini')
            self.UserAgent = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, как Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        except Exception as e:
            print(e)

    def download_file(self, url, filetype, maxfile=100, verify=True):
        """
        Downloads a file using requests,

        maxfile=100 in MegaBytes
        chunk_size=1024 the bytes to write from mem
        """
        local_filename = randint(10000, 999999999)
        local_filename = str(local_filename) + str(filetype)

        if not url.startswith(('http', 'https')):
            url = 'http://' + str(url)

        try:
            time.sleep(2)
            self.logger.debug("Download started: " + str(url))
            r = requests.get(url, stream=True, headers=self.UserAgent, verify=verify)
            with open(local_filename, 'wb+') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            download = os.path.isfile(local_filename)
            return local_filename, download
        except Exception as e:
            if self.verbose:
                p = ' [*] Download of file failed: ' + str(e)
                print(helpers.color(p, firewall=True))
            self.logger.error("Failed to download file: " + str(url) + ' error: ' + str(e))
            download = os.path.isfile(local_filename)
            return local_filename, download

    def download_file2(self, url, filetype, timeout=10):
        local_filename = randint(10000, 999999999)
        local_filename = str(local_filename) + str(filetype)

        if not url.startswith(('http', 'https')):
            url = 'http://' + str(url)

        try:
            self.logger.debug("Download2 started: " + str(url))
            with urllib.request.urlopen(url, timeout=timeout) as response:
                data = response.read()
            with open(local_filename, 'wb+') as f:
                f.write(data)
            download = os.path.isfile(local_filename)
            self.logger.debug("Download2 completed: " + str(url))
            return local_filename, download
        except urllib.error.HTTPError as e:
            self.logger.error('urllib2 HTTPError: ' + str(e))
        except urllib.error.URLError as e:
            self.logger.error('urllib2 URLError: ' + str(e))
        except Exception as e:
            if self.verbose:
                p = ' [*] Download2 of file failed: ' + str(e)
                print(helpers.color(p, firewall=True))
            self.logger.error("Failed to download2 file: " + str(e))
        download = os.path.isfile(local_filename)
        return local_filename, download

    def delete_file(self, local_filename):
        try:
            if os.path.isfile(local_filename):
                os.remove(local_filename)
                self.logger.debug("File deleted: " + str(local_filename))
            else:
                if self.verbose:
                    p = ' [*] File not found to remove: ' + local_filename
                    print(helpers.color(p, firewall=True))
        except Exception as e:
            self.logger.error("Failed to delete file: " + str(e))
            if self.verbose:
                print(e)

    def GoogleCaptchaDetection(self, RawHtml):
        soup = BeautifulSoup(RawHtml, "lxml")
        if "Our systems have detected unusual traffic" in soup.text:
            p = " [!] Google Captcha was detected! (For best results resolve/restart -- Increase sleep/jitter in SimplyEmail.ini)"
            self.logger.warning("Google Captcha was detected!")
            print(helpers.color(p, warning=True))
            return True
        else:
            return False

    def requesturl(self, url, useragent, timeout=10, retrytime=5, statuscode=False, raw=False, verify=True):
        """
        A very simple request function
        This is setup to handle the following parms:

        url = the passed in url to request
        useragent = the useragent to use
        timeout = how long to wait if no "BYTES" rec

        Exception handling will also retry on the event of
        a timeout and warn the user.
        """
        rawhtml = ""
        r = None  # Инициализация переменной r
        try:
            r = requests.get(url, headers={'User-Agent': useragent}, timeout=timeout, verify=verify)
            rawhtml = r.content
            self.logger.debug(
                f'Request completed: code = {r.status_code} size = {len(rawhtml)} url = {url}')
        except requests.exceptions.Timeout:
            if self.verbose:
                p = f' [!] Request for url timed out, retrying: {url}'
                self.logger.info(f'Request timed out, retrying: {url}')
                print(helpers.color(p, firewall=True))
            r = requests.get(url, headers={'User-Agent': useragent}, timeout=retrytime, verify=verify)
            rawhtml = r.content
        except requests.exceptions.TooManyRedirects:
            if self.verbose:
                p = f' [!] Request for url resulted in bad url: {url}'
                self.logger.error(f'Request for url resulted in bad url: {url}')
                print(helpers.color(p, warning=True))
        except requests.exceptions.RequestException as e:
            if self.verbose:
                p = f' [!] Request for url resulted in major error: {e}'
                self.logger.critical(f'Request for url resulted in major error: {e}')
                print(helpers.color(p, warning=True))
        except Exception as e:
            p = f' [!] Request for url resulted in unhandled error: {e}'
            self.logger.critical(f'Request for url resulted in unhandled error: {e}')
        if r:
            if statuscode:
                return rawhtml, r.status_code
            elif raw:
                return r
            else:
                return rawhtml
        return rawhtml  # Возвращаем rawhtml в случае, если r не инициализирован

