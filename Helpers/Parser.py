#!/usr/bin/env python
# encoding=utf8

import os
import re
import logging
import subprocess
import time
from random import randint


class Parser:

    def __init__(self, input_data):
        self.input_data = input_data
        self.logger = logging.getLogger("SimplyEmail.Parser")

    def generic_clean(self):
        tags_to_remove = ['<em>', '<b>', '</b>', '</em>', '<strong>', '</strong>', '<tr>', '</tr>', '</a>']
        for tag in tags_to_remove:
            self.input_data = self.input_data.replace(tag, '')

        replacements = {
            '%2f': ' ', '%3a': ' ',
            ',': ' ', '>': ' ', ':': ' ', '=': ' ',
            '<': ' ', '/': ' ', '\\': ' ', ';': ' ', '&': ' ',
            '%3A': ' ', '%3D': ' ', '%3C': ' ', '&#34': ' ', '"': ' '
        }
        for old, new in replacements.items():
            self.input_data = self.input_data.replace(old, new)

    def url_clean(self):
        self.input_data = self.input_data.replace('<em>', '').replace('</em>', '').replace('%2f', ' ').replace('%3a',
                                                                                                               ' ')
        chars_to_remove = ['<', '>', ':', '=', ';', '&', '%3A', '%3D', '%3C']
        for char in chars_to_remove:
            self.input_data = self.input_data.replace(char, ' ')

    def remove_unicode(self):
        try:
            if self.input_data is None:
                return self.input_data
            if isinstance(self.input_data, str):
                self.input_data = self.input_data.encode('ascii', 'ignore').decode('ascii')
            else:
                self.input_data = self.input_data.encode('ascii', 'ignore').decode('ascii')
            remove_ctrl_chars_regex = re.compile(r'[^\x20-\x7e]')
            self.input_data = remove_ctrl_chars_regex.sub('', self.input_data)
        except Exception as e:
            self.logger.error('UTF8 decoding issues: ' + str(e))

    def find_emails(self):
        return re.findall(r'[\w\.-]+@[\w\.-]+', self.input_data)

    def grep_find_emails(self):
        final_output = []
        start_file_name = f"temp_{randint(1000, 999999)}.txt"
        end_file_name = f"temp_{randint(1000, 999999)}.txt"

        try:
            with open(start_file_name, "w") as myfile:
                myfile.write(self.input_data)

            ps = subprocess.Popen(('grep', "@", start_file_name), stdout=subprocess.PIPE)
            val = subprocess.check_output(("grep", "-i", "-o", '[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}'),
                                          stdin=ps.stdout)
            self.email_evasion_check(ps)
        except Exception as e:
            self.logger.error('Grep email finding issue: ' + str(e))
        finally:
            if os.path.exists(start_file_name):
                os.remove(start_file_name)

        if val:
            with open(end_file_name, "w") as myfile:
                myfile.write(val.decode())
            with open(end_file_name, "r") as myfile:
                output = myfile.readlines()
            if os.path.exists(end_file_name):
                os.remove(end_file_name)
            for item in output:
                final_output.append(item.strip())
        return final_output

    def email_evasion_check(self, data):
        try:
            subprocess.check_output(("grep", "-i", "-o", '[A-Z0-9._%+-]+\\s+@+\\s+[A-Z0-9.-]+\\.[A-Z]{2,4}'),
                                    stdin=data.stdout)
        except Exception as e:
            self.logger.error('Email evasion check issue: ' + str(e))

    def clean_list_output(self):
        return [item.rstrip("\n") for item in self.input_data]

    def build_results(self, input_list, module_name):
        module_name = f'"{module_name}"'
        return [f"{{'Email': '{email}', 'Source': {module_name}}}" for email in input_list]

    def build_json(self, input_list, module_name):
        current_date = time.strftime("%d/%m/%Y")
        current_time = time.strftime("%H:%M:%S")
        return [
            {
                'email': email,
                'module_name': module_name,
                'collection_time': current_time,
                'collection_data': current_date,
            }
            for email in input_list
        ]

    def extended_clean(self, module_name):
        self.generic_clean()
        self.url_clean()
        final_output = self.grep_find_emails()
        html_results = self.build_results(final_output, module_name)
        return final_output, html_results
