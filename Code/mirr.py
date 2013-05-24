#!/usr/bin/env python
# -*- coding utf-8 -*-

import sys
import traceback
import openpyxl
from collections import  OrderedDict
from annex import get_input_date, get_input_int, cached_property, memoize, get_input_comment
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
commands['1'] = 'run_simulation'
commands['2'] = 'irr_distribution'
commands['3'] = 'report_isbscf'
commands['4'] = 'charts'
commands['5'] = 'print_equipment'
commands['6'] = 'outputPrimaryEnergy'
commands['7'] = 'outputElectricityProduction'
commands['8'] = 'irr_correlations'
commands['9'] = 'irr_scatter_charts'
commands['10'] = 'npv_correlations'
commands['11'] = 'simulations_log'

class Interface():
    def __init__(self):
        self.db = Database()

    @memoize
    def getMirr(self):
        return Mirr()

    def charts(self):
        simulation_number =  self.get_input_simulation("for plotting revenue-costs charts ")
        plot_charts(simulation_number, yearly=False)
        plot_charts(simulation_number, yearly=True)

    def report_isbscf(self):
        self.getMirr().o.prepare_report_IS_BS_CF_IRR(excel=True, yearly=False)
        self.getMirr().o.prepare_report_IS_BS_CF_IRR(excel=True, yearly=True)

    def print_equipment(self):

        eqipment_price = self.getMirr().technology_module.getInvestmentCost()
        print "\nEquipment investment cost - Total: %s" % eqipment_price
        self.getMirr().technology_module.print_equipment()

    def get_inputs(self):
        def_start = self.getMirr().main_config.getStartDate()
        def_end = self.getMirr().main_config.getEndDate()
        def_res = self.getMirr().main_config.getResolution()

        memo = " (from %s to %s)" % (def_start,def_end)
        memo_res = " Enter resolution or press ENTER to use default %s" % (def_res, )

        start_date =  get_input_date(text="Start date" + memo, default=def_start)
        end_date =  get_input_date(text="End date" + memo, default=def_end)
        resolution = get_input_int(memo_res, default=def_res)

        return (start_date, end_date, resolution)

    def outputPrimaryEnergy(self):
        start_date, end_date, resolution = self.get_inputs()
        self.getMirr().energy_module.outputPrimaryEnergy(start_date, end_date, resolution)

    def outputElectricityProduction(self):
        start_date, end_date, resolution = self.get_inputs()
        self.getMirr().technology_module.outputElectricityProduction(start_date, end_date, resolution)

    def run_simulation(self):
        """Running simulation and saving results"""
        iterations_number = self.get_number_iterations(default=REPORT_DEFAULT_NUMBER_ITERATIONS)
        irr_values, simulation_no =  run_all_simulations(iterations_number)
        if irr_values:
            save_irr_values(irr_values[:], simulation_no)
            show_irr_charts(irr_values[:], IRR, simulation_no)

        comment = get_input_comment()
        self.db.update_simulation_comment(simulation_no, comment)


    def get_number_iterations(self, text="", default=""):
        return  get_input_int("Please select number of iterations to run (or press Enter to use default %s) : " %default, default)

    def get_input_simulation(self, text=""):
        last_simulation = self.db.get_last_simulation_no()
        return  get_input_int("Please input ID of simulation for %s (or press Enter to use last-run %s): " %(text, last_simulation), last_simulation)

    def irr_distribution(self, yearly=False):
        """Shows last N irrs distribution from database"""
        simulations_number =  self.get_input_simulation("for plotting IRR distribution ")
        show_save_irr_distribution(IRR, simulations_number, yearly)

    def irr_correlations(self):
        self._run_correlations(CORRELLATION_IRR_FIELD)

    def npv_correlations(self):
        self._run_correlations(CORRELLATION_NPV_FIELD)

    def _run_correlations(self, field):
        """field - dict [short_name] = database name"""
        simulation_no = self.get_input_simulation("for %s correlations charts: " %field.keys()[0])
        plot_correlation_tornado(field, simulation_no)

    def irr_scatter_charts(self):
        simulation_no = self.get_input_simulation("for IRR scatter_chart: ")
        irr_scatter_charts(simulation_no)

    def simulations_log(self, last=10):
        self.db.get_last_simulations_log(last)

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

