#!/usr/bin/env python
# -*- coding utf-8 -*-
# Project MIRR - Modelling Investment Risk in Renewables  - Research related to risk quantification of investments in renewable energy sources
# Project owner Borut Del Fabbro

import sys
import traceback
from collections import OrderedDict
from random import randint

from annex import getInputDate, getInputInt, memoize, getInputComment
from database import Database
from ecm import ElectricityMarketPriceSimulation
from em import WeatherSimulation
from simulations import runAndSaveSimulation
from _mirr import Mirr
from charts import plotRevenueCostsChart, plotCorrelationTornadoChart, plotIRRScatterChart, plotStepChart
from report_output import ReportOutput
from constants import CORRELLATION_IRR_FIELD, CORRELLATION_NPV_FIELD, REPORT_DEFAULT_NUMBER_ITERATIONS
from rm import analyseSimulationResults, plotSaveStochasticValuesSimulation, plotGeneratedWeather, plotGeneratedElectricity


commands = OrderedDict()  #Commands sequence for menu, all commands is method of Interfave class
commands['1'] = 'runSimulation'
commands['2'] = 'analyseSimulationResults'
commands['3'] = 'mainReport'
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
commands['16'] = 'outputGeneratedElectricityPrices'  #Graph of daily electricty market prices
commands['17'] = 'outputGeneratedWeatherData'  #Graph of daily electricty market prices
commands['0'] = 'stop'
commands['h'] = 'help'
commands['help'] = 'help'


class Interface():
    """Class for Main menu for all operations"""

    def __init__(self):
        self.db = Database()
        # self.main_config = MainConfig()  #link to main config

    def runSimulation(self, country=None, iterations_no=None, comment=None):
        """Running simulation and saving results"""
        country = self.getInputCountry(country)

        if iterations_no is None:
            iterations_no = self.getNumberIterations(default=REPORT_DEFAULT_NUMBER_ITERATIONS)  #ask user how many iterations
        if comment is None:
            comment = getInputComment()  #get user comment

        simulation_no = runAndSaveSimulation(country, iterations_no, comment)  #runing

    def analyseSimulationResults(self, simulation_no=None):
        """
        1 Plots yearly irrs distributions for user definded simulation no
        2 Saves report to xls file
        3 Print stats to output
        """
        if simulation_no is None:
            simulation_no = self.getInputSimulation("plotting IRR distribution ")
        analyseSimulationResults(simulation_no, yearly=True)

    def mainReport(self):
        """Save main report for user defind simulation and iteration number"""
        params = self.getSimulationIterationNums("for getting ISBS excel report ")
        ReportOutput(None).prepareReportISBSCFIRR(params, yearly=False)  #preparing monthly report
        ReportOutput(None).prepareReportISBSCFIRR(params, yearly=True)  #preparing yearly report

    def charts(self):
        """Plots Revenue, Cost charts monthly and yearly for user definded simulation no"""
        simulation_no, iteration_no = self.getSimulationIterationNums("for plotting revenue-costs charts ")
        country = self.db.getSimulationCountry(simulation_no, print_result=True)
        plotRevenueCostsChart(simulation_no, iteration_no, yearly=False, country=country)  #plot monthly chart
        plotRevenueCostsChart(simulation_no, iteration_no, yearly=True, country=country)  #plot yearly chart

    def printEquipment(self):
        """Prints equipment of user defined simulation no , used first iteration"""
        simulation_no = self.getInputSimulation("printing equipment ")
        country = self.db.getSimulationCountry(simulation_no,
                                               print_result=True)

        print self.db.getIterationField(simulation_no, iteration_no=1, field='equipment_description')

    def outputPrimaryEnergy(self):
        """Plots solar insolations step chart for user definded simulation no, iteration no and data range"""
        simulation_no, iteration_no = self.getSimulationIterationNums("for printing chart with Primary Energy ")
        country = self.db.getSimulationCountry(simulation_no=simulation_no, print_result=True)
        start_date, end_date, resolution = self.getStartEndResolution(simulation_no, iteration_no)  #ask user start date, end, resolution
        plotStepChart(simulation_no, iteration_no, start_date, end_date, resolution, field='insolations_daily', country=country)

    def outputElectricityProduction(self):
        """Plots electricity production step chart for user definded simulation no, iteration no and data range"""
        simulation_no, iteration_no = self.getSimulationIterationNums("for printing chart with Electricity Production ")
        country = self.db.getSimulationCountry(simulation_no=simulation_no, print_result=True)
        start_date, end_date, resolution = self.getStartEndResolution(simulation_no, iteration_no)  #ask user start date, end, resolution
        plotStepChart(simulation_no, iteration_no, start_date, end_date, resolution, field='electricity_production_daily', country=country)

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
        if last is None:
            last = getInputInt("Please input number of number of last simulations to display (or press Enter to use default %s) : " % default,
                               default)
        self.db.printLastSimulationsLog(last)

    def deleteSimulation(self, simulation_no=None):
        """Deletes user entered simulation number"""
        if simulation_no is None:
            simulation_no = self.getInputSimulation("DELETING: ")
        self.db.deleteSimulation(simulation_no)

    def generateWeatherData(self, country=None):
        """Generates multi simulations of Weather data for each day in project and saves it to database"""
        country = self.getInputCountry(country)

        simulations_no = 100
        period = self.getMirr(country).main_config.getAllDates()
        simulations = WeatherSimulation(country, period, simulations_no)
        simulations.simulate()

    def generateElectricityMarketPrice(self, country=None):
        """Generates multi simulations of Electricity Price for each day in project and saves it to database"""
        country = self.getInputCountry(country)

        simulations_no = 100
        period = self.getMirr(country).main_config.getAllDates()
        simulations = ElectricityMarketPriceSimulation(country, period, simulations_no)
        simulations.simulate()

    def outputGeneratedElectricityPrices(self, simulation_no=None, country=None):
        """Plots graph of generated Electricity Prices from user defined simulation_no"""
        country = self.getInputCountry(country)

        what = "Electricity prices"
        simulation_no = simulation_no or self.getInputElectricitySimulationNoOrAll(what) or range(1, 101)
        if not isinstance(simulation_no, int):
            print "Plotting all %s can take some time (about 30-60 seconds) ..." % what
        plotGeneratedElectricity(what, simulation_no, country)

    def outputGeneratedWeatherData(self, simulation_no=None, country=None):
        """Plots graph of generated Electricity Prices from user defined simulation_no"""
        country = self.getInputCountry(country)

        what = "Weather data"
        if simulation_no is None:
            simulation_no = self.getInputWeatherElectricitySimulationNo(what)
        plotGeneratedWeather(what, simulation_no, country)

    ####################################################################################################################

    def _run_correlations(self, field):
        """field - dict [short_name] = database name"""
        simulation_no = self.getInputSimulation("%s correlations charts: " % field.keys()[0])
        country = self.db.getSimulationCountry(simulation_no=simulation_no,
                                               print_result=True)

        plotCorrelationTornadoChart(field, simulation_no, country=country)

    @memoize
    def getMirr(self, country):
        """return class instances that combines all modules together"""
        return Mirr(country)

    def getNumberIterations(self, text="", default=""):
        """User input for number of iterations"""
        return getInputInt("Please select number of iterations to run (or press Enter to use default %s) : " % default, default)

    def getInputSimulation(self, text=""):
        """User input for choosing simulation no"""
        last_simulation = self.db.getLastSimulationNo()
        return getInputInt("Please input ID of simulation for %s (or press Enter to use last-run %s): " % (text, last_simulation), last_simulation)

    def getInputIteration(self, text, simulation_no):
        """User input for choosing iteration no"""
        iterations = "[1-%s]" % (self.db.getIterationsNumber(simulation_no) + 1)
        return getInputInt(
            "Please enter iteration of Simulation %s for %s from %s (or press Enter to use first): " % (simulation_no, text, iterations), 1)

    def getSimulationIterationNums(self, text):
        """User input for choosing simulation no and iteration no"""
        simulation_no = self.getInputSimulation(text)
        iteration_no = self.getInputIteration(text, simulation_no)
        return (simulation_no, iteration_no)

    def getInputWeatherElectricitySimulationNo(self, what='????'):
        """User Input for weather or electricity simulation no"""
        random_no = randint(1, 100)
        result = getInputInt("Please input which %s simulation Number to plot (or press Enter to plot random - %s): " % (what, random_no), random_no)
        return result

    def getInputElectricitySimulationNoOrAll(self, what='????'):
        """User Input for electricity simulation or return None"""
        return getInputInt("Please input which %s simulation Number to plot (or press Enter to plot ALL ): " % what, default=None)

    def getInputCountry(self, country=None):

        countries = OrderedDict()
        countries[1] = 'SLOVENIA'
        countries[2] = 'AUSTRIA'
        countries[3] = 'ITALY'
        countries[4] = 'GERMANY'
        countries[5] = 'SPAIN'

        if country in countries:
            return country

        for key, value in countries.items():
            print key, ' --> ', value

        user_input = getInputInt("Please input country number to use (or press Enter to use DEFAULT): ", default=None)
        user_choice = countries.get(user_input)
        if user_choice is None:
            print "User choice: 'DEFAULT'"
        else:
            print "User choice: %r" % user_choice
        return user_choice

    def getStartEndResolution(self, simulation_no, iteration_no):
        """return  StartEndResolution based on default values and user input, that can modify defaults"""

        config_values = self.db.getIterationValuesFromDb(simulation_no=simulation_no,
                                         fields=['main_configs'],
                                         yearly=False,
                                         iteration_no=iteration_no,
                                         one_result=True,
                                         )['main_configs']


        def_start = config_values['start_date']  #get defaults
        def_end = config_values['end_date']  #get defaults
        def_res = int(config_values['resolution'])  #get defaults

        memo = " (from %s to %s)" % (def_start, def_end)
        memo_res = "Please select resolution of graph in days (or press Enter to use default %s) : " % def_res

        start_date = getInputDate(text="Start date" + memo, default=def_start)  #get user input of use default
        end_date = getInputDate(text="End date" + memo, default=def_end)
        resolution = getInputInt(memo_res, default=def_res)  # ask user resolution
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
            try:
                int(k)
            except ValueError:
                pass
            else:
                print "%s = %s" % (k, v)


def printEntered(line):
    """print user choosed line"""
    print "="*70
    if line in commands:
        print "Entered %s - %s" % (line, commands[line])
    else:
        print "Entered %s " % (line, )


def runMethod(obj, line):
    """run method of Interface class, name of method is taken from GLOBAL dict commands"""
    if line in commands:
        method = getattr(obj, commands[line])
    else:
        method = getattr(obj, line, obj.noMethod)
    try:
        method()
    except ValueError as e:
        print "-"*80
        print "Error: %r" %e
        print "-"*80


if __name__ == '__main__':
    """This runs when this module executed"""
    try:
        i = Interface()
        i.help()
        while True:
            print "="*70
            line = raw_input('Prompt command (For exit: 0 or stop; For help: help or h): ').strip()
            printEntered(line)
            runMethod(i, line)
    except KeyboardInterrupt:
        print sys.exc_info()[1]
    except:
        print traceback.format_exc()

