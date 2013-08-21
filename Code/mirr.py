#!/usr/bin/env python
# -*- coding utf-8 -*-
# Project MIRR - Modelling Investment Risk in Renewables  - Research related to risk quantification at investments in renewable energy sources
# Project owner Borut Del Fabbro

import sys
import traceback

from collections import  OrderedDict
from annex import getInputDate, getInputInt, memoize, getInputComment
from database import Database
from ecm import ElectricityMarketPriceSimulation
from em import WeatherSimulation
from simulations import  run_save_simulation
from _mirr import Mirr
from charts import plotRevenueCostsChart, plotCorrelationTornadoChart, plotIRRScatterChart, plotStepChart
from report_output import ReportOutput
from config_readers import MainConfig
from constants import CORRELLATION_IRR_FIELD, CORRELLATION_NPV_FIELD,  REPORT_DEFAULT_NUMBER_SIMULATIONS, REPORT_DEFAULT_NUMBER_ITERATIONS
from rm import  analyseSimulationResults, plotSaveStochasticValuesSimulation

commands = OrderedDict()
commands['1'] = 'runSimulation'
commands['2'] = 'analyseSimulationResults'
commands['3'] = 'report_isbscf'
commands['4'] = 'charts'
commands['5'] = 'print_equipment'
commands['6'] = 'outputPrimaryEnergy'
commands['7'] = 'outputElectricityProduction'
commands['8'] = 'irr_correlations'
commands['9'] = 'irr_scatter_charts'
commands['10'] = 'npv_correlations'
commands['11'] = 'distributionOfInputVariables'
commands['12'] = 'simulationsLog'
commands['13'] = 'deleteSimulation'
commands['14'] = 'generateWeatherData'  #daily insolation and Temperature
commands['15'] = 'generateElectricityMarketPrice'  #daily electricty market prices
commands['0'] = 'stop'

class Interface():
    def __init__(self):
        self.db = Database()
        self.main_config = MainConfig()

    def runSimulation(self, iterations_no=None, comment=None):
        """Running simulation and saving results"""
        if iterations_no is None:
            iterations_no = self.get_number_iterations(default=REPORT_DEFAULT_NUMBER_ITERATIONS)
        if comment is  None:
            comment = getInputComment()

        simulation_no = run_save_simulation(iterations_no, comment)

    def analyseSimulationResults(self, simulation_no=None):
        """Shows last N irrs distribution from database"""
        if simulation_no is  None:
            simulation_no =  self.get_input_simulation("plotting IRR distribution ")

        analyseSimulationResults(simulation_no, yearly=True)

    def charts(self):
        simulation_no, iteration_no =  self.get_simulation_iteration_nums("for plotting revenue-costs charts ")
        plotRevenueCostsChart(simulation_no, iteration_no, yearly=False)
        plotRevenueCostsChart(simulation_no, iteration_no, yearly=True)

    def print_equipment(self):
        simulation_no =  self.get_input_simulation("printing equipment ")
        print self.db.get_iteration_field(simulation_no, iteration_no=1, field='equipment_description')

    def outputPrimaryEnergy(self):
        simulation_no, iteration_no =  self.get_simulation_iteration_nums("for printing chart with Primary Energy ")
        start_date, end_date, resolution = self.get_inputs()
        plotStepChart(simulation_no, iteration_no, start_date, end_date, resolution, field= 'insolations_daily')

    def outputElectricityProduction(self):
        simulation_no, iteration_no =  self.get_simulation_iteration_nums("for printing chart with Electricity Production ")
        start_date, end_date, resolution = self.get_inputs()
        plotStepChart(simulation_no, iteration_no, start_date, end_date, resolution, field= 'electricity_production_daily')

    def irr_correlations(self):
        self._run_correlations(CORRELLATION_IRR_FIELD)

    def irr_scatter_charts(self, simulation_no=None):
        if simulation_no is None:
            simulation_no = self.get_input_simulation("IRR scatter_chart: ")
        plotIRRScatterChart(simulation_no, 'irr_project', yearly=True)
        plotIRRScatterChart(simulation_no, 'irr_owners', yearly=True)

    def npv_correlations(self):
        self._run_correlations(CORRELLATION_NPV_FIELD)

    def distributionOfInputVariables(self, simulation_no=None):
        if simulation_no is None:
            simulation_no = self.get_input_simulation("stochastic distribution charts: ")
        plotSaveStochasticValuesSimulation(simulation_no)

    def simulationsLog(self, last=None):
        default = 10
        if last is  None:
            last = getInputInt("Please input number of number of last simulations to display (or press Enter to use default %s) : " %default, default)
        self.db.get_last_simulations_log(last)

    def deleteSimulation(self, simulation_no=None):
        if simulation_no is  None:
            simulation_no = self.get_input_simulation("DELETING: ")
        self.db.delete_simulation(simulation_no)

    def generateWeatherData(self):
        simulations_no = 100
        period = self.main_config.getAllDates()
        simulations = WeatherSimulation(period, simulations_no)
        simulations.simulate()

    def generateElectricityMarketPrice(self):
        simulations_no = 100
        period = self.main_config.getAllDates()
        simulations = ElectricityMarketPriceSimulation(period, simulations_no)
        simulations.simulate()

    def _run_correlations(self, field):
        """field - dict [short_name] = database name"""
        simulation_no = self.get_input_simulation("%s correlations charts: " %field.keys()[0])
        plotCorrelationTornadoChart(field, simulation_no)

    @memoize
    def getMirr(self):
        return Mirr()

    def get_number_iterations(self, text="", default=""):
        return  getInputInt("Please select number of iterations to run (or press Enter to use default %s) : " %default, default)

    def get_input_simulation(self, text=""):
        last_simulation = self.db.get_last_simulation_no()
        return  getInputInt("Please input ID of simulation for %s (or press Enter to use last-run %s): " %(text, last_simulation), last_simulation)

    def get_input_iteration(self, text, simulation_no):
        iterations = "[1-%s]" % (self.db.get_iterations_number(simulation_no)+1)
        return  getInputInt("Please enter iteration of Simulation %s for %s from %s (or press Enter to use first): " %(simulation_no, text, iterations), 1)

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

        start_date =  getInputDate(text="Start date" + memo, default=def_start)
        end_date =  getInputDate(text="End date" + memo, default=def_end)
        resolution = getInputInt(memo_res, default=def_res)

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
        print traceback.format_exc()

