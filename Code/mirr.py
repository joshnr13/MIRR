from constants import report_directory
import sys
import datetime
import pylab
import numpy
import csv
import traceback

from collections import defaultdict, OrderedDict
from annex import Annuitet, last_day_month, next_month, first_day_month, cached_property, uniquify_filename, transponse_csv, add_header_csv, last_day_previous_month
from annex import accumulate

from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from ecm import EconomicModule
from report import Report
from main_config_reader import MainConfig

commands = {}

commands['0'] = 'stop'
commands['1'] = 'charts_monthly'
commands['2'] = 'charts_yearly'
commands['3'] = 'report_is'
commands['4'] = 'report_bs'
commands['5'] = 'report_isbscf'
commands['6'] = 'report_isbscf_xl'
commands['7'] = 'report_isbscf_xl_yearly'
commands['8'] = 'print_equipment'




class Interface():
    def __init__(self):
        main_config = MainConfig()
        self.energy_module = EnergyModule(main_config)
        self.technology_module = TechnologyModule(main_config, self.energy_module)
        self.subside_module = SubsidyModule(main_config)
        self.economic_module = EconomicModule(main_config, self.technology_module, self.subside_module)
        self.r = Report(main_config, self.economic_module)
        self.r.calc_report_values()

    def charts_monthly(self):
        self.r.plot_charts_monthly()
    def charts_yearly(self):
        self.r.plot_charts_yearly()
    def report_is(self):
        self.r.prepare_report_IS()
    def report_bs(self):
        self.r.prepare_report_BS()

    def report_isbscf(self, yearly=False):
        self.r.prepare_report_IS_BS_CF_IRR(yealy)

    def report_isbscf_xl(self, yearly=False):
        try:
            import openpyxl
            self.r.prepare_report_IS_BS_CF_IRR(excel=True, yearly=yearly)
        except ImportError:
            print "Cannot import python module openpyxl. No excel support for reports!"
            self.report_isbs(yearly=yearly)

    def report_isbscf_xl_yearly(self):
        return  self.report_isbscf_xl(yearly=True)

    def print_equipment(self):
        self.technology_module.print_equipment()

    def stop(self):
        raise KeyboardInterrupt("User selected command to exit")
    def no_such_method(self):
        print "So such function. Try again from allowed %s" % commands.values()
    def help(self):
        print "Alowed commands (Short name = full name) "
        for k, v in sorted(commands.items()):
            print "%s = %s" % (k, v)


def print_entered(line):
    if line in commands:
        print "Entered %s means %s" % (line, commands[line])
    else:
        print "Entered %s " % (line, )


def run_method(obj, line):
    if line in commands:
        method = getattr(obj, commands[line])
    else:
        method = getattr(obj, line, obj.no_such_method)
    method()


try:
    i = Interface()
    i.help()
    while True:
        line = raw_input('Prompt command (For exit: 0 or stop; For help: help): ').strip()
        print_entered(line)
        run_method(i, line)
except KeyboardInterrupt:
    print sys.exc_info()[1]
except:
    #print sys.exc_info()
    var = traceback.format_exc()
    print var

