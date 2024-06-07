#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Inspired by theHarvester and the capabilities. This project is simply a learning experience of
# recon methods to obtain email address and the way you can go about it.
# Also I really wanted the ability to learn SQL, and make this tool multi-threaded!
#
# * = Require API Key
#
import argparse
import configparser
import pathlib
from typing import Final

from Helpers import helpers
from Helpers import VersionCheck
from Common import TaskController


def cli_parser():
    parser = argparse.ArgumentParser(description='''
        Email enumeration is an important phase of many operations that a pen-tester or
        Red Teamer goes through. There are tons of applications that do this but I wanted
        a simple yet effective way to get what Recon-Ng gets and theHarvester gets.
        ''')
    parser.add_argument("--all", action='store_true', help="Use all non-API methods to obtain Emails")
    parser.add_argument("--email", metavar="company.com", help="Set required email addr user, ex ale@email.com")
    parser.add_argument("--list-modules", dest="list", action='store_true', help="List the current Modules Loaded")
    parser.add_argument("--test-module", dest="test", metavar="html / flickr / google",
                        help="Test individual module (For Linting)")
    parser.add_argument("--no-scope", action='store_true',
                        help="Set this to enable 'No-Scope' of the email parsing")
    parser.add_argument("--name-generation", action='store_true', help="Set this to enable Name Generation")
    parser.add_argument("--verify", action='store_true', help="Set this to enable SMTP server email verify")
    parser.add_argument("--verbose", action='store_true', help="Set this switch for verbose output of modules")
    parser.add_argument("--json", metavar='json-emails.txt', help="Set this switch for JSON output to specific file")
    parser.add_argument("--output", help="Svae output in Json file. Example='data.json'")

    args = parser.parse_args()
    return args


def task_starter(version):
    log = helpers.log()
    log.start()
    args = cli_parser()

    MAIN_DIR: Final[pathlib.Path] = pathlib.Path(__file__).parent
    JSON_FILE: Final[pathlib.Path] = args.output / MAIN_DIR

    if args.email:
        cli_domain = args.email.lower()
    else:
        log.warning_msg("Domain not supplied", "Main")
        print(helpers.color("[*] No Domain Supplied to start up!\n", warning=True))
        exit()

    task = TaskController.Conducter()
    task.load_modules()

    if args.list:
        log.info_msg("Tasked to List Modules", "Main")
        task.ListModules()
        version_check = VersionCheck.VersionCheck(version)
        version_check.version_request()
        exit()

    task.TaskSelector(cli_domain, output=JSON_FILE)


def main():
    try:
        config = configparser.ConfigParser()
        config.read('Common/SimplyEmail.ini')
        version = config['GlobalSettings']['Version']
    except Exception as e:
        print(e)
        exit()

    orc = TaskController.Conducter()
    orc.title()
    task_starter(version)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
