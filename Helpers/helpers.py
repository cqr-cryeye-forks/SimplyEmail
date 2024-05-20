#!/usr/bin/env python

import os
import textwrap
import logging
import time
import magic
import json
import configparser
import collections
import random
from fake_useragent import UserAgent


def dict_to_json(input_dict):
    """
    Takes in a list of dict items.
    Converts them to json and returns list of json obj.
    """
    return [json.dumps(item) for item in input_dict]


def get_search_id():
    return time.strftime("%d%m%Y%H%M%S")


def get_datetime():
    return time.strftime("%d/%m/%Y %H:%M:%S")


def json_list_to_json_obj(input_json_list, domain):
    """
    Takes a list of json objects,
    places them in a key and returns the data.
    """
    current_date = time.strftime("%d/%m/%Y")
    current_time = time.strftime("%H:%M:%S")
    current_tool = "SimplyEmail"
    config = configparser.ConfigParser()
    config.read('Common/SimplyEmail.ini')
    current_version = config['GlobalSettings']['Version']
    count = len(input_json_list)
    dic = collections.OrderedDict({
        "domain_of_collection": domain,
        "data_of_collection": current_date,
        "time_of_collection": current_time,
        "tool_of_collection": current_tool,
        "current_version": current_version,
        "email_collection_count": count,
        "emails": input_json_list,
    })
    return json.dumps(dic, indent=4, sort_keys=True)


def color(string, status=True, warning=False, bold=True, blue=False, firewall=False):
    # Change text color for the linux terminal, defaults to green.
    attr = ['32'] if status else []
    if warning:
        attr.append('31')
    if bold:
        attr.append('1')
    if firewall:
        attr.append('33')
    if blue:
        attr.append('34')
    return f'\x1b[{";".join(attr)}m{string}\x1b[0m'


def format_long(title, message, front_tab=True, spacing=16):
    """
    Print a long title:message with our standardized formatting.
    Wraps multiple lines into a nice paragraph format.
    """
    lines = textwrap.wrap(textwrap.dedent(message).strip(), width=50)
    formatted_message = ""

    if lines:
        title_format = '{0: <%s}' % spacing
        formatted_message += f"\t{title_format.format(title)}{lines[0]}" if front_tab else f" {title_format.format(title)}{lines[0]}"
        for line in lines[1:]:
            formatted_message += f"\n\t{' ' * spacing}{line}" if front_tab else f"\n{' ' * spacing}{line}"
    return formatted_message


def directory_listing(directory):
    # Returns a list of dir's of results
    return [os.path.join(dir, f) for dir, _, files in os.walk(directory) for f in files if
            os.path.exists(os.path.join(dir, f))]


def split_email(email):
    return email.lower().split("@")


def get_user_agent():
    # gets a random useragent and returns the UA
    return UserAgent().random


def mod_sleep(delay, jitter=0):
    # Quick Snipit From EmPyre Agent (@HarmJ0y)
    jitter = abs(jitter) if jitter < 0 else min(jitter, int(1 / jitter))
    sleep_time = random.randint(int((1.0 - jitter) * delay), int((1.0 + jitter) * delay))
    time.sleep(sleep_time)


def get_file_type(path):
    return magic.from_file(str(path))


#######################
# Setup Logging Class #
#######################

class log(object):
    """simple logging testing and dev"""

    def __init__(self):
        self.name = ".SimplyEmail.log"

    def start(self):
        logger = logging.getLogger("SimplyEmail")
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(self.name)
        formatter = logging.Formatter('%(asctime)s-[%(name)s]-[%(levelname)s]- %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        logger.info("Program started")
        logging.captureWarnings(True)
        logger.info("Set Logging Warning Capture: True")

    def info_msg(self, message, module_name):
        self._log_msg(message, module_name, level="info")

    def warning_msg(self, message, module_name):
        self._log_msg(message, module_name, level="warning")

    def _log_msg(self, message, module_name, level="info"):
        try:
            logger = logging.getLogger(f'SimplyEmail.{module_name}')
            getattr(logger, level)(str(message))
        except Exception as e:
            print(e)
