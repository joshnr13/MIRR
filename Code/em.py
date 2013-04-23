#!/usr/bin/env python
# -*- coding utf-8 -*-

import random
import pylab
import datetime
import numpy
import ConfigParser
import csv
import os

class EnergyModule():

    def __init__(self):
        self.loadConfig()
        self.loadInputs()
        self.loadMainConfig()

    def loadMainConfig(self, filename='main_config.ini'):
        """Reads main config file """
        config = ConfigParser.SafeConfigParser({'lifetime': 30, 'start_date': '2000/1/1', 'resolution': 10})
        filepath = os.path.join(os.getcwd(), 'configs', filename)
        config.read(filepath)
        self.lifetime = config.getint('Main', 'lifetime')
        self.resolution = config.getint('Main', 'resolution')
        self.start_date = datetime.datetime.strptime(config.get('Main', 'start_date'), '%Y/%m/%d').date()
        self.end_date = datetime.date(self.start_date.year + self.lifetime, self.start_date.month, self.start_date.day)

    def loadConfig(self, filename='em_config.ini'):
        """Reads module config file"""
        config = ConfigParser.ConfigParser()
        filepath = os.path.join(os.getcwd(), 'configs', filename)
        config.read(filepath)
        self.mean = config.getfloat('NormalDistribution', 'mean')
        self.stdev = config.getfloat('NormalDistribution', 'stdev')

    def getRandomFactor(self):
        """return random factor with normal distribution"""
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
        """for each day of month:   .insulation = average monthly insolation for respective month * (random factor according to normal distribution)"""
        return self.getAvMonthInsolation(date)* self.getRandomFactor()

    def generatePrimaryEnergyAvaialbilityLifetime(self):
        """return energy availability per each day in whole lifetime"""
        lifetime_days = (self.end_date - self.start_date).days
        return [self.generatePrimaryEnergyAvaialbility(self.start_date+datetime.timedelta(days=i)) for i in range(lifetime_days) ]


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
            start_date = self.start_date
        if end_date is  None:
            end_date = self.end_date
        if resolution is  None:
            resolution = self.resolution

        x, y = self.get_xy_values_for_plot(start_date, end_date, resolution)
        pylab.step(x, y)
        pylab.show()


if __name__ == '__main__':
    start_date = datetime.date(2000, 1, 1)
    end_date = datetime.date(2001, 12, 31)
    em = EnergyModule()
    #print em.generatePrimaryEnergyAvaialbilityLifetime()
    em.outputPrimaryEnergy(start_date, end_date)
    #print (end_date - start_date).days

