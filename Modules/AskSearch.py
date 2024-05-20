#!/usr/bin/env python
import configparser
import logging
from Helpers import Download, Parser, helpers


class AskSearch:

    def __init__(self, domain, verbose=False):
        self.logger = logging.getLogger("SimplyEmail.AskSearch")
        self.name = "Ask Search for Emails"
        self.description = "Simple Ask Search for Emails"
        self.verbose = verbose
        self.domain = domain
        self.html = ""
        self.counter = 0

        self._load_config()

    def _load_config(self):
        """
        Загружает конфигурационный файл и устанавливает необходимые параметры.
        """
        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.user_agent = {'User-Agent': helpers.get_user_agent()}
            self.page_limit = config['AskSearch'].getint('QueryPageLimit', 10)
            self.counter = config['AskSearch'].getint('QueryStart', 1)
            self.sleep = config['SleepConfig'].getint('QuerySleep', 1)
            self.jitter = config['SleepConfig'].getint('QueryJitter', 1)
        except Exception as e:
            self.logger.critical(f'AskSearch module failed to load: {e}')
            print(helpers.color("[*] Major Settings for Ask Search are missing, EXITING!\n", warning=True))

    def execute(self):
        """
        Выполняет процесс поиска и извлечения email адресов.
        """
        self.logger.debug("AskSearch module started")
        self.process()
        final_output, html_results, json_results = self.get_emails()
        return final_output, html_results, json_results

    def process(self):
        """
        Выполняет запросы к поисковой системе Ask для извлечения HTML.
        """
        dl = Download.Download(self.verbose)
        while self.counter <= self.page_limit:
            if self.verbose:
                message = f' [*] AskSearch on page: {self.counter}'
                print(helpers.color(message, firewall=True))
                self.logger.info(message)

            url = f'http://www.ask.com/web?q=@{self.domain}&pu=10&page={self.counter}'
            try:
                raw_html = dl.requesturl(url, useragent=self.user_agent)
                self.html += raw_html
                self.counter += 1
                helpers.mod_sleep(self.sleep, jitter=self.jitter)
            except Exception as e:
                error = f" [!] Fail during Request to Ask (Check Connection): {e}"
                self.logger.error(error)
                print(helpers.color(error, warning=True))

    def get_emails(self):
        """
        Извлекает email адреса из HTML с помощью парсера.
        """
        parser = Parser.Parser(self.html)
        final_output, html_results = parser.extended_clean(self.name)
        json_results = parser.build_json(final_output, self.name)
        self.logger.debug('AskSearch completed search')
        return final_output, html_results, json_results


# Пример использования
if __name__ == "__main__":
    ask_search = AskSearch("example.com", verbose=True)
    results = ask_search.execute()
    print(results)
