#!/usr/bin/env python
# -*- coding utf-8 -*-

import math
import pylab
import datetime
import random
import ConfigParser

import os
from em import EnergyModule
from config_readers import MainConfig, TechnologyModuleConfigReader
from base_class import BaseClassConfig
from annex import get_configs, memoize, get_list_dates, years_between_1Jan
from tm_equipment import PlantEquipment
from collections import OrderedDict


class TechnologyModule(BaseClassConfig, TechnologyModuleConfigReader):
    def __init__(self, config_module, energy_module):
        BaseClassConfig.__init__(self, config_module)
        TechnologyModuleConfigReader.__init__(self)
        self.energy_module = energy_module
        self.assembleSystem()
        self.getInvestmentCost()
        self.calc_project_datelist()
        self.calc_degradation_coefficients()

    def assembleSystem(self):
        """generates objects for each solarmodule """
        self.total_power = self.groups_number * self.modules_in_group * self.module_power

        self.buildPlant()
        self.addSolarModulesAndInverter()
        self.addACTransmission()

    def buildPlant(self):
        self.plant = PlantEquipment(self.network_available_probability)

    def addSolarModulesAndInverter(self):

        for i in range(self.groups_number):
            eq_group = self.plant.add_Solar_group()
            eq_group.add_inverter(self.inverter_price, self.inverter_reliability, self.inverter_power_efficiency)
            for j in range(self.modules_in_group):
                eq_group.add_solar_module(self.module_price, self.module_reliability, self.module_power_efficiency, self.module_power)

    def addACTransmission(self):
        actransmission_group = self.plant.add_AC_group()
        actransmission_group.add_connection_grid(self.connection_grip_cost)
        if self.transformer_present:
            actransmission_group.add_transformer(self.transformer_price, self.transformer_reliability, self.transformer_power_efficiency)

    def getInvestmentCost(self):
        """return  investment costs of all plant"""
        return  self.plant.getInvestmentCost() + self.documentation_price

    def print_equipment(self):
        """prints all equipment tree"""
        print self.plant
        for i, group_info in enumerate(self.plant.get_groups()):
            print "Group: %s" % (i + 1)
            print group_info

    def calc_degradation_coefficients(self):
        degradation_coefficients = OrderedDict()
        for date in self.date_list:
            degradation_coefficients[date] = (1-self.degradation_yearly)**years_between_1Jan(self.start_date_project, date)
        self.degradation_coefficients = degradation_coefficients

    def get_module_degradation(self, date):
        """return  module degradation coefficient at given @date"""
        return  self.degradation_coefficients[date]

    def calc_project_datelist(self):
        self.date_list = get_list_dates(self.start_date_project, self.end_date_project)

    def generateElectiricityProduction(self, date):
        insolation = self.energy_module.get_insolation(date)
        degradation = self.get_module_degradation(date)
        production = self.plant.getElectricityProductionPlant1Day(insolation)
        return  production * degradation

    def getElectricityProduction(self, date_start, date_end):
        """return sum of electricity in kWh for each day for the selected period"""

        date_list = get_list_dates(date_start, date_end)
        electricity = 0
        for date in date_list:
            electricity += self.generateElectiricityProduction(date)

        return electricity

    def getElectricityProduction(self, date_start, date_end):
        date_list = get_list_dates(date_start, date_end)
        sun_values = numpy.array([self.plant.getElectricityProductionPlant1Day(1) for day in date_list])
        insolations = self.energy_module.insolations.values()
        degrodations = numpy.array(self.degradation_coefficients.values())
        return numpy.sum(sun_values*degrodations*insolations)

    def getElectricityProductionLifeTime(self):
        date_list = get_list_dates(self.start_date_project, self.end_date_project)
        sun_values = numpy.array([self.plant.getElectricityProductionPlant1Day(1) for day in date_list])
        insolations = self.energy_module.insolations.values()
        degrodations = numpy.array(self.degradation_coefficients.values())
        return numpy.sum(sun_values*degrodations*insolations)

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
            start_date = self.start_date_project
        if end_date is  None:
            end_date = self.end_date_project
        if resolution is  None:
            resolution = self.resolution

        x, y = self.get_xy_values_for_plot(start_date, end_date, resolution)
        pylab.step(x, y)
        pylab.show()


if __name__ == '__main__':
    from annex import timer
    import numpy
    mainconfig = MainConfig()
    em = EnergyModule(mainconfig)
    tm = TechnologyModule(mainconfig, em)
    #print tm.getConfigsValues()

    #print em.generatePrimaryEnergyAvaialbilityLifetime()
    start_date = datetime.date(2013, 1, 1)
    end_date = mainconfig.getEndDate()
    end_date_1d = datetime.date(2013, 1, 2)
    #tm.outputElectricityProduction(start_date, end_date)

    @timer
    def test_time():
        print  tm.getElectricityProduction(start_date, end_date)

    @timer
    def test_time2():
        print tm.getElectricityProduction(start_date, end_date)


    @timer
    def test_time3():
        print tm.getElectricityProductionLifeTime()


    tm.print_equipment()
    print tm.getInvestmentCost()
    test_time2()
    test_time3()
    #date_list = get_list_dates(start_date, end_date)
    #print [d.strftime('%Y-%m-%d') for d in date_list]
    #print tm.get_degradation_coefficients(date_list)

