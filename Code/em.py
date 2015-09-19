#!/usr/bin/env python
# -*- coding utf-8 -*-
"""Energy module - Everything related to energy input is managed here. Calculation of solar irradiation happens here. The resuklts are fed into technology module taht converts this data into produced electricty."""

from base_class import BaseClassConfig
from config_readers import EnergyModuleConfigReader
from constants import TESTMODE
from collections import OrderedDict
from annex import cached_property, setupPrintProgress, yearsBetween1Jan, convertDictDates
from database import  Database
from numpy.random import normal as gauss

class EnergyModule(BaseClassConfig, EnergyModuleConfigReader):
    """module for holding info about weather and insolations"""
    def __init__(self, config_module, country):
        BaseClassConfig.__init__(self, config_module)  #load main configs
        EnergyModuleConfigReader.__init__(self, country)  #load module configs
        self.db = Database()  #connection to
        self.country = country

    @cached_property
    def weather_data(self):
        """Takes weather data from database lazy, only when they are needed"""
        simulations_no = 1
        period = self.all_project_dates
        weather_simulation = WeatherSimulation(self.country, period, simulations_no)
        data = weather_simulation.generateOneSimulation(1)['data']  # generated weather data
        result = convertDictDates(data)
        return result

    @cached_property
    def insolations(self):
        """Calculating insolations for whole project lazy, only when they are needed"""
        last_day_construction = self.last_day_construction
        return OrderedDict((date, self.weather_data[date][0] if date > last_day_construction else 0) for date in self.all_project_dates)

    def getInsolation(self, date):
        """return  insolationg at given date"""
        return self.insolations[date]

    def getInsolationsLifetime(self):
        """return  all dict with insolations dates and values"""
        return self.insolations

    @cached_property
    def avg_production_day_per_kW(self):
        """Calculating average daily pruduction per kW for whole project."""
        return OrderedDict((date, self.weather_data[date][2]) for date in self.all_project_dates)

    def getAvgProductionDayPerKW(self, date):
        """return  average daily pruduction per kW at given date"""
        return self.avg_production_day_per_kW[date]

    def getAvgProductionDayPerKWLifetime(self):
        """return all dict with average daily pruduction per kW dates and values"""
        return self.avg_production_day_per_kW



class WeatherSimulation(EnergyModuleConfigReader):
    """module for simulation of weather"""
    def __init__(self, country, period, simulations_no):
        """
        @period - list dates for simulation
        @simulations_no - number of simulation (to save it to db)
        """
        EnergyModuleConfigReader.__init__(self, country)  #module configs
        self.db = Database()  #  connection to db
        self.period = period
        self.simulations_no = simulations_no
        self.country = country
        self.years = {d.year for d in self.period}

    def cleanPreviousData(self):
        """cleaning previous simulation data in database"""
        print "Cleaning previous data for %r" % self.country
        self.db.cleanPreviousWeatherData(self.country)

    def simulate(self):
        """main method to run simulation"""
        self.cleanPreviousData()  #clean prev values
        print_progress = setupPrintProgress('%d')
        for simulation_no in range(1, self.simulations_no+1):
            data = self.generateOneSimulation(simulation_no)  #generate simulation one by one
            self.writeWeatherDataDb(data)  #write them into db
            print_progress(simulation_no)  # print progress bar with simulation_no
        print_progress(stop=True)

    def generateOneSimulation(self, simulation_no):
        """generate simulation one by one
        return  dict with [date]=(insolation, temperature)
        """
        self.randomizeAvgProductionCorrections(self.country)
        days_dict = OrderedDict()
        self.interannual_variability = self.generateInterannualVariability()
        self.dust_uncertainty = self.generateDustUncertanty()
        self.snow_uncertainty = self.generateSnowUncertanty()
        for date in self.period:
            insolation, temperature, avg_production_day_per_kW = self.generateWeatherData(date)
            days_dict[date.strftime("%Y-%m-%d")] = (insolation, temperature, avg_production_day_per_kW)
        simulation_result = {"simulation_no": simulation_no, "data": days_dict}
        return simulation_result

    def writeWeatherDataDb(self, data, silent=True):
        """Saving into db dict"""
        data['country'] = self.country
        self.db.writeWeatherData(data)
        if not silent:
            print 'Writing weather data simulationif %s' % data["simulation_no"]

    def generateWeatherData(self, date):
        """
        return 3 values:  insolation, temperature, avg_production_day_per_kW
        """
        temperature = self.getAvMonthTemperature(date)
        insolation = self.getAvMonthInsolation(date)

        return insolation, temperature, self.generateAvgProductionDayPerKw(date)

    def generateAvgProductionDayPerKw(self, date):
        "Generates average daily production for a given month by applying some relative errors."
        avg_production_per_kw = self.getAvProductionDayPerKw(date.month)
        avg_production_per_kw *= (1 + self.data_uncertainty)
        avg_production_per_kw *= (1 + self.transposition_model_uncertainty)
        avg_production_per_kw *= (1 + self.long_term_irradiation_uncertainty)
        avg_production_per_kw *= (1 + self.interannual_variability[date.year]) # changes on yearly basis
        avg_production_per_kw *= (1 + self.dust_uncertainty[date.year])
        avg_production_per_kw *= (1 + self.snow_uncertainty[date.year])
        return avg_production_per_kw

    def generateInterannualVariability(self):
        """Generates interannual variabilities in advance for all years of period."""
        return {y: gauss(0, self.interannual_variability_std) for y in self.years}

    def generateDustUncertanty(self):
        """Generates dust uncertainty for all years of period."""
        return {d: gauss(0, self.dust_uncertainty_std) for d in self.years}

    def generateSnowUncertanty(self):
        """Generates snow uncertainty for all years of period."""
        return {d: gauss(0, self.snow_uncertainty_std) for d in self.years}

    def getRandomFactor(self):
        """return random factor with normal distribution"""
        if not TESTMODE:
            return gauss(self.mean, self.stdev)
        else:
            return self.mean

    def getAvMonthInsolation(self, date):
        """Returns average daily insolation in given date"""
        return self.getAvMonthInsolationMonth(date.month)

    def getAvMonthTemperature(self, date):
        """Returns average daily temperature in given date"""
        return self.getAvMonthTemperatureMonth(date.month)