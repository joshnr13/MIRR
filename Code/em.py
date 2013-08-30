#!/usr/bin/env python
# -*- coding utf-8 -*-

from base_class import BaseClassConfig
from config_readers import EnergyModuleConfigReader, EmInputsReader
from constants import TESTMODE
from collections import OrderedDict
from annex import cached_property
from database import  Database
from numpy.random import normal as gauss

class EnergyModule(BaseClassConfig, EnergyModuleConfigReader):
    """module for holding info about weather and insolations"""
    def __init__(self, config_module):
        BaseClassConfig.__init__(self, config_module)
        EnergyModuleConfigReader.__init__(self)
        self.inputs = EmInputsReader()  #read inputs from file
        self.db = Database()  #connection to db

    @cached_property
    def weather_data(self):
        """Takes weather data from database lazy, only when they are needed"""
        result = self.db.getWeatherData(self.weather_data_rnd_simulation)
        if not result:
            raise ValueError("Please generate first Weather data before using it")
        else:
            return result

    @cached_property
    def insolations(self):
        """Calculating insolations for whole project lazy, only when they are needed"""
        last_day_construction = self.last_day_construction
        return  OrderedDict((date, self.weather_data[date][0] if date > last_day_construction else 0) for date in self.all_project_dates)

    def getInsolation(self,  date):
        """return  insolationg at given date"""
        return  self.insolations[date]

    def getInsolationsLifetime(self):
        """return  all dict with insolations dates and values"""
        return  self.insolations

class WeatherSimulation(EnergyModuleConfigReader):
    """module for simulation of weather"""
    def __init__(self, period, simulations_no):
        """
        @period - list dates for simulation
        @simulations_no - number of simulation (to save it to db)
        """
        EnergyModuleConfigReader.__init__(self)
        self.inputs = EmInputsReader()  #read inputs from file
        self.db = Database()  #connection to db
        self.period = period
        self.simulations_no = simulations_no

    def cleanPreviousData(self):
        """cleaning previous simulation data in database"""
        print "Cleaning previous data"
        self.db.cleanPreviousWeatherData()

    def simulate(self):
        """main method to run simulation"""
        self.cleanPreviousData()  #clean prev values
        for simulation_no in range(1, self.simulations_no+1):
            data = self.generateOneSimulation(simulation_no)  #generate simulation one by one
            self.writeWeatherDataDb(data)  #write them into db

    def generateOneSimulation(self, simulation_no):
        """generate simulation one by one
        return  dict with [date]=(insolation, temperature)
        """
        days_dict = OrderedDict()
        for date in self.period:
            insolation, temperature = self.generateWeatherData(date)
            days_dict[date.strftime("%Y-%m-%d")] = (insolation, temperature)
        simulation_result = {"simulation_no": simulation_no, "data": days_dict}
        return  simulation_result

    def writeWeatherDataDb(self, data):
        """Saving into db dict"""
        self.db.writeWeatherData(data)
        print 'Writing weather data simulation %s' % data["simulation_no"]

    def generateWeatherData(self, date):
        """
        generates insolation and temperature for given_data
        - each time new random factor used

        ALGO:
          Tries up to 100 times to generate temperature in bounds [TMin, TMax]
          if T not in bounds tries next time,
          else uses generated value

        return  2 values:  insolation, temperature
        """
        av_temperature = self.getAvMonthTemperature(date)
        av_insolation = self.getAvMonthInsolation(date)

        for _ in range(100):
            rnd_factor = self.getRandomFactor()
            temperature = av_temperature * rnd_factor
            insolation =  av_insolation * rnd_factor
            if temperature >= self.TMin and temperature <= self.TMax:
                break

        return  insolation, temperature

    def getRandomFactor(self):
        """return random factor with normal distribution"""
        if not TESTMODE:
            return gauss(self.mean, self.stdev)
        else:
            return self.mean

    def getAvMonthInsolation(self, date):
        """Returns average daily insolation in given date"""
        return  self.inputs.getAvMonthInsolationMonth(date.month - 1)

    def getAvMonthTemperature(self, date):
        """Returns average daily temperature in given date"""
        return  self.inputs.getAvMonthTemperatureMonth(date.month - 1)

