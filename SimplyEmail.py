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
    parser.add_argument("--email", metavar="company.com", default="",
                        help="Set required email addr user, ex ale@email.com")
    parser.add_argument("--list-modules", action='store_true', help="List the current Modules Loaded")
    parser.add_argument("--test-module", metavar="html / flickr / google",
                        help="Test individual module (For Linting)")
    parser.add_argument("--no-scope", action='store_true',
                        help="Set this to enable 'No-Scope' of the email parsing")
    parser.add_argument("--name-generation", action='store_true', help="Set this to enable Name Generation")
    parser.add_argument("--verify", action='store_true', help="Set this to enable SMTP server email verify")
    parser.add_argument("--verbose", action='store_true', help="Set this switch for verbose output of modules")
    parser.add_argument("--json", metavar='json-emails.txt', default="",
                        help="Set this switch for JSON output to specific file")
    parser.add_argument('--help', '-h', action="store_true", help="Show this help message and exit")

    args = parser.parse_args()
    if args.help:
        parser.print_help()
        exit()

    return args.all, args.email, args.list_modules, args.test_module, args.no_scope, args.name_generation, args.verify, args.verbose, args.json


def task_starter(version):
    log = helpers.log()
    log.start()
    cli_all, cli_domain, cli_list, cli_test, cli_scope, cli_names, cli_verify, cli_verbose, cli_json = cli_parser()
    cli_domain = cli_domain.lower()
    task = TaskController.Conducter()
    task.load_modules()

    if cli_list:
        log.infomsg("Tasked to List Modules", "Main")
        task.ListModules()
        version_check = VersionCheck.VersionCheck(version)
        version_check.version_request()
        exit()

    if not cli_domain:
        log.warningmsg("Domain not supplied", "Main")
        print(helpers.color("[*] No Domain Supplied to start up!\n", warning=True))
        exit()

    if cli_test:
        log.infomsg(f"Tasked to Test Module: {cli_test}", "Main")
        version_check = VersionCheck.VersionCheck(version)
        version_check.version_request()
        task.TestModule(cli_domain, cli_test, verbose=cli_verbose, scope=cli_scope, Names=cli_names, Verify=cli_verify,
                        json=cli_json)

    if cli_all:
        log.infomsg(f"Tasked to run all Modules on domain: {cli_domain}", "Main")
        version_check = VersionCheck.VersionCheck(version)
        version_check.version_request()
        task.TaskSelector(cli_domain, verbose=cli_verbose, scope=cli_scope, Names=cli_names, Verify=cli_verify,
                          json=cli_json)


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
    orc.title_screen()
    task_starter(version)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            exit()
        except SystemExit:
            exit()
