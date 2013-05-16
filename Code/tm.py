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
from annex import get_configs


class TechnologyModule(BaseClassConfig, TechnologyModuleConfigReader):
    def __init__(self, config_module, energy_module):
        BaseClassConfig.__init__(self, config_module)
        TechnologyModuleConfigReader.__init__(self)
        self.energy_module = energy_module
        self.assembleSystem()
        self.calculate_equipment_investment_costs()

    def assembleSystem(self):
        """generates objects for each solarmodule """
        self.total_power = self.groups_number * self.modules_in_group * self.module_power

        self.equipment_groups = EquipmentGroups(self.network_available_probability)

        for i in range(self.groups_number):
            eq_group = EquipmentGroup()

            eq_group.add_inverter(self.inverter_price, self.inverter_reliability, self.inverter_power_efficiency)

            for j in range(self.modules_in_group):
                eq_group.add_solar_module(self.module_price, self.module_reliability, self.module_power_efficiency)

            self.equipment_groups.add_group(eq_group)

        transformer_group = EquipmentGroup()
        self.equipment_groups.add_group(transformer_group)
        for i in range(self.transformers_number):
            transformer_group.add_transformer(self.transformer_price, self.transformer_reliability,self.transformer_power_efficiency)

    def calculate_equipment_investment_costs(self):
        """Calculation of investment costs"""

        self.total_costs = (
            self.connection_grip_price +
            self.documentation_price +
            self.modules_in_group * self.groups_number * self.module_price +
            self.transformers_number * self.transformer_price +
            self.inverter_price * self.groups_number * self.inverter_price
            )

    def getEquipmentInvestmentCosts(self):
        return  self.total_costs



    def print_equipment(self):
        """prints all equipment tree"""
        for group in self.equipment_groups.get_groups():
            print "\tGroup: %s" % group
            for eq in group.get_equipment():
                print "\t\tEquipment: %s" % eq

    def generateElectiricityProduction(self, date):
        """based on insolation generates electricity production values for each day
        produced electricity = insolation * energyConversionFactor"""
        insolation = self.energy_module.get_insolation(date)
        return insolation * self.electr_conv_factor

    def getElectricityProduction(self, date_start, date_end):
        """return sum of electricity in kWh for each day for the selected period"""
        duration_days = (date_end - date_start).days
        return sum([self.generateElectiricityProduction(date_start+datetime.timedelta(days=i)) for i in range(duration_days+1) ])

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



class Equipment():
    """Is the principal class for all equipment. """
    def __init__(self,reliability, price, power_efficiency, state, system_crucial, group_cruical):
        """
        @state - current state - working, maintance, failure
        @system_crucial - if state is not working then the whole system does not work
        @group_cruical - if crucial then if state is not working then the respective group to which belongs does not work
        @reliability - % as of probability that it is working
        @price - investments price in EUR
        """
        self.state = 0
        self.crucial = True
        self.group_cruical = False
        self.power_efficiency = power_efficiency
        self.invesment_price = price
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

    def __str__(self):
        return "Name: %s  Price: %s  Reliability: %s  Effiency: %s" % (self.name,self.invesment_price, self.reliability, self.power_efficiency)

class EquipmentSolarModule(Equipment):
    """Class for holding special info about Solar Modules"""
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, *args, **kwargs)
        self.name = "Solar Module"

class EquipmentInverter(Equipment):
    """Class for holding special info about Inverters"""
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, *args, **kwargs)
        self.name = "Inverter"

class EquipmentTransformer(Equipment):
    """Class for holding special info about Transformers"""
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, *args, **kwargs)
        self.name = "Transformer"

class EquipmentGroup():

    def __init__(self):
        self.group_equipment = []

    def add_solar_module(self, price, reliability, efficiency):
        eq = EquipmentSolarModule(reliability, price, efficiency, state=0, system_crucial=False, group_cruical=False)
        self.add_equipment(eq)

    def add_inverter(self, price, reliability, efficiency):
        eq = EquipmentInverter(reliability, price, efficiency, state=0, system_crucial=False, group_cruical=True )
        self.add_equipment(eq)

    def add_transformer(self, price, reliability, efficiency):
        eq = EquipmentTransformer(reliability, price, efficiency, state=0, system_crucial=False, group_cruical=True )
        self.add_equipment(eq)

    def add_equipment(self,  equipment):
        """Base method to add new equipment - (equipment - class object)"""
        self.group_equipment.append(equipment)

    def isGroupUnderMaintenance(self):
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

    def isNetworkAvailable(self):
        """Availability of system network - user input as % of availability e.g. 99,9%
        return  False or True"""
        if random.random() >= self.network_available_probability:
            return  True
        else:
            return  False

    def isSystemUnderMaintenance(self):
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
    #print tm.getConfigsValues()

    #print em.generatePrimaryEnergyAvaialbilityLifetime()
    start_date = datetime.date(2013, 1, 1)
    end_date = datetime.date(2013, 12, 31)
    #tm.outputElectricityProduction(start_date, end_date)

    tm.print_equipment()
    print tm.getEquipmentInvestmentCosts()
