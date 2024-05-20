#!/usr/bin/env python
import requests
import configparser
from Helpers import helpers
import logging


class VersionCheck:

    def __init__(self, version):
        self.config = configparser.ConfigParser()
        self.logger = logging.getLogger("SimplyEmail.VersionCheck")
        self.version = str(version)

        self._load_config()

    def _load_config(self):
        """
        Загружает конфигурационный файл и устанавливает необходимые параметры.
        """
        try:
            self.config.read('Common/SimplyEmail.ini')
            self.start = self.config['GlobalSettings'].get('VersionRepoCheck', 'No')
            self.repo_location = self.config['GlobalSettings'].get('VersionRepoCheckLocation', '')
            self.user_agent = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, как Gecko) Chrome/39.0.2171.95 Safari/537.36'
            }
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")

    def version_request(self):
        """
        Отправляет запрос на проверку версии и сравнивает ее с текущей версией.
        """
        if self.start.lower() == "yes":
            self.logger.info("Version / Update request started")
            try:
                response = requests.get(self.repo_location, headers=self.user_agent, timeout=3)
                response.raise_for_status()

                latest_version = response.text.strip()
                if latest_version != self.version:
                    warning_msg = " [!] Newer Version Available, Re-Run Setup.sh to update!"
                    print(helpers.color(warning_msg, warning=True, bold=False))
                    self.logger.info("Version / Update returned newer Version Available")
                else:
                    self.logger.info("No updates available. Current version is up to date.")
            except requests.RequestException as e:
                error_msg = " [!] Fail during Request to Update/Version Check (Check Connection)"
                self.logger.error(f"{error_msg}: {e}")
                print(helpers.color(error_msg, warning=True))
            except Exception as e:
                self.logger.error(f"Unexpected error during version check: {e}")


# Пример использования
if __name__ == "__main__":
    version_check = VersionCheck("1.0.0")
    version_check.version_request()
