#!/usr/bin/env python
# -*- coding utf-8 -*-

import pylab
import datetime
import ConfigParser
import os
from em import EnergyModule

class TechnologyModule():
    def __init__(self, energy_module):
        self.energy_module = energy_module
        self.loadConfig()
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

    def loadConfig(self, filename='tm_config.ini'):
        """Reads module config file"""
        config = ConfigParser.ConfigParser()
        filepath = os.path.join(os.getcwd(), 'configs', filename)
        config.read(filepath)
        self.electr_conv_factor = config.getfloat('Electricity', 'ConversionFactor')

    def generateElectiricityProduction(self, date):
        """based on insolation generates electricity production values for each day
        produced electricity = insolation * energyConversionFactor"""
        insolation = self.energy_module.generatePrimaryEnergyAvaialbility(date)
        return insolation * self.electr_conv_factor

    def getElectricityProduction(self, date_start, date_end):
        """return sum of electricity in kWh for each day for the selected period"""
        duration_days = (date_end - date_start).days
        return sum([self.generateElectiricityProduction(date_start+datetime.timedelta(days=i)) for i in range(duration_days) ])

    def get_xy_values_for_plot(self, start_date, end_date, resolution):
        """return x,y values for plotting step chart"""

        result = self.energy_module.getResolutionStartEnd(start_date, end_date, resolution)
        y = []

        for start_period, end_period in result:
            y.append(self.getElectricityProduction(start_period, end_period))

        x = []
        sm = 0
        for r in result:
            delta = (r[1] - r[0]).days
            x.append(sm+delta)
            sm += delta

        return x,y

    def outputElectricityProduction(self, start_date=None, end_date=None, resolution=None):
        """Makes a graph (x-axis displays time; y-axis= displays electricity produced).
        The minimum interval on the x-axis is set by resolution (integer number of days).
        Values on the y-axis are sum of the electricity produced in the time interval.
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
        print x, y



if __name__ == '__main__':
    start_date = datetime.date(2000, 1, 1)
    end_date = datetime.date(2001, 12, 31)
    em = EnergyModule()
    #print em.generatePrimaryEnergyAvaialbilityLifetime()
    tm = TechnologyModule(em)
    tm.outputElectricityProduction(start_date, end_date)
