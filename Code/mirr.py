#!/usr/bin/env python
# -*- coding utf-8 -*-

import sys
import traceback
import openpyxl
from collections import  OrderedDict
from annex import get_input_date, get_input_int, cached_property, memoize
from database import Database
from simulations import  run_all_simulations, save_irr_values, show_irr_charts, plot_correlation_tornado, plot_charts, irr_scatter_charts, show_save_irr_distribution
from config_readers import MainConfig
from _mirr import Mirr
from numpy import isnan
from numbers import Number
from constants import CORRELLATION_IRR_FIELD, CORRELLATION_NPV_FIELD, IRR, REPORT_DEFAULT_NUMBER_SIMULATIONS, REPORT_DEFAULT_NUMBER_ITERATIONS

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
commands['8'] = 'irr_correlations'
commands['9'] = 'irr_scatter_charts'
commands['10'] = 'npv_correlations'

#commands['99'] = 'read_db'

"""run_simulations  - then it asks you how many
report_irr - makes graphs about IRR distribution and saves data
report_isbscf  - makes xls - yearly and monthly for last set written to the database
charts - makes monthly and yearly charts for the last set written to the database
"""

class Interface():
    def __init__(self):
        self.db = Database()

    @memoize
    def getMirr(self):
        return Mirr()

    def charts(self):
        plot_charts(yearly=False)
        plot_charts(yearly=True)

    def report_isbscf(self):
        self.getMirr().o.prepare_report_IS_BS_CF_IRR(excel=True, yearly=False)
        self.getMirr().o.prepare_report_IS_BS_CF_IRR(excel=True, yearly=True)

    def print_equipment(self):
        self.getMirr().technology_module.print_equipment()

        eqipment_price = self.getMirr().technology_module.getInvestmentCost()
        print "\n Equipment investment cost - Total: %s" % eqipment_price

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

    def run_simulations(self):
        """Running simulation and saving results"""
        simulations_number = self.get_input(text="iterations to run", default=REPORT_DEFAULT_NUMBER_ITERATIONS)
        irr_values, simulation_no =  run_all_simulations(simulations_number)
        if irr_values:
            save_irr_values(irr_values[:], simulation_no)
            show_irr_charts(irr_values[:], IRR, simulation_no)

    def get_input(self, text="", default=""):
        return  get_input_int(text="Please select number of %s (or press Enter to use default %s) : " %(text, default), default=default)

    def report_irr(self, yearly=False):
        """Shows last N irrs distribution from database"""
        simulations_number =  self.get_input("previous simulations for plotting IRR distribution ", REPORT_DEFAULT_NUMBER_SIMULATIONS)
        show_save_irr_distribution(IRR, simulations_number, yearly)

    def irr_correlations(self):
        self._run_correlations(CORRELLATION_IRR_FIELD)

    def npv_correlations(self):
        self._run_correlations(CORRELLATION_NPV_FIELD)

    def _run_correlations(self, field):
        """field - dict [short_name] = database name"""
        number = self.get_input("previous simulations for %s correlations charts: " %field.keys()[0], REPORT_DEFAULT_NUMBER_SIMULATIONS)
        plot_correlation_tornado(field, number)

    def irr_scatter_charts(self):
        number = self.get_input("previous simulations for IRR scatter_chart: ", REPORT_DEFAULT_NUMBER_SIMULATIONS)
        irr_scatter_charts(number)

    def stop(self):
        raise KeyboardInterrupt("User selected command to exit")
    def no_such_method(self):
        print "No such function. Try again from allowed %s" % commands.values()
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

