import os
import random
import numpy

from annex import memoize, last_day_month
from collections import defaultdict
from em import  InputsReader
from datetime import date
################################# Equipment ######################

class Equipment():
    """Is the principal class for all equipment. """
    def __init__(self,reliability, price, power_efficiency, power, state, system_crucial, group_cruical):
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
        self.efficiency = power_efficiency
        self.invesment_price = price
        self.reliability = reliability
        self.power = power
        self.name = ""

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
        return "Name: %s  Price: %s  Reliability: %s  Effiency: %s" % (self.name,self.invesment_price, self.reliability, self.efficiency)

    def get_params(self):
        return  self.__dict__

    def getInvestmentCost(self):
        """return  investment cost (price) of eqipment"""
        return self.invesment_price

    def getElectricityProductionEquipment(self, insolation):
        """Gets electiricity production for equipment"""
        return 0

    def getEfficiency(self):
        return  self.efficiency


class EquipmentSolarModule(Equipment):
    """Class for holding special info about Solar Modules"""
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, *args, **kwargs)
        self.name = "SolarModule Equipment"

    def getElectricityProductionEquipment(self, insolation):
        """Gets electiricity production for SolarModule"""
        return insolation * self.power * self.efficiency / 1000

    def getPower(self):
        return self.power

class EquipmentConnectionGrid(Equipment):
    """Class for holding special info about Solar Modules"""
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, *args, **kwargs)
        self.name = "ConnectionGrid Equipment"

class EquipmentInverter(Equipment):
    """Class for holding special info about Inverters"""
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, *args, **kwargs)
        self.name = "Inverter Equipment"

class EquipmentTransformer(Equipment):
    """Class for holding special info about Transformers"""
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, *args, **kwargs)
        self.name = "Transformer Equipment"


################################# GROUPS ######################

class EquipmentGroup():

    def __init__(self, group_type):
        self.group_type = group_type
        self.group_equipment = defaultdict(list)
        self.inverters = 0
        self.solar_modules = 0
        self.transformers = 0
        self.connection_grids = 0

        self.transformer_object = None
        self.connectiongrid_object = None

    def getGroupType(self):
        return  self.group_type

    def add_connection_grid(self, price):
        """Adds connection Grid! Could be only ONE"""
        eq = EquipmentConnectionGrid(reliability=1, price=price, power_efficiency=1, power=None, state=0, system_crucial=False, group_cruical=False)
        self.connectiongrid_object = eq
        self.connection_grids = 1
        self.add_equipment(eq, type='connection_grip')

    def add_solar_module(self, price, reliability, power_efficiency, power):
        eq = EquipmentSolarModule(reliability, price, power_efficiency,power, state=0, system_crucial=False, group_cruical=False)
        self.solar_modules += 1
        self.add_equipment(eq, type='solar_module')

    def add_inverter(self, price, reliability, power_efficiency):
        eq = EquipmentInverter(reliability, price, power_efficiency, power=None, state=0, system_crucial=False, group_cruical=True )
        self.inverters += 1
        self.add_equipment(eq, type='inverter')

    def add_transformer(self, price, reliability, power_efficiency):
        """Adds connection Grid! Could be only ONE"""
        eq = EquipmentTransformer(reliability, price, power_efficiency, power=None, state=0, system_crucial=False, group_cruical=True )
        self.transformers = 1
        self.transformer_object = eq
        self.add_equipment(eq, type='transformer')

    def add_equipment(self,  equipment, type):
        """Base method to add new equipment - (equipment - class object)"""
        self.group_equipment[type].append(equipment)

    def isGroupUnderMaintenance(self):
        for equipment in self.group_equipment:
            if equipment.isStateMaintenance():
                return  True
        return False

    def get_group_power(self):
        """return  solar power of all solar modules in group"""
        return sum([g.getPower() for g in self.get_solar_equipment()])

    def get_solar_equipment(self):
        """return  list of solar modules"""
        return  self.group_equipment['solar_module']

    def get_inverter_equipment(self):
        """return  list of inverters"""
        return  self.group_equipment['inverter']

    def get_connection_grid_equipment(self):
        """return list of grid equipment"""
        return  self.group_equipment['connection_grip']

    def get_transformer_equipment(self):
        """return  list of transformers"""
        return  self.group_equipment['transformer']

    def get_equipment(self):
        return  (
                self.get_solar_equipment() +
                self.get_inverter_equipment() +
                self.get_transformer_equipment() +
                self.get_connection_grid_equipment()
                )

    def get_equipment_params(self, cls):
        for eq in self.get_equipment():
            if isinstance(eq, cls):
                return eq.get_params()
        else:
            return {}

    def __str__(self):
        description = []
        if self.solar_modules:
            solar_params = self.get_equipment_params(EquipmentSolarModule)
            solar_params['solar_modules'] = self.solar_modules
            solar_params['group_power'] = self.solar_modules * solar_params['power']
            solar_params['group_power'] = self.get_group_power()

            s =  "Group power {group_power}KW ({solar_modules} x Solar Module {power}kW), Reliability: {reliability}, Effiency: {efficiency}".format(**solar_params)
            description.append(s)

        if self.inverters:
            inverter_params = self.get_equipment_params(EquipmentInverter)
            inverter_params['inverter_modules'] = self.inverters
            i =  "{inverter_modules} x Inverter, Reliability: {reliability}, Effiency: {efficiency}".format(**inverter_params)
            description.append(i)

        if self.transformers:
            transformer_params = self.get_equipment_params(EquipmentTransformer)
            transformer_params['transformer_modules'] = self.transformers
            t =  "{transformer_modules} x Transformer, Reliability: {reliability}, Effiency: {efficiency}".format(**transformer_params)
            description.append(t)

        if self.connection_grids:
            connection_grid_params = self.get_equipment_params(EquipmentConnectionGrid)
            connection_grid_params['connection_grids'] = self.connection_grids
            t =  "{connection_grids} x Connection grid".format(**connection_grid_params)
            description.append(t)

        return "  " + "\n  ".join(description)

    def getInvestmentCost(self):
        """return  investment cost of group"""
        total = 0
        for eq in self.get_equipment():
            total += eq.getInvestmentCost()
        return total

    def getInverterEffiency(self):
        if self.get_inverter_equipment():
            return  self.get_inverter_equipment()[0].getEfficiency()
        else:
            return 0

    #@profile
    def getElectricityProductionGroup(self, insolation):
        """return  ElectiricityProduction for group"""
        group_production = sum([eq.getElectricityProductionEquipment(insolation) for eq in self.get_solar_equipment()])
        inverter_efficiency = self.getInverterEffiency()
        return  group_production * inverter_efficiency


################################ PLANT #######################


class PlantEquipment():
    def __init__(self, network_available_probability ):
        self.groups = defaultdict(list)
        self.network_available_probability = network_available_probability
        self.AC_group = None

    def __add_group(self, group_type):
        """adds new group and returns link to it"""
        group = EquipmentGroup(group_type)
        self.groups[group_type].append(group)
        return group

    def add_Solar_group(self):
        """adds new group  SOLAR and returns link to it"""
        group_type = 'Solar group'
        return  self.__add_group(group_type)

    def add_AC_group(self):
        """adds new group AC and returns link to it"""
        group_type = 'AC group'
        self.AC_group = self.__add_group(group_type)
        return self.AC_group


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
        return  self.get_Solar_groups() + self.get_AC_group()

    def get_Solar_groups(self):
        return self.groups['Solar group']

    def get_AC_group(self):
        return self.groups['AC group']

    def getInvestmentCost(self):
        """return  Investment costs of ALL equipment groups"""
        total = 0
        for group in (self.get_groups()):
            total += group.getInvestmentCost()
        return total

    #@memoize
    def getTransformerEffiency(self):
        if self.get_AC_group():
            obj = self.get_AC_group()[0].get_transformer_equipment()
            if obj:
                return obj[0].getEfficiency()
        else:
            return 0

    #@memoize
    def isGridAvailable(self):
        if self.get_AC_group():
            if self.get_AC_group()[0].get_connection_grid_equipment():
                return True
        return  False

    ##@profile
    def getElectricityProductionPlant1Day(self, insolation):
        """return  ElectiricityProduction for whole Plant"""

        if self.isGridAvailable():
            groups_production = sum([g.getElectricityProductionGroup(insolation) for g in self.get_Solar_groups()])
            transformer_efficiency = self.getTransformerEffiency()
            return  groups_production * transformer_efficiency
        else:
            return 0

    def getPlantPower(self):
        """return  Total power of plant"""
        return sum([gr.get_group_power() for gr in self.get_Solar_groups()])

    def expectedYearProduction(self):
        inputs = InputsReader()

        av_insolations = []
        days = []
        for i in range(1, 13):
            last_month_date = last_day_month(date(2000,  i, 1))
            av_insolations.append(inputs.getAvMonthInsolation(last_month_date))
            days.append(last_month_date.day)

        one_day_production = numpy.array([self.getElectricityProductionPlant1Day(insolation) for insolation in av_insolations])
        whole_year_production = numpy.sum(numpy.array(days) * one_day_production)

        return  round(whole_year_production, 0)


    def __str__(self):
        return  "Plant Power %s KW . Expected year power production %s KW" % (self.getPlantPower(), self.expectedYearProduction())


if __name__ == '__main__':
    p = PlantEquipment(1)
    print p.expectedYearProduction()

