#!/usr/bin/env python
import configparser
import logging
from Helpers import Download, Parser, helpers


class ClassName:
    def __init__(self, domain, verbose=False):
        self.apikey = True
        self.name = "Hunter API"
        self.description = "Search the Hunter DB for potential emails"
        self.domain = domain
        self.verbose = verbose
        self.results = []
        self.logger = logging.getLogger("SimplyEmail.Hunter")
        config = self.load_config()
        self.set_attributes(config)

    def load_config(self):
        config = configparser.ConfigParser()
        config.read('Common/SimplyEmail.ini')
        return config

    def set_attributes(self, config):
        try:
            self.UserAgent = config['GlobalSettings']['UserAgent']
            self.apikeyv = config['APIKeys']['Hunter']
            self.RequestLimit = int(config['Hunter']['RequestLimit'])
            self.QuotaLimit = int(config['Hunter']['QuotaLimit'])
            self.EmailType = config['Hunter']['EmailType']
            self.set_email_type()
        except KeyError as e:
            self.logger.critical(f"Hunter module failed to initialize: {e}")
            print(helpers.color(f" [*] Error in Hunter settings: {e}\n", warning=True))

    def set_email_type(self):
        if self.EmailType == "Both":
            self.type = ""
            self.etype = "total"
        elif self.EmailType == "Personal":
            self.type = "&type=personal"
            self.etype = "personal_emails"
        elif self.EmailType == "Generic":
            self.type = "&type=generic"
            self.etype = "generic_emails"
        else:
            raise ValueError("Email Type setting invalid")

    def execute(self):
        self.logger.debug("Hunter module started")
        self.process()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def process(self):
        dl = Download.Download(self.verbose)
        over_quota_limit, quota_used = self.check_quota(dl)
        total_emails, offset = self.check_email_count(dl)

        requests_made = 0
        while total_emails > 0:
            if self.should_stop(over_quota_limit, quota_used, requests_made):
                break
            requests_made += self.fetch_emails(dl, total_emails, offset)
            total_emails -= 100
            offset += 100

        self.log_results(over_quota_limit, quota_used, requests_made)

    def check_quota(self, dl):
        try:
            url = f"https://api.hunter.io/v2/account?api_key={self.apikeyv}"
            response = dl.requesturl(url, useragent=self.UserAgent, raw=True).json()
            quota = int(response['data']['calls']['available'])
            quota_used = int(response['data']['calls']['used'])
            over_quota_limit = quota_used >= self.QuotaLimit
            return over_quota_limit, quota_used
        except Exception as e:
            self.logger.critical(f"Hunter API error: {e}")
            raise

    def check_email_count(self, dl):
        try:
            url = f"https://api.hunter.io/v2/email-count?domain={self.domain}"
            response = dl.requesturl(url, useragent=self.UserAgent, raw=True).json()
            total_emails = int(response['data'][self.etype])
            return total_emails, 0
        except Exception as e:
            self.logger.critical(f"Major issue with Hunter search: {e}")
            raise

    def should_stop(self, over_quota_limit, quota_used, requests_made):
        if over_quota_limit or requests_made >= self.RequestLimit:
            if self.verbose:
                print(helpers.color(
                    f" [*] Search stopped: {quota_used}/{self.QuotaLimit} quota used",
                    firewall=True
                ))
            return True
        return False

    def fetch_emails(self, dl, total_emails, offset):
        try:
            url = (f"https://api.hunter.io/v2/domain-search?domain={self.domain}"
                   f"{self.type}&limit=100&offset={offset}&api_key={self.apikeyv}")
            response = dl.requesturl(url, useragent=self.UserAgent, raw=True).json()
            email_count = min(int(response['meta']['results']), total_emails)
            self.results.extend([email['value'] for email in response['data']['emails'][:email_count]])
            return email_count // 10 + (1 if email_count % 10 != 0 else 0)
        except Exception as e:
            self.logger.critical(f"Hunter API error: {e}")
            raise

    def log_results(self, over_quota_limit, quota_used, requests_made):
        if self.verbose:
            print(helpers.color(' [*] Hunter completed JSON request', firewall=True))
            requests_used = requests_made + quota_used
            if over_quota_limit:
                print(helpers.color(
                    " [*] No Hunter requests left. Refills in about a month",
                    firewall=True
                ))
            else:
                print(helpers.color(
                    f" [*] {requests_used}/{requests_used + quota_used} Hunter requests left",
                    firewall=True
                ))

    def get_emails(self):
        parse = Parser.Parser(self.results)
        final_output = parse.clean_list_output()
        html_results = parse.build_results(final_output, self.name)
        json_results = parse.build_json(final_output, self.name)
        self.logger.debug('Hunter completed search')
        return final_output, html_results, json_results
