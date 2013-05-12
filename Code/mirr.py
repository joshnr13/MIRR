#!/usr/bin/env python
# -*- coding utf-8 -*-

import sys
import traceback
from collections import  OrderedDict
from annex import get_input_date, get_input_int, cached_property, memoize
from database import test_database_read
from simulations import run_one_iteration, run_all_iterations
from _mirr import Mirr

commands = OrderedDict()
commands['0'] = 'stop'
commands['1'] = 'charts_monthly'
commands['2'] = 'charts_yearly'
commands['3'] = 'report_is'
commands['4'] = 'report_bs'
commands['5'] = 'report_isbscf'
commands['6'] = 'report_isbscf_xl'
commands['7'] = 'report_isbscf_xl_yearly'
commands['8'] = 'print_equipment'
commands['9'] = 'outputPrimaryEnergy'
commands['10'] = 'outputElectricityProduction'
commands['11'] = 'run_1_sumulation'
commands['12'] = 'run_simulations'
commands['13'] = 'read_db'


class Interface():
    def __init__(self):
        pass

    @memoize
    def getMirr(self):
        return Mirr()

    def charts_monthly(self):
        self.getMirr().o.plot_charts_monthly()

    def charts_yearly(self):
        self.getMirr().o.plot_charts_yearly()

    def report_is(self):
        self.getMirr().o.prepare_report_IS()

    def report_bs(self):
        self.getMirr().o.prepare_report_BS()

    def report_isbscf(self, yearly=False):
        self.getMirr().o.prepare_report_IS_BS_CF_IRR(yearly)

    def report_isbscf_xl(self, yearly=False):
        try:
            import openpyxl
            self.getMirr().o.prepare_report_IS_BS_CF_IRR(excel=True, yearly=yearly)
        except ImportError:
            print "Cannot import python module openpyxl. No excel support for reports!"
            self.report_isbscf(yearly=yearly)

    def report_isbscf_xl_yearly(self):
        return  self.report_isbscf_xl(yearly=True)

    def print_equipment(self):
        self.getMirr().technology_module.print_equipment()

    def get_inputs(self):
        def_start = self.getMirr().main_config.getStartDate()
        def_end = self.getMirr().main_config.getEndDate()
        def_res = self.getMirr().main_config.getResolution()

        memo = " (from %s to %s)" % (def_start,def_end)
        memo_res = " Enter resolution or press ENTER to use default %s" % (def_res, )

        start_date =  get_input_date(text="Start date" + memo, default=def_start)
        end_date =  get_input_date(text="End date" + memo, default=def_end)
        resolution = get_input_int(text=memo_res, default=def_res)

        return (start_date, end_date, resolution)


    def outputPrimaryEnergy(self):
        start_date, end_date, resolution = self.get_inputs()
        self.getMirr().energy_module.outputPrimaryEnergy(start_date, end_date, resolution)

    def outputElectricityProduction(self):
        start_date, end_date, resolution = self.get_inputs()
        self.getMirr().technology_module.outputElectricityProduction(start_date, end_date, resolution)

    def read_db(self):
        """Test reading results from Mongo"""
        test_database_read()

    def run_1_sumulation(self):
        """Test writing results to Mongo"""
        run_one_iteration()

    def run_simulations(self):
        run_all_iterations()


    def stop(self):
        raise KeyboardInterrupt("User selected command to exit")
    def no_such_method(self):
        print "So such function. Try again from allowed %s" % commands.values()
    def help(self):
        print "Alowed commands (Short name = full name) "
        for k, v in (commands.items()):
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

if __name__ == '__main__':

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

