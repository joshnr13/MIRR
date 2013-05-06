#!/usr/bin/env python
# -*- coding utf-8 -*-

import random
import pylab
import datetime
import numpy
import ConfigParser
import os
from base_class import BaseClassConfig
from main_config_reader import MainConfig
from constants import TESTMODE

class EnergyModule(BaseClassConfig):

    def __init__(self, config_module):
        BaseClassConfig.__init__(self, config_module)
        self.loadConfig()
        self.loadInputs()

    def loadConfig(self, filename='em_config.ini'):
        """Reads module config file"""
        config = ConfigParser.ConfigParser()
        filepath = os.path.join(os.getcwd(), 'configs', filename)
        config.read(filepath)
        self.mean = config.getfloat('NormalDistribution', 'mean')
        self.stdev = config.getfloat('NormalDistribution', 'stdev')

    def getRandomFactor(self):
        """return random factor with normal distribution"""
        if TESTMODE:
            return  self.mean
        else:
            return random.gauss(self.mean, self.stdev)

    def loadInputs(self):
        """Loads inputs to memory"""
        filepath = os.path.join(os.getcwd(), 'inputs', 'em_input.txt')
        self.inputs = numpy.genfromtxt(filepath, dtype=None, delimiter=';',  names=True)

    def getAvMonthInsolation(self, date):
        """Returns average daily insolation in given date"""
        return self.inputs[date.month-1]['Hopt']

    def generatePrimaryEnergyAvaialbility(self, date):
        """Parameters: start date
        based on monthly averages creates daily data
        """
        result = self.getAvMonthInsolation(date) * self.getRandomFactor()
        return result

    def generatePrimaryEnergyAvaialbilityLifetime(self):
        """return energy availability per each day in whole lifetime"""
        lifetime_days = (self.end_date_project - self.start_date_project).days
        return [self.generatePrimaryEnergyAvaialbility(self.start_date_project+datetime.timedelta(days=i)) for i in range(lifetime_days) ]

    def getAccumulatedEnergy(self, start_date, end_date):
        """
        parameters: start date,end_date
        return accumulated energy from start date(incl) till end date (incl)
        """
        result = 0
        while start_date < end_date:
            result += self.generatePrimaryEnergyAvaialbility(start_date)
            start_date += datetime.timedelta(days=1)
        return result

    def getResolutionStartEnd(self, start_date, end_date, resolution):
        """Returns list [start , start_date + resolution] using resolution (days interval)"""
        result = []
        while start_date < end_date:
            next_step_date = start_date + datetime.timedelta(days=resolution)
            if next_step_date <= end_date:
                result.append((start_date, next_step_date))
                start_date = next_step_date
            elif next_step_date > end_date:
                result.append((start_date, end_date))
            start_date = next_step_date
        return result

    def get_xy_values_for_plot(self, start_date, end_date, resolution):
        """return x,y values for plotting step chart"""

        result = self.getResolutionStartEnd(start_date, end_date, resolution)
        result.insert(0, (start_date, start_date))
        y = []

        for start_period, end_period in result:
            y.append(self.getAccumulatedEnergy(start_period, end_period))

        x = []
        sm = 0
        for r in result:
            delta = (r[1] - r[0]).days
            x.append(sm+delta)
            sm += delta

        return x,y

    def outputPrimaryEnergy(self, start_date=None, end_date=None, resolution=None):
        """Parameters: start_date; end_date; resolution
           Makes a graph (x-axis displays time; y-axis= displays primary energy).
           The minimum interval on the x-axis is set by resolution (integer number of days).
           Values on the y-axis are sum of the energy in the time interval.
        """
        if start_date is  None:
            start_date = self.start_date_project
        if end_date is  None:
            end_date = self.end_date_project
        if resolution is  None:
            resolution = self.resolution

        x, y = self.get_xy_values_for_plot(start_date, end_date, resolution)
        pylab.step(x, y)
        pylab.show()


if __name__ == '__main__':
    mainconfig = MainConfig()
    em = EnergyModule(mainconfig)

    #print em.generatePrimaryEnergyAvaialbilityLifetime()
    start_date = datetime.date(2000, 1, 1)
    end_date = datetime.date(2001, 12, 31)
    em.outputPrimaryEnergy(start_date, end_date)
    #print (end_date - start_date).days

