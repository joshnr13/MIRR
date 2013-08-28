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
from simulations import  runAndSaveSimulation
from _mirr import Mirr
from charts import plotRevenueCostsChart, plotCorrelationTornadoChart, plotIRRScatterChart, plotStepChart
from report_output import ReportOutput
from config_readers import MainConfig
from constants import CORRELLATION_IRR_FIELD, CORRELLATION_NPV_FIELD,  REPORT_DEFAULT_NUMBER_ITERATIONS
from rm import  analyseSimulationResults, plotSaveStochasticValuesSimulation

commands = OrderedDict()  #Commands sequence for menu, all commands is method of Interfave class
commands['1'] = 'runSimulation'
commands['2'] = 'analyseSimulationResults'
commands['3'] = 'report_isbscf'
commands['4'] = 'charts'
commands['5'] = 'printEquipment'
commands['6'] = 'outputPrimaryEnergy'
commands['7'] = 'outputElectricityProduction'
commands['8'] = 'irrCorrelations'
commands['9'] = 'irrScatterCharts'
commands['10'] = 'npvCorrelations'
commands['11'] = 'distributionOfInputVariables'
commands['12'] = 'simulationsLog'
commands['13'] = 'deleteSimulation'
commands['14'] = 'generateWeatherData'  #daily insolation and Temperature
commands['15'] = 'generateElectricityMarketPrice'  #daily electricty market prices
commands['0'] = 'stop'

class Interface():
    """Class for Main menu for all operations"""
    def __init__(self):
        self.db = Database()
        self.main_config = MainConfig()

    def runSimulation(self, iterations_no=None, comment=None):
        """Running simulation and saving results"""
        if iterations_no is None:
            iterations_no = self.getNumberIterations(default=REPORT_DEFAULT_NUMBER_ITERATIONS)
        if comment is  None:
            comment = getInputComment()

        simulation_no = runAndSaveSimulation(iterations_no, comment)

    def analyseSimulationResults(self, simulation_no=None):
        """
        1 Plots yearly irrs distributions for user definded simulation no
        2 Saves report to xls file
        3 Print stats to output
        """
        if simulation_no is  None:
            simulation_no =  self.getInputSimulation("plotting IRR distribution ")
        analyseSimulationResults(simulation_no, yearly=True)

    def charts(self):
        """Plots Revenue, Cost charts monthly and yearly for user definded simulation no"""
        simulation_no, iteration_no =  self.getSimulationIterationNums("for plotting revenue-costs charts ")
        plotRevenueCostsChart(simulation_no, iteration_no, yearly=False)
        plotRevenueCostsChart(simulation_no, iteration_no, yearly=True)

    def printEquipment(self):
        """Prints equipment of user defined simulation no , used first iteration"""
        simulation_no =  self.getInputSimulation("printing equipment ")
        print self.db.getIterationField(simulation_no, iteration_no=1, field='equipment_description')

    def outputPrimaryEnergy(self):
        """Plots solar insolations step chart for user definded simulation no, iteration no and data range"""
        simulation_no, iteration_no =  self.getSimulationIterationNums("for printing chart with Primary Energy ")
        start_date, end_date, resolution = self.getStartEndResolution()
        plotStepChart(simulation_no, iteration_no, start_date, end_date, resolution, field= 'insolations_daily')

    def outputElectricityProduction(self):
        """Plots electricity production step chart for user definded simulation no, iteration no and data range"""
        simulation_no, iteration_no =  self.getSimulationIterationNums("for printing chart with Electricity Production ")
        start_date, end_date, resolution = self.getStartEndResolution()
        plotStepChart(simulation_no, iteration_no, start_date, end_date, resolution, field= 'electricity_production_daily')

    def irrCorrelations(self):
        """plots correlations chart with IRR values"""
        self._run_correlations(CORRELLATION_IRR_FIELD)

    def irrScatterCharts(self, simulation_no=None):
        """Plots irr scatter chart for irr_project and irr_owners yearly values"""
        if simulation_no is None:
            simulation_no = self.getInputSimulation("IRR scatter_chart: ")
        plotIRRScatterChart(simulation_no, 'irr_project', yearly=True)
        plotIRRScatterChart(simulation_no, 'irr_owners', yearly=True)

    def npvCorrelations(self):
        """plots npv correlatins npv_project_y """
        self._run_correlations(CORRELLATION_NPV_FIELD)

    def distributionOfInputVariables(self, simulation_no=None):
        """Plots and saves stochastic diagrams"""
        if simulation_no is None:
            simulation_no = self.getInputSimulation("stochastic distribution charts: ")
        plotSaveStochasticValuesSimulation(simulation_no)

    def simulationsLog(self, last=None):
        """Show last simulation logs - short information about number of iterations,date and comments"""
        default = 10
        if last is  None:
            last = getInputInt("Please input number of number of last simulations to display (or press Enter to use default %s) : " %default, default)
        self.db.printLastSimulationsLog(last)

    def deleteSimulation(self, simulation_no=None):
        """Deletes user entered simulation number"""
        if simulation_no is  None:
            simulation_no = self.getInputSimulation("DELETING: ")
        self.db.deleteSimulation(simulation_no)

    def generateWeatherData(self):
        """Generates multi simulations of Weather data for each day in project and saves it to database"""
        simulations_no = 100
        period = self.main_config.getAllDates()
        simulations = WeatherSimulation(period, simulations_no)
        simulations.simulate()

    def generateElectricityMarketPrice(self):
        """Generates multi simulations of Electricity Price for each day in project and saves it to database"""
        simulations_no = 100
        period = self.main_config.getAllDates()
        simulations = ElectricityMarketPriceSimulation(period, simulations_no)
        simulations.simulate()

    def _run_correlations(self, field):
        """field - dict [short_name] = database name"""
        simulation_no = self.getInputSimulation("%s correlations charts: " %field.keys()[0])
        plotCorrelationTornadoChart(field, simulation_no)

    @memoize
    def getMirr(self):
        """return class instances that combines all modules together"""
        return Mirr()

    def getNumberIterations(self, text="", default=""):
        """User input for number of iterations"""
        return  getInputInt("Please select number of iterations to run (or press Enter to use default %s) : " %default, default)

    def getInputSimulation(self, text=""):
        """User input for choosing simulation no"""
        last_simulation = self.db.getLastSimulationNo()
        return  getInputInt("Please input ID of simulation for %s (or press Enter to use last-run %s): " %(text, last_simulation), last_simulation)

    def getInputIteration(self, text, simulation_no):
        """User input for choosing iteration no"""
        iterations = "[1-%s]" % (self.db.getIterationsNumber(simulation_no)+1)
        return  getInputInt("Please enter iteration of Simulation %s for %s from %s (or press Enter to use first): " %(simulation_no, text, iterations), 1)

    def getSimulationIterationNums(self, text):
        """User input for choosing simulation no and iteration no"""
        simulation_no =  self.getInputSimulation(text)
        iteration_no =  self.getInputIteration(text, simulation_no )
        return (simulation_no, iteration_no)

    def getStartEndResolution(self):
        """return  StartEndResolution based on default values and user input, that can modify defaults"""
        def_start = self.getMirr().main_config.getStartDate()  #get defaults
        def_end = self.getMirr().main_config.getEndDate() #get defaults
        def_res = self.getMirr().main_config.getResolution() #get defaults

        memo = " (from %s to %s)" % (def_start,def_end)
        memo_res = "Please select resolution of graph in days (or press Enter to use default %s) : " % def_res

        start_date =  getInputDate(text="Start date" + memo, default=def_start)  #get user input of use default
        end_date =  getInputDate(text="End date" + memo, default=def_end)
        resolution = getInputInt(memo_res, default=def_res)
        return (start_date, end_date, resolution)

    def stop(self):
        """Exits from menu"""
        raise KeyboardInterrupt("Exit command selected")

    def noMethod(self):
        """Shows in case of error while choosing menu item"""
        print "No such function. Try again from allowed %s" % commands.values()

    def help(self):
        """Show allowed commands"""
        print "Alowed commands (Short name = full name) "
        for k, v in (commands.items()):
            print "%s = %s" % (k, v)

def printEntered(line):
    """print user choosed line"""
    if line in commands:
        print "Entered %s - %s" % (line, commands[line])
    else:
        print "Entered %s " % (line, )

def runMethod(obj, line):
    if line in commands:
        method = getattr(obj, commands[line])
    else:
        method = getattr(obj, line, obj.noMethod)
    method()

if __name__ == '__main__':
    """This runs when this module executed"""
    try:
        i = Interface()
        i.help()
        while True:
            line = raw_input('Prompt command (For exit: 0 or stop; For help: help): ').strip()
            printEntered(line)
            runMethod(i, line)
    except KeyboardInterrupt:
        print sys.exc_info()[1]
    except:
        print traceback.format_exc()

