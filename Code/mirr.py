#!/usr/bin/env python
# -*- coding utf-8 -*-

import sys
import traceback
import openpyxl
from collections import  OrderedDict
from annex import get_input_date, get_input_int, cached_property, memoize, get_input_comment
from database import Database

from simulations import  run_save_simulation, save_irr_values_xls, show_save_irr_distribution, print_equipment_db, plotsave_stochastic_values_by_simulation
from simulations import WeatherSimulations
from charts import plot_charts, show_irr_charts, plot_correlation_tornado, irr_scatter_charts, step_chart
from report_output import ReportOutput
from config_readers import MainConfig
from _mirr import Mirr
from numpy import isnan
from numbers import Number
from constants import CORRELLATION_IRR_FIELD, CORRELLATION_NPV_FIELD,  REPORT_DEFAULT_NUMBER_SIMULATIONS, REPORT_DEFAULT_NUMBER_ITERATIONS
from constants import IRR_REPORT_FIELD, IRR_REPORT_FIELD2

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
commands['11'] = 'stochastic_distributions'
commands['12'] = 'simulations_log'
commands['13'] = 'delete_simulation'
commands['14'] = 'generate_weather_data'  #daily insolation and Temperature

class Interface():
    def __init__(self):
        self.db = Database()
        self.main_config = MainConfig()

    def run_simulation(self, iterations_no=None, comment=None):
        """Running simulation and saving results"""
        if iterations_no is None:
            iterations_no = self.get_number_iterations(default=REPORT_DEFAULT_NUMBER_ITERATIONS)
        if comment is  None:
            comment = get_input_comment()

        simulation_no = run_save_simulation(iterations_no, comment)


    def irr_distribution(self, simulation_no=None):
        """Shows last N irrs distribution from database"""
        if simulation_no is  None:
            simulation_no =  self.get_input_simulation("plotting IRR distribution ")

        show_save_irr_distribution(simulation_no, yearly=True)

    def report_isbscf(self):
        params = self.get_simulation_iteration_nums("for getting ISBS excel report ")
        ReportOutput(0).prepare_report_IS_BS_CF_IRR(params, yearly=False)
        ReportOutput(0).prepare_report_IS_BS_CF_IRR(params, yearly=True)

    def charts(self):
        simulation_no, iteration_no =  self.get_simulation_iteration_nums("for plotting revenue-costs charts ")
        plot_charts(simulation_no, iteration_no, yearly=False)
        plot_charts(simulation_no, iteration_no, yearly=True)

    def print_equipment(self):
        simulation_no =  self.get_input_simulation("printing equipment ")
        print print_equipment_db(simulation_no)

    def outputPrimaryEnergy(self):
        simulation_no, iteration_no =  self.get_simulation_iteration_nums("for printing chart with Primary Energy ")
        start_date, end_date, resolution = self.get_inputs()
        step_chart(simulation_no, iteration_no, start_date, end_date, resolution, field= 'insolations_daily')

    def outputElectricityProduction(self):
        simulation_no, iteration_no =  self.get_simulation_iteration_nums("for printing chart with Electricity Production ")
        start_date, end_date, resolution = self.get_inputs()
        step_chart(simulation_no, iteration_no, start_date, end_date, resolution, field= 'electricity_production_daily')

    def irr_correlations(self):
        self._run_correlations(CORRELLATION_IRR_FIELD)

    def irr_scatter_charts(self, simulation_no=None):
        if simulation_no is None:
            simulation_no = self.get_input_simulation("IRR scatter_chart: ")
        irr_scatter_charts(simulation_no, 'irr_project', yearly=True)
        irr_scatter_charts(simulation_no, 'irr_owners', yearly=True)

    def npv_correlations(self):
        self._run_correlations(CORRELLATION_NPV_FIELD)

    def stochastic_distributions(self, simulation_no=None):
        if simulation_no is None:
            simulation_no = self.get_input_simulation("stochastic distribution charts: ")
        plotsave_stochastic_values_by_simulation(simulation_no)

    def simulations_log(self, last=None):
        default = 10
        if last is  None:
            last = get_input_int("Please input number of number of last simulations to display (or press Enter to use default %s) : " %default, default)
        self.db.get_last_simulations_log(last)

    def delete_simulation(self, simulation_no=None):
        if simulation_no is  None:
            simulation_no = self.get_input_simulation("DELETING: ")
        self.db.delete_simulation(simulation_no)

    def generate_weather_data(self):
        simulations_no = 100
        period = self.main_config.getAllDates()
        simulations = WeatherSimulations(period, simulations_no)
        simulations.simulate()

    def _run_correlations(self, field):
        """field - dict [short_name] = database name"""
        simulation_no = self.get_input_simulation("%s correlations charts: " %field.keys()[0])
        plot_correlation_tornado(field, simulation_no)
    @memoize
    def getMirr(self):
        return Mirr()
    def get_number_iterations(self, text="", default=""):
        return  get_input_int("Please select number of iterations to run (or press Enter to use default %s) : " %default, default)
    def get_input_simulation(self, text=""):
        last_simulation = self.db.get_last_simulation_no()
        return  get_input_int("Please input ID of simulation for %s (or press Enter to use last-run %s): " %(text, last_simulation), last_simulation)
    def get_input_iteration(self, text, simulation_no):
        iterations = "[1-%s]" % (self.db.get_iterations_number(simulation_no)+1)
        return  get_input_int("Please enter iteration of Simulation %s for %s from %s (or press Enter to use first): " %(simulation_no, text, iterations), 1)
    def get_simulation_iteration_nums(self, text):
        simulation_no =  self.get_input_simulation(text)
        iteration_no =  self.get_input_iteration(text, simulation_no )
        return (simulation_no, iteration_no)
    def get_inputs(self):
        def_start = self.getMirr().main_config.getStartDate()
        def_end = self.getMirr().main_config.getEndDate()
        def_res = self.getMirr().main_config.getResolution()

        memo = " (from %s to %s)" % (def_start,def_end)
        memo_res = "Please select resolution of graph in days (or press Enter to use default %s) : " % def_res

        start_date =  get_input_date(text="Start date" + memo, default=def_start)
        end_date =  get_input_date(text="End date" + memo, default=def_end)
        resolution = get_input_int(memo_res, default=def_res)

        return (start_date, end_date, resolution)
    def stop(self):
        raise KeyboardInterrupt("Exit command selected")
    def no_such_method(self):
        print "No such function. Try again from allowed %s" % commands.values()
    def help(self):
        print "Alowed commands (Short name = full name) "
        for k, v in (commands.items()):
            print "%s = %s" % (k, v)

def print_entered(line):
    if line in commands:
        print "Entered %s - %s" % (line, commands[line])
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

