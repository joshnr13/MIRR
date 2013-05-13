#!/usr/bin/env python
# -*- coding utf-8 -*-

import sys
import traceback
import openpyxl
from collections import  OrderedDict
from annex import get_input_date, get_input_int, cached_property, memoize
from database import test_database_read, get_and_show_irr_distribution
from simulations import run_one_iteration, run_all_iterations
from main_config_reader import MainConfig
from _mirr import Mirr

commands = OrderedDict()
i = 0
commands['0'] = 'stop'
commands['1'] = 'run_simulations'
commands['2'] = 'report_irr'
commands['3'] = 'report_isbscf'
commands['4'] = 'charts'
commands['5'] = 'print_equipment'
commands['6'] = 'outputPrimaryEnergy'
commands['7'] = 'outputElectricityProduction'

#commands['99'] = 'read_db'

"""run_simulations  - then it asks you how many
report_irr - makes graphs about IRR distribution and saves data
report_isbscf  - makes xls - yearly and monthly for last set written to the database
charts - makes monthly and yearly charts for the last set written to the database
"""

class Interface():
    def __init__(self):
        pass

    @memoize
    def getMirr(self):
        return Mirr()

    def charts(self):
        self.getMirr().o.plot_charts_monthly()
        self.getMirr().o.plot_charts_yearly()

    #def report_is(self):
        #self.getMirr().o.prepare_report_IS()

    #def report_bs(self):
        #self.getMirr().o.prepare_report_BS()

    #def report_isbscf(self, yearly=False):
        #self.getMirr().o.prepare_report_IS_BS_CF_IRR(yearly)

    def report_isbscf(self):
        self.getMirr().o.prepare_report_IS_BS_CF_IRR(excel=True, yearly=False)
        self.getMirr().o.prepare_report_IS_BS_CF_IRR(excel=True, yearly=True)

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

    #def read_db(self):
        #"""Test reading results from Mongo"""
        #test_database_read()

    #def run_1_sumulation(self):
        #"""Test writing results to Mongo"""
        #run_one_iteration()

    def run_simulations(self):
        default_simulations_number = MainConfig().getSimulationNumber()
        simulations_number = get_input_int(text="Please select number of simulations (or press enter to default %s) :: " %default_simulations_number, default=default_simulations_number)
        run_all_iterations(simulations_number)

    def report_irr(self):
        """Shows last N irrs distribution from database"""
        default_simulations_number = MainConfig().getSimulationNumber()
        simulations_number = get_input_int(text="Please select number of previous irrs for plotting distribution (default %s) :: " %default_simulations_number, default=default_simulations_number)
        get_and_show_irr_distribution(number=simulations_number, field='irr_owners', yearly=False)

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

