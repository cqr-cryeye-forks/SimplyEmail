#!/usr/bin/env python
import configparser
import helpers
import dns.resolver
import socket
import smtplib


class VerifyEmail:
    """
    Класс для проверки email адресов и MX записей домена.
    """

    def __init__(self, emails, domain, verbose=False):
        self.emails = emails
        self.domain = domain
        self.verbose = verbose
        self.mxhost = {}
        self.final_list = []

        self._load_config()

    def _load_config(self):
        config = configparser.ConfigParser()
        try:
            config.read('Common/SimplyEmail.ini')
            self.user_agent = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, как Gecko) Chrome/39.0.2171.95 Safari/537.36'
            }
        except Exception as e:
            print(f"Error loading config: {e}")

    def verify_email(self, email):
        """
        Проверка валидности email адреса.
        """
        hostname = socket.gethostname()
        socket.setdefaulttimeout(10)
        server = smtplib.SMTP(timeout=10)
        server.set_debuglevel(0)

        try:
            if self.verbose:
                print(helpers.color(f"[*] Checking for valid email: {email}", firewall=True))

            server.connect(self.mxhost['Host'])
            server.helo(hostname)
            server.mail('email@gmail.com')
            code, _ = server.rcpt(email)
            server.quit()

            return code == 250
        except Exception as e:
            print(f"Error verifying email: {e}")
            return False

    def verify_smtp_server(self):
        """
        Проверка, является ли SMTP сервер "catch-all".
        """
        hostname = socket.gethostname()
        socket.setdefaulttimeout(10)
        server = smtplib.SMTP(timeout=10)
        server.set_debuglevel(0)
        address_to_verify = f"There.Is.Knowwaythiswillwork1234567@{self.domain}"

        try:
            server.connect(self.mxhost['Host'])
            server.helo(hostname)
            server.mail('email@gmail.com')
            code, _ = server.rcpt(address_to_verify)
            server.quit()

            return code != 250
        except Exception as e:
            print(f"Error verifying SMTP server: {e}")
            return False

    def get_mx(self):
        """
        Получение MX записей для домена.
        """
        try:
            if self.verbose:
                print(helpers.color("[*] Attempting to resolve MX records!", firewall=True))

            answers = dns.resolver(self.domain, 'MX')
            mx_records = [{'Host': str(rdata.exchange), 'Pref': int(rdata.preference)} for rdata in answers]
            self.mxhost = sorted(mx_records, key=lambda k: k['Pref'])[0]

            if self.verbose:
                print(helpers.color(f"[*] MX Host: {self.mxhost['Host']}", firewall=True))
        except Exception as e:
            print(helpers.color(f"[!] Failed to get MX record: {e}", warning=True))

    def execute_verify(self):
        """
        Выполнение проверки email адресов.
        """
        self.get_mx()
        is_valid_server = self.verify_smtp_server()

        if is_valid_server:
            for email in self.emails:
                if self.verify_email(email):
                    if self.verbose:
                        print(helpers.color(f"[!] Email seems valid: {email}", status=True))
                    self.final_list.append(email)
                else:
                    if self.verbose:
                        print(helpers.color(f"[!] Checks show email is not valid: {email}", firewall=True))
        else:
            print(helpers.color(f"[!] Checks show 'Server Is Catch All' on: {self.mxhost['Host']}", warning=True))

        return self.final_list
