#!/usr/bin/env python
import configparser
from Helpers import helpers
from Helpers.Download import Download


# Email layouts supported:
# {first}.{last} = alex.alex@domain.com
# {first}{last} = jamesharvey@domain.com
# {f}{last} = ajames@domain.com
# {f}.{last} = a.james@domain.com
# {first}{l} = jamesh@domain.com
# {first}.{l} = j.amesh@domain.com
# {first}_{last} = james_amesh@domain.com


class EmailFormat:
    """
    A simple class to detect Email Format.
    Using basic checks and EmailHunter.
    """

    def __init__(self, domain, verbose=False):
        self.domain = domain
        self.verbose = verbose
        self.config = self.load_config()
        self.user_agent = self.config.get('GlobalSettings', 'UserAgent')
        self.api_key = self.config.get('APIKeys', 'Hunter')
        self.email_type = self.config.get('Hunter', 'EmailType')
        self.type, self.etype = self.get_email_type()

    @staticmethod
    def load_config():
        config = configparser.ConfigParser()
        config.read('Common/SimplyEmail.ini')
        return config

    def get_email_type(self):
        email_type_map = {
            "Both": ("", "total"),
            "Personal": ("&type=personal", "personal_emails"),
            "Generic": ("&type=generic", "generic_emails")
        }
        return email_type_map.get(self.email_type, ("", "total"))

    def email_hunter_detect(self):
        """
        A function to use EmailHunter to use their
        JSON API to detect the email format.
        """
        try:
            dl = Download.Download(self.verbose)
            url = f"https://api.hunter.io/v2/domain-search?domain={self.domain}{self.type}&limit=100&offset=0&api_key={self.api_key}"
            response = dl.requesturl(url, useragent=self.user_agent, raw=True)
            results = response.json()
            pattern = results['data'].get('pattern')
            if pattern:
                return pattern
            else:
                if self.verbose:
                    print(helpers.color(' [!] No pattern detected via EmailHunter API', firewall=True))
                return False
        except Exception as e:
            print(helpers.color(f"[!] Major issue with EmailHunter Search: {str(e)}", warning=True))

    @staticmethod
    def build_name(clean_name, format, raw=False):
        """
        Will help build names and return
        all required name formats for the email
        to be built.
        """
        first_name, last_name = clean_name
        first_initial = first_name[0]
        last_initial = last_name[0]

        formats = {
            '{f}.{last}': f"{first_initial}.{last_name}",
            '{f}{last}': f"{first_initial}{last_name}",
            '{first}{last}': f"{first_name}{last_name}",
            '{first}.{last}': f"{first_name}.{last_name}",
            '{first}{l}': f"{first_name}{last_initial}",
            '{first}.{l}': f"{first_name}.{last_initial}",
            '{first}_{last}': f"{first_name}_{last_name}",
            '{first}': first_name
        }

        if raw:
            return first_name, first_initial, last_name, last_initial
        return formats.get(format, "")

    def email_detect(self, clean_names, domain, final_emails):
        """
        if EmailHunterDetect cant find a
        format this function will build everytype of
        email and compare for a model.
        """
        final_result = []
        formats = [
            '{f}{last}', '{f}.{last}', '{first}{last}',
            '{first}.{last}', '{first}.{l}', '{first}{l}',
            '{first}_{last}', '{first}'
        ]

        for format in formats:
            set_result = False
            for name in clean_names:
                built_email = self.build_name(name, format) + f"@{domain}"
                count = final_emails.count(built_email.lower())
                if count > 0:
                    if self.verbose:
                        print(helpers.color(f" [*] Email format matched {format}: {built_email}", firewall=True))
                    if not set_result:
                        final_result.append(format)
                        set_result = True
        return final_result

    def email_builder(self, clean_names, domain, format, verbose=True):
        """
        Builds emails and returns a list of emails.
        """
        built_emails = []
        if len(clean_names) < 0:
            return False

        for name in clean_names:
            try:
                built_email = self.build_name(name, format) + f"@{domain}"
                if built_email:
                    if verbose:
                        print(helpers.color(f" [*] Email built: {built_email}", firewall=True))
                    built_emails.append(built_email)
            except Exception as e:
                print(e)

        if built_emails:
            return built_emails
        else:
            if verbose:
                print(helpers.color(' [!] No names built, please do a sanity check!', warning=True))
            return False
