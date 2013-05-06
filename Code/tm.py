#!/usr/bin/env python
# -*- coding utf-8 -*-

import math
import pylab
import datetime
import ConfigParser
import os
from em import EnergyModule
from main_config_reader import MainConfig
from base_class import BaseClassConfig

class TechnologyModule(BaseClassConfig):
    def __init__(self, config_module, energy_module):
        BaseClassConfig.__init__(self, config_module)
        self.energy_module = energy_module
        self.loadConfig()
        self.assembleSystem()

    def loadConfig(self, filename='tm_config.ini'):
        """Reads module config file"""
        config = ConfigParser.ConfigParser()
        filepath = os.path.join(os.getcwd(), 'configs', filename)
        config.read(filepath)

        total_power = 10000
        one_module_power = 250
        modules_per_inverter = 4
        self.electr_conv_factor = config.getfloat('Electricity', 'ConversionFactor')

        self.total_power = config.getfloat('Equipment', 'total_power')
        self.one_module_power = config.getfloat('Equipment', 'one_module_power')
        self.modules_per_inverter = int(config.getfloat('Equipment', 'modules_per_inverter'))
        self.module_cost = config.getfloat('Equipment', 'module_cost')
        self.inverter_cost = config.getfloat('Equipment', 'inverter_cost')
        self.module_reliability = config.getfloat('Equipment', 'module_reliability') / 100
        self.inverter_reliability = config.getfloat('Equipment', 'inverter_reliability') / 100
        self.module_power_efficiency = config.getfloat('Equipment', 'module_power_efficiency') / 100
        self.inverter_power_efficiency = config.getfloat('Equipment', 'inverter_power_efficiency') / 100

        self.network_available_probability = config.getfloat('Network', 'network_available_probability') / 100


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
            start_date = self.start_date_project
        if end_date is  None:
            end_date = self.end_date_project
        if resolution is  None:
            resolution = self.resolution

        x, y = self.get_xy_values_for_plot(start_date, end_date, resolution)
        pylab.step(x, y)
        pylab.show()

    def assembleSystem(self):
        """generates objects for each solarmodule """
        self.number_of_modules = self.total_power // self.one_module_power
        self.number_of_inverters = int(math.ceil(self.number_of_modules / self.modules_per_inverter))
        self.equipment_groups = EquipmentGroups(self.network_available_probability)

        for i in range(self.number_of_inverters):
            eq_group = EquipmentGroup()
            eq_group.add_inverter(self.inverter_cost, self.inverter_reliability, self.inverter_power_efficiency)
            for j in range(self.modules_per_inverter):
                eq_group.add_solar_module(self.module_cost, self.module_reliability, self.module_power_efficiency)

            self.equipment_groups.add_group(eq_group)

    def print_equipment(self):
        """prints all equipment tree"""
        for group in self.equipment_groups.get_groups():
            print "\tGroup: %s" % group
            for eq in group.get_equipment():
                print "\t\tEquipment: %s" % eq


class Equipment():
    """Is the principal class for all equipment. """
    def __init__(self,reliability, cost, power_efficiency, state, system_crucial, group_cruical):
        """
        @state - current state - working, maintance, failure
        @system_crucial - if state is not working then the whole system does not work
        @group_cruical - if crucial then if state is not working then the respective group to which belongs does not work
        @reliability - % as of probability that it is working
        @cost - investments cost in EUR
        """
        self.state = 0
        self.crucial = True
        self.group_cruical = False
        self.power_efficiency = power_efficiency
        self.invesment_cost = cost
        self.reliability = reliability

    def isStateWorking(self):
        if self.getState() == 1:
            return  True
        else :
            return  False

    def isStateFailure(self):
        if self.getState() == 2:
            return  True
        else :
            return  False

    def isStateMaintenance(self):
        if self.getState() == 0:
            return  True
        else :
            return  False

    def getState(self):
        return  self.state

    def isCrucialForSystem(self):
        return  self.crucial

    def isCrucialForGroup(self):
        return  self.group_cruical


class EquipmentSolarModule(Equipment):
    """Class for holding special info about Solar Modules"""
    pass

class EquipmentInverter(Equipment):
    """Class for holding special info about Inverters"""
    pass

class EquipmentGroup():

    def __init__(self):
        self.group_equipment = []

    def add_solar_module(self, cost, reliability, efficiency):
        eq = EquipmentSolarModule(reliability, cost, efficiency, state=0, system_crucial=False, group_cruical=False)
        self.add_equipment(eq)

    def add_inverter(self, cost, reliability, efficiency):
        eq = EquipmentInverter(reliability, cost, efficiency, state=0, system_crucial=False, group_cruical=True )
        self.add_equipment(eq)

    def add_equipment(self,  equipment):
        """Base method to add new equipment - (equipment - class object)"""
        self.group_equipment.append(equipment)

    def isGroupUnderMaintenance():
        for equipment in self.group_equipment:
            if equipment.isStateMaintenance():
                return  True
        return False

    def get_equipment(self):
        return  self.group_equipment[:]


class EquipmentGroups():
    def __init__(self, network_available_probability ):
        self.groups = []
        self.network_available_probability = network_available_probability

    def add_group(self, group):
        self.groups.append(group)

    def isSystemOperational(self):
        """isSystemOperational = isNetworkAvailable * isSystemUnderMaintenance"""
        return  self.isNetworkAvailable() * self.isSystemUnderMaintenance()

    def isNetworkAvailable():
        """Availability of system network - user input as % of availability e.g. 99,9%
        return  False or True"""
        if random.random() >= self.network_available_probability:
            return  True
        else:
            return  False

    def isSystemUnderMaintenance():
        """check for maintenace of components (objects Equipment)"""
        for group in self.groups:
            if group.isGroupUnderMaintenance():
                return  True
        return False

    def get_groups(self):
        return  self.groups





if __name__ == '__main__':
    mainconfig = MainConfig()
    em = EnergyModule(mainconfig)
    tm = TechnologyModule(mainconfig, em)

    #print em.generatePrimaryEnergyAvaialbilityLifetime()
    start_date = datetime.date(2000, 1, 1)
    end_date = datetime.date(2001, 12, 31)
    tm.outputElectricityProduction(start_date, end_date)

    tm.print_equipment()
