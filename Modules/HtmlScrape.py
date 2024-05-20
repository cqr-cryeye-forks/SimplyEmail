#!/usr/bin/env python

import subprocess
import configparser
import shutil
from Helpers import helpers
from Helpers import Parser


class ClassName:
    def __init__(self, domain, verbose=False):
        self.apikey = False
        self.name = "HTML Scrape of Target Website"
        self.description = "HTML Scrape the target website for emails and data"
        self.verbose = verbose
        self.domain = domain
        self.config = self.load_config()
        self.setup_attributes()
        self.retVal = 0

    def load_config(self):
        config = configparser.ConfigParser()
        config.read('Common/SimplyEmail.ini')
        return config

    def setup_attributes(self):
        try:
            config = self.config
            self.useragent = f'--user-agent="{config["GlobalSettings"]["UserAgent"]}"'
            self.depth = f'--level={config["HtmlScrape"]["Depth"]}'
            self.wait = f'--wait={config["HtmlScrape"]["Wait"]}'
            self.limit_rate = f'--limit-rate={config["HtmlScrape"]["LimitRate"]}'
            self.timeout = f'--timeout={config["HtmlScrape"]["Timeout"]}'
            self.save = f'--directory-prefix={config["HtmlScrape"]["Save"]}{self.domain}'
            self.remove = config["HtmlScrape"]["RemoveHTML"]
            self.maxRetries = "--tries=5"
        except KeyError as e:
            print(helpers.color(f" [*] Missing configuration for {e}, EXITING!\n", warning=True))

    def execute(self):
        try:
            self.search()
            final_output, html_results, json_results = self.get_emails()
            return final_output, html_results, json_results
        except Exception as e:
            print(e)

    def search(self):
        temp_domain = f"http://www.{self.domain}"
        wget_options = [
            "wget", "-q", "-e robots=off", "--header=\"Accept: text/html\"", self.useragent,
            "--recursive", self.depth, self.wait, self.limit_rate, self.save,
            self.timeout, "--page-requisites",
            "-R gif,jpg,pdf,png,css,zip,mov,wmv,ppt,doc,docx,xls,exe,bin,pptx,avi,swf,vbs,xlsx,kfp,pub",
            "--no-clobber", self.maxRetries, "--domains", self.domain, temp_domain
        ]
        try:
            if self.verbose:
                print(helpers.color(' [*] HTML scrape underway [This can take a bit!]', firewall=True))
            self.retVal = subprocess.call(wget_options)
            if self.retVal > 0:
                print(helpers.color(f" [*] Wget returned error, retrying: {self.retVal}", warning=True))
                self.retVal = subprocess.call(wget_options)
        except Exception as e:
            print(e)
            print(" [!] ERROR during Wget Request")

    def get_emails(self):
        directory = self.save.replace("--directory-prefix=", "")
        final_output = []

        try:
            if self.retVal == 0:
                ps = subprocess.Popen(('grep', '-r', "@", directory), stdout=subprocess.PIPE)
                val = subprocess.check_output(
                    ("grep", "-i", "-o", '[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}'),
                    stdin=ps.stdout
                ).decode('utf-8')

                if val:
                    final_output = val.splitlines()
        except Exception as e:
            print(e)

        if self.remove.lower() == "yes":
            try:
                shutil.rmtree(directory)
            except Exception as e:
                print(e)

        parse = Parser.Parser(final_output)
        html_results = parse.build_results(final_output, self.name)
        json_results = parse.build_json(final_output, self.name)
        return final_output, html_results, json_results
