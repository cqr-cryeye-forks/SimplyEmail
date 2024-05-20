# -*- coding: utf-8 -*-
import configparser
import glob
import importlib.util
import os
import multiprocessing
import threading
import sys
import warnings
import time
import subprocess
import logging
import datetime
from typing import Any

# Internal modules
from Helpers import helpers
from Helpers import messages
from Helpers import HtmlBootStrapTheme
from Helpers import VerifyEmails
from Helpers import Connect6
from Helpers import EmailFormat
from Helpers import LinkedinNames


class Conducter:

    def __init__(self):
        self.modules = {}
        self.dmodules = {}
        self.Emails = []
        self.ConsumerList = []
        self.HtmlList = []
        self.JsonList = []
        self.Tasks = []
        self.ResultsList = []
        self.search_id = 0
        self.logger = logging.getLogger("SimplyEmail.TaskController")
        try:
            config = configparser.ConfigParser()
            config.read('Common/SimplyEmail.ini')
            self.version = config['GlobalSettings']['Version']
            self.logger.info(f"SimplyEmail Version set to: {self.version}")
            t = datetime.datetime.now()
            self.TimeDate = t.strftime("%Y%m%d-%H%M")
            self.logger.info(f"SimplyEmail started at: {self.TimeDate}")
        except Exception as e:
            print(e)

    def _execute_module_add_emails(self, Emails, Results_queue, Html_queue, Json_queue, HtmlResults, JsonResults):
        self.logger.debug("_execute_module_add_emails: adding emails to consumer queues")
        for Email in Emails:
            Results_queue.put(Email)
        for Email in HtmlResults:
            Html_queue.put(Email)
        for Email in JsonResults:
            Json_queue.put(Email)
        self.logger.debug("_execute_module_add_emails: completed adding emails to consumer queues")

    def _execute_api_module(self, Module) -> bool:
        self.logger.debug("_execute_api_module: checking for API key")
        if Module.apikeyv:
            e = f" [*] API module key loaded for: {Module.name}"
            print(helpers.color(e, status=True))
            self.logger.info("_execute_api_module: API key present")
            return True
        else:
            e = f" [*] No API module key loaded for: {Module.name}"
            print(helpers.color(e, firewall=True))
            self.logger.info("_execute_api_module: no API key present")
            return False

    def _execute_get_task(self, task_queue) -> Any | None:
        try:
            task = task_queue.get()
            self.logger.debug("_execute_get_task: process requested tasking")
            return task
        except Exception:
            self.logger.warning("_execute_get_task: task_queue.get() failed (unknown reason)")
            return None

    def ExecuteModule(self, Task_queue, Results_queue, Html_queue, Json_queue, domain, verbose=False):
        while True:
            Task = self._execute_get_task(Task_queue)
            if Task is None:
                self.logger.info("_execute_get_task: task_queue is empty (shutting down process)")
                break
            try:
                Task = self.modules[Task]
                Module = Task.ClassName(domain, verbose=verbose)
                name = f" [*] Starting: {Module.name}"
                print(helpers.color(name, status=True))
                try:
                    if Module.apikey and not self._execute_api_module(Module):
                        break
                    Emails, HtmlResults, JsonResults = Module.execute()
                    if Emails:
                        count = len(Emails)
                        self._execute_module_add_emails(Emails, Results_queue, Html_queue, Json_queue, HtmlResults, JsonResults)
                        count = len(Emails)
                        messages.email_count(count, Module.name)
                    else:
                        Message = f" [*] {Module.name} has completed with no Email(s)"
                        print(helpers.color(Message, status=True))
                except Exception as e:
                    error = f" [!] Error During Runtime in Module {Module.name}: {e}"
                    print(helpers.color(error, warning=True))
            except Exception as e:
                error = f" [!] Error Loading Module: {e}"
                print(helpers.color(error, warning=True))

    def printer(self, FinalEmailList, Domain, VerifyEmail=False, NameEmails=False):
        Date = time.strftime("%d/%m/%Y")
        Time = time.strftime("%I:%M:%S")
        buildpath = f"{Domain}-{self.TimeDate}"
        os.makedirs(buildpath, exist_ok=True)
        PrintTitle = (
            "\t----------------------------------\n"
            f"\tEmail Recon: {Date} {Time}\n"
            "\t----------------------------------\n"
        )
        if NameEmails:
            x = 0
            NamePath = f"{buildpath}/Email_List_Built.txt"
            for item in FinalEmailList:
                item += "\n"
                if x == 0:
                    try:
                        with open(NamePath, "a") as myfile:
                            myfile.write(PrintTitle)
                    except Exception as e:
                        print(e)
                try:
                    with open(NamePath, "a") as myfile:
                        myfile.write(item)
                    x += 1
                except Exception as e:
                    print(e)
            print(helpers.color(" [*] Completed output!", status=True))
            self.logger.info("Version / Update request started")
            return x
        elif VerifyEmail:
            x = 0
            VerPath = f"{buildpath}/Email_List_Verified.txt"
            for item in FinalEmailList:
                item += "\n"
                if x == 0:
                    try:
                        with open(VerPath, "a") as myfile:
                            myfile.write(PrintTitle)
                    except Exception as e:
                        print(e)
                try:
                    with open(VerPath, "a") as myfile:
                        myfile.write(item)
                    x += 1
                except Exception as e:
                    print(e)
            print(helpers.color(" [*] Completed output!", status=True))
            return x
        else:
            x = 0
            ListPath = f"{buildpath}/Email_List.txt"
            for item in FinalEmailList:
                item += "\n"
                if x == 0:
                    try:
                        with open(ListPath, "a") as myfile:
                            myfile.write(PrintTitle)
                    except Exception as e:
                        print(e)
                try:
                    with open(ListPath, "a") as myfile:
                        myfile.write(item)
                    x += 1
                except Exception as e:
                    print(e)
            print(helpers.color(" [*] Completed output!", status=True))
            return x

    def HtmlPrinter(self, HtmlFinalEmailList, Domain):
        self.logger.debug("HTML Printer started")
        buildpath = f"{Domain}-{self.TimeDate}"
        Html = HtmlBootStrapTheme.HtmlBuilder(HtmlFinalEmailList, Domain)
        Html.build_html()
        Html.output_html(buildpath)

    def JsonPrinter(self, JsonFinalEmailList, FullPath, Domain):
        self.logger.debug("Json Printer started")
        json_data = helpers.json_list_to_json_obj(JsonFinalEmailList, Domain)
        if json_data:
            self.logger.debug(f"JSON wrote file: {FullPath}")
            with open(FullPath, 'w') as file:
                file.write(json_data)

    def CleanResults(self, domain, scope=False):
        self.logger.debug("Clean Results started")
        SecondList = []
        HtmlSecondList = []
        if scope:
            for item in self.ConsumerList:
                SecondList.append(item)
        else:
            for item in self.ConsumerList:
                if domain.lower() in helpers.split_email(item)[-1]:
                    SecondList.append(item)
        FinalList = []
        HtmlFinalList = []
        if scope:
            for item in self.HtmlList:
                HtmlSecondList.append(item)
        else:
            for item in self.HtmlList:
                if domain.lower() in helpers.split_email(item)[-1]:
                    HtmlSecondList.append(item)
        for item in SecondList:
            if item.lower() not in FinalList:
                FinalList.append(item.lower())
        for item in HtmlSecondList:
            if item not in HtmlFinalList:
                HtmlFinalList.append(item)
        print(helpers.color(" [*] Completed cleaning results", status=True))
        self.logger.info("Completed cleaning results")
        return FinalList, HtmlFinalList

    def CleanJsonResults(self, domain, scope=False):
        self.logger.debug("JSON Clean Results started")
        SecondList = []
        FinalList = []
        if scope:
            for item in self.JsonList:
                SecondList.append(item)
        else:
            for item in self.JsonList:
                if domain.lower() in item['email'].lower():
                    SecondList.append(item)
        for item in SecondList:
            if item not in FinalList:
                FinalList.append(item)
        return FinalList

    def Consumer(self, Results_queue, verbose):
        while True:
            try:
                item = Results_queue.get()
                if item is None:
                    break
                self.ConsumerList.append(item)
            except Exception as e:
                if verbose:
                    print(e)

    def HtmlConsumer(self, Html_queue, verbose):
        while True:
            try:
                item = Html_queue.get()
                if item is None:
                    break
                self.HtmlList.append(item)
            except Exception as e:
                if verbose:
                    print(e)

    def JsonConsumer(self, Json_queue, verbose):
        while True:
            try:
                item = Json_queue.get()
                if item is None:
                    break
                self.JsonList.append(item)
            except Exception as e:
                if verbose:
                    print(e)

    def _task_queue_start(self) -> multiprocessing.Queue:
        self.logger.debug("_task_queue_start: starting task queue")
        try:
            Task_queue = multiprocessing.Queue()
            return Task_queue
        except Exception:
            self.logger.critical("_task_queue_start: FAILED to start task_queue")

    def _results_queue_start(self) -> multiprocessing.Queue:
        self.logger.debug("_results_queue_start: starting results queue")
        try:
            Results_queue = multiprocessing.Queue()
            return Results_queue
        except Exception:
            self.logger.critical("_results_queue_start: FAILED to start Results_queue")

    def _html_queue_start(self) -> multiprocessing.Queue:
        self.logger.debug("_html_queue_start: starting HTML queue")
        try:
            Html_queue = multiprocessing.Queue()
            return Html_queue
        except Exception:
            self.logger.critical("_html_queue_start: FAILED to start Html_queue")

    def _json_queue_start(self) -> multiprocessing.Queue:
        self.logger.debug("_json_queue_start: starting JSON queue")
        try:
            Json_queue = multiprocessing.Queue()
            return Json_queue
        except Exception:
            self.logger.critical("_json_queue_start: FAILED to start Json_queue")

    def TaskSelector(self, domain, verbose=False, scope=False, Names=False, json="", Verify=False):
        self.logger.debug(f"Starting TaskSelector for: {domain}")
        Task_queue = self._task_queue_start()
        Results_queue = self._results_queue_start()
        Html_queue = self._html_queue_start()
        Json_queue = self._json_queue_start()

        Config = configparser.ConfigParser()
        Config.read("Common/SimplyEmail.ini")
        total_proc = int(Config['ProcessConfig']['TotalProcs'])
        self.logger.debug(f"TaskSelector processor set to: {total_proc}")

        for Task in self.modules:
            Task_queue.put(Task)

        if total_proc > len(self.modules):
            total_proc = len(self.modules)
        for _ in range(total_proc):
            Task_queue.put(None)

        procs = []
        for _ in range(total_proc):
            proc = multiprocessing.Process(
                target=self.ExecuteModule, args=(Task_queue, Results_queue, Html_queue, Json_queue, domain, verbose))
            proc.daemon = True
            proc.start()
            procs.append(proc)

        t = threading.Thread(target=self.Consumer, args=(Results_queue, verbose,))
        t.daemon = True
        t.start()

        t2 = threading.Thread(target=self.HtmlConsumer, args=(Html_queue, verbose,))
        t2.daemon = True
        t2.start()

        t3 = threading.Thread(target=self.JsonConsumer, args=(Json_queue, verbose,))
        t3.daemon = True
        t3.start()

        while True:
            LeftOver = multiprocessing.active_children()
            time.sleep(1)
            if len(LeftOver) == 0:
                time.sleep(1)
                Results_queue.put(None)
                Html_queue.put(None)
                Json_queue.put(None)
                try:
                    JsonFinalEmailList = self.CleanJsonResults(domain, scope)
                    FinalEmailList, HtmlFinalEmailList = self.CleanResults(domain, scope)
                except Exception as e:
                    error = f" [!] Something went wrong with parsing results: {e}"
                    print(helpers.color(error, warning=True))
                    self.logger.critical(f"Something went wrong with parsing results: {e}")
                try:
                    if not json:
                        FinalCount = self.printer(FinalEmailList, domain)
                except Exception as e:
                    error = f" [!] Something went wrong with outputting results: {e}"
                    print(helpers.color(error, warning=True))
                    self.logger.critical(f"Something went wrong with outputting results: {e}")
                try:
                    if json:
                        self.JsonPrinter(JsonFinalEmailList, json, domain)
                    else:
                        self.HtmlPrinter(HtmlFinalEmailList, domain)
                except Exception as e:
                    error = f" [!] Something went wrong with HTML results: {e}"
                    print(helpers.color(error, warning=True))
                    self.logger.critical(f"Something went wrong with HTML results: {e}")
                break
        for p in procs:
            p.join()
            self.logger.debug("TaskSelector processes joined!")
        Task_queue.close()
        Results_queue.close()
        Html_queue.close()
        Json_queue.close()
        BuiltNameCount = 0
        try:
            if Names and not json:
                BuiltNames = self.NameBuilder(domain, FinalEmailList, Verbose=verbose)
                BuiltNameCount = len(BuiltNames)
            if not Names:
                BuiltNames = []
            if Verify:
                val = self.VerifyScreen()
                if val:
                    email = VerifyEmails.VerifyEmail(FinalEmailList, BuiltNames, domain)
                    VerifiedList = email.execute_verify()
                    if VerifiedList:
                        self.printer(FinalEmailList, domain, VerifyEmail=Verify)
        except Exception as e:
            print(e)
        try:
            if Names and BuiltNames:
                self.printer(BuiltNames, domain, NameEmails=True)
        except Exception as e:
            error = f" [!] Something went wrong with outputting results of Built Names: {e}"
            print(helpers.color(error, warning=True))
        if not json:
            self.CompletedScreen(FinalCount, BuiltNameCount, domain)

    def TestModule(self, domain, module, verbose=False, scope=False, Names=False, json='', Verify=False):
        self.logger.debug(f"Starting TaskSelector for: {domain}")
        Config = configparser.ConfigParser()
        Config.read("Common/SimplyEmail.ini")
        total_proc = 1
        self.logger.debug(f"Test TaskSelector processor set to: {total_proc}")
        Task_queue = self._task_queue_start()
        Results_queue = self._results_queue_start()
        Html_queue = self._html_queue_start()
        Json_queue = self._json_queue_start()

        for Task in self.modules:
            if module in Task:
                Task_queue.put(Task)
        for _ in range(total_proc):
            Task_queue.put(None)

        procs = []
        for _ in range(total_proc):
            proc = multiprocessing.Process(
                target=self.ExecuteModule, args=(Task_queue, Results_queue, Html_queue, Json_queue, domain, verbose))
            proc.daemon = True
            proc.start()
            procs.append(proc)

        t = threading.Thread(target=self.Consumer, args=(Results_queue, verbose,))
        t.daemon = True
        t.start()

        t2 = threading.Thread(target=self.HtmlConsumer, args=(Html_queue, verbose,))
        t2.daemon = True
        t2.start()

        t3 = threading.Thread(target=self.JsonConsumer, args=(Json_queue, verbose,))
        t3.daemon = True
        t3.start()

        while True:
            LeftOver = multiprocessing.active_children()
            time.sleep(1)
            if len(LeftOver) == 0:
                time.sleep(1)
                Results_queue.put(None)
                Html_queue.put(None)
                Json_queue.put(None)
                try:
                    JsonFinalEmailList = self.CleanJsonResults(domain, scope)
                    FinalEmailList, HtmlFinalEmailList = self.CleanResults(domain, scope)
                except Exception as e:
                    error = f" [!] Something went wrong with parsing results: {e}"
                    print(helpers.color(error, warning=True))
                    self.logger.critical(f"Something went wrong with parsing results: {e}")
                try:
                    if not json:
                        FinalCount = self.printer(FinalEmailList, domain)
                except Exception as e:
                    error = f" [!] Something went wrong with outputting results: {e}"
                    print(helpers.color(error, warning=True))
                    self.logger.critical(f"Something went wrong with outputting results: {e}")
                try:
                    if json:
                        self.JsonPrinter(JsonFinalEmailList, json, domain)
                    else:
                        self.HtmlPrinter(HtmlFinalEmailList, domain)
                except Exception as e:
                    error = f" [!] Something went wrong with HTML results: {e}"
                    print(helpers.color(error, warning=True))
                    self.logger.critical(f"Something went wrong with HTML results: {e}")
                break
        for p in procs:
            p.join()
        Task_queue.close()
        Results_queue.close()
        Html_queue.close()
        Json_queue.close()
        BuiltNameCount = 0
        try:
            if Names and not json:
                BuiltNames = self.NameBuilder(domain, FinalEmailList, Verbose=verbose)
                BuiltNameCount = len(BuiltNames)
            if not Names:
                BuiltNames = []
            if Verify:
                val = self.VerifyScreen()
                if val:
                    email = VerifyEmails.VerifyEmail(FinalEmailList, BuiltNames, domain)
                    VerifiedList = email.execute_verify()
                    if VerifiedList:
                        self.printer(FinalEmailList, domain, VerifyEmail=Verify)
        except Exception as e:
            print(e)
        try:
            if Names and BuiltNames:
                self.printer(BuiltNames, domain, NameEmails=True)
        except Exception as e:
            error = f" [!] Something went wrong with outputting results of Built Names: {e}"
            print(helpers.color(error, warning=True))
        if not json:
            self.CompletedScreen(FinalCount, BuiltNameCount, domain)

    def NameBuilder(self, domain, emaillist, Verbose=False) -> list:
        self.logger.debug("Starting NameBuilder")
        self.title()
        ValidFormat = ['{first}.{last}', '{first}{last}', '{f}{last}', '{f}.{last}', '{first}{l}', '{first}_{last}', '{first}']
        print(" [*] Now attempting to build Names:\n")
        CleanNames = []

        self.logger.debug("Starting LinkedInScraper for names")
        Li = LinkedinNames.LinkedinScraper(domain, Verbose=Verbose)
        LNames = Li.linked_in_names()
        if LNames:
            e = f' [*] LinkedinScraper has Gathered: {len(LNames)} Names'
            print(helpers.color(e, status=True))
            self.logger.info(f"LinkedInScraper has Gathered: {len(LNames)}")
            for raw in LNames:
                try:
                    name = Li.linked_in_clean(raw)
                    if name:
                        CleanNames.append(name)
                except Exception as e:
                    print(e)
                    self.logger.error(f"Issue cleaning LinkedInNames: {e}")

        c6 = Connect6.Connect6Scraper(domain, Verbose=Verbose)
        urllist = c6.connect6_auto_url()
        self.title()
        print(helpers.color(" [*] Now Starting Connect6 Scrape:"))
        self.logger.info("Now starting Connect6 scrape")
        if urllist:
            line = (
                f" [*] SimplyEmail has attempted to find correct URL for Connect6:\n"
                f"     URL detected: {helpers.color(urllist[0], status=True)}"
            )
            print(line)
            Question = " [>] Is this URL correct?: "
            Answer = input(helpers.color(Question, bold=False))
            if Answer.upper() in "YES":
                Names = c6.connect6_download(urllist[0])
                if Names:
                    e = f' [*] Connect6 has Gathered: {len(Names)} Names'
                    print(helpers.color(e, status=True))
                    for raw in Names:
                        name = c6.connect6_parse_name(raw)
                        if name:
                            CleanNames.append(name)
            else:
                while True:
                    for item in urllist:
                        print(f"    Potential URL: {item}")
                    e = f' [!] GoogleDork This: site:connect6.com "{domain}"'
                    print(helpers.color(e, bold=False))
                    print(" [-] Commands Supported: (B) ack - (R) etry")
                    Question = " [>] Please Provide a URL: "
                    Answer = input(helpers.color(Question, bold=False))
                    if Answer.upper() in "BACK":
                        e = " [!] Skipping Connect6 Scrape!"
                        print(helpers.color(e, firewall=True))
                        break
                    if Answer:
                        break
                if Answer.upper() != "B":
                    Names = c6.connect6_download(Answer)
                    if Names:
                        e = f' [*] Connect6 has Gathered: {len(Names)} Names'
                        print(helpers.color(e, status=True))
                        for raw in Names:
                            name = c6.connect6_parse_name(raw)
                            if name:
                                CleanNames.append(name)
        else:
            line = f" [*] SimplyEmail has attempted to find correct URL for Connect6:\n     URL was not detected!"
            print(line)
            e = f' [!] GoogleDork This: site:connect6.com "{domain}"'
            print(helpers.color(e, bold=False))
            while True:
                print(" [-] Commands Supported: (B) ack - (R) etry")
                Question = " [>] Please Provide a URL: "
                Answer = input(helpers.color(Question, bold=False))
                if Answer.upper() in "BACK":
                    e = " [!] Skipping Connect6 Scrape!"
                    print(helpers.color(e, firewall=True))
                    break
                if Answer:
                    break
            if Answer.upper() != "B":
                Names = c6.connect6_download(Answer)
                if Names:
                    e = f' [*] Connect6 has Gathered: {len(Names)} Names'
                    print(helpers.color(e, status=True))
                    for raw in Names:
                        name = c6.connect6_parse_name(raw)
                        if name:
                            CleanNames.append(name)

        self.title()
        print(helpers.color(' [*] Names have been built:', status=True))
        print(helpers.color(' [*] Attempting to resolve email format', status=True))
        Em = EmailFormat.EmailFormat(domain, Verbose=Verbose)
        Format = Em.email_hunter_detect()
        if Format:
            e = f' [!] Auto detected the format: {Format}'
            print(helpers.color(e, status=True))
        if not Format:
            print(helpers.color(" [*] Now attempting to manually detect format (slow)!"))
            Format = Em.email_detect(CleanNames, domain, emaillist)
            if len(Format) > 1:
                line = helpers.color(' [*] More than one email format was detected!\n')
                try:
                    for item in Format:
                        line += f'   * Format: {item}\n'
                    print(line)
                except:
                    print(helpers.color(" [*] No email samples gathered to show.", firewall=True))
                line = ' [*] Here are a few samples of the emails obtained:\n'
                for i in range(1, 6):
                    try:
                        line += f'      {i}) {emaillist[i]} \n'
                    except:
                        pass
                print(line)
                while True:
                    s = False
                    Question = " [>] Please provide a valid format: "
                    Answer = input(helpers.color(Question, bold=False))
                    try:
                        for item in ValidFormat:
                            if str(Answer) == str(item):
                                Format = str(Answer)
                                s = True
                    except:
                        pass
                    if s:
                        break
            if len(Format) < 1:
                Format = False
            else:
                Format = str(Format[0])
        if not Format:
            print(helpers.color(' [!] Failed to resolve format of email', firewall=True))
            line = helpers.color(' [*] Available formats supported:\n', status=True)
            line += '     {first}.{last} = alex.alex@domain.com\n'
            line += '     {first}{last} = jamesharvey@domain.com\n'
            line += '     {f}{last} = ajames@domain.com\n'
            line += '     {f}.{last} = a.james@domain.com\n'
            line += '     {first}{l} = jamesh@domain.com\n'
            line += '     {first}.{l} = j.amesh@domain.com\n'
            line += '     {first}_{last} = james_amesh@domain.com\n'
            line += '     {first} = james@domain.com\n\n'
            print(line)
            if emaillist:
                line = ' [*] Here are a few samples of the emails obtained:\n'
                line += f'      1) {emaillist[0]}\n'
                try:
                    if emaillist[1]:
                        line += f'      2) {emaillist[1]}\n'
                    if emaillist[2]:
                        line += f'      3) {emaillist[2]}'
                except:
                    pass
                print(line)
            else:
                line = ' [*] No unique emails discovered to display (May have to go manual)!\n'
                print(helpers.color(line, firewall=True))
            while True:
                s = False
                Question = " [>] Please provide a valid format: "
                Answer = input(helpers.color(Question, bold=False))
                try:
                    for item in ValidFormat:
                        if str(Answer) == str(item):
                            Format = str(Answer)
                            s = True
                except:
                    pass
                if s:
                    break

        BuiltEmails = Em.email_builder(CleanNames, domain, Format, Verbose=Verbose)
        if BuiltEmails:
            return BuiltEmails

    def load_modules(self):
        warnings.filterwarnings('ignore', '.*Parent module*')
        x = 1
        for name in glob.glob('Modules/*.py'):
            if name.endswith(".py") and ("__init__" not in name):
                spec = importlib.util.spec_from_file_location(name.replace("/", ".").rstrip('.py'), name)
                loaded_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(loaded_module)
                self.logger.debug(f"Loading Module: {loaded_module}")
                self.modules[name] = loaded_module
                self.dmodules[x] = loaded_module
                x += 1
        return self.dmodules, self.modules

    def ListModules(self):
        print(helpers.color(" [*] Available Modules are:\n", blue=True))
        self.logger.debug("User Executed ListModules")
        x = 1
        ordList = []
        finalList = []
        for name in self.modules:
            parts = name.split("/")
            ordList.append(parts[-1])
        ordList = sorted(ordList)
        for name in ordList:
            name = f'Modules/{name}'
            finalList.append(name)
        for name in finalList:
            print(f"\t{x})\t{name: <24}")
            x += 1
        print("")

    def title(self):
        os.system('clear')
        self.logger.debug("Title executed")
        print(" ============================================================")
        print(f" Current Version: {self.version} | Website: CyberSyndicates.com")
        print(" ============================================================")
        print(" Twitter: @real_slacker007 |  Twitter: @Killswitch_gui")
        print(" ============================================================")

    def CompletedScreen(self, FinalCount, EmailsBuilt, domain):
        Config = configparser.ConfigParser()
        Config.read("Common/SimplyEmail.ini")
        TextSaveFile = Config['GlobalSettings']['SaveFile']
        HtmlSaveFile = Config['GlobalSettings']['HtmlFile']
        FinalEmailCount = int(EmailsBuilt) + int(FinalCount)

        Line = (
            " [*] Email reconnaissance has been completed:\n\n"
            f"   File Location: \t\t{os.getcwd()}/{domain}-{self.TimeDate}\n"
            f"   Unique Emails Found:\t\t{FinalCount}\n"
            f"   Emails Built from Names:\t{EmailsBuilt}\n"
            f"   Total Emails:\t\t{FinalEmailCount}\n"
            f"   Raw Email File:\t\t{TextSaveFile}\n"
            f"   HTML Email File:\t\t{HtmlSaveFile}\n"
            "   Built Email File:\t\tEmail_List_Built.txt\n"
            "   Verified Email File:\t\tEmail_List_Verified.txt\n"
            f"   Domain Performed:\t\t{domain}\n"
        )
        self.title()
        print(Line)

        Question = "[>] Would you like to launch the HTML report?: "
        Answer = input(helpers.color(Question, bold=False))
        Answer = Answer.upper()
        if Answer in "NO":
            sys.exit(0)
        if Answer in "YES":
            HtmlSaveFile = f"{domain}-{self.TimeDate}/{HtmlSaveFile}"
            subprocess.Popen(("firefox", HtmlSaveFile), stdout=subprocess.PIPE)

    def VerifyScreen(self) -> bool:
        self.title()
        self.logger.debug("VerifyScreen executed")
        line = (
            " [*] Email reconnaissance has been completed:\n\n"
            "    Email verification will allow you to use common methods\n"
            "    to attempt to enumerate if the email is valid.\n"
            "    This grabs the MX records, sorts and attempts to check\n"
            "    if the SMTP server sends a code other than 250 for known bad addresses\n"
        )
        print(line)
        Question = " [>] Would you like to verify email(s)?: "
        Answer = input(helpers.color(Question, bold=False))
        Answer = Answer.upper()
        if Answer in "NO":
            self.logger.info("User declined to run verify emails")
            return False
        if Answer in "YES":
            self.logger.info("User opted to verify emails")
            return True
