#!/usr/bin/env python
# -*- coding utf-8 -*-

import random
import numpy
from annex import lastDayMonth, memoized
from collections import defaultdict
from datetime import date


class Equipment():
    """Is the principal class for all equipment. """
    def __init__(self,reliability, price, power_efficiency, power, state, system_crucial, group_cruical):
        """
        @state - current state - working, maintance, failure
        @system_crucial - if state is not working then the whole system does not work
        @group_cruical - if crucial then if state is not working then the respective group to which belongs does not work
        @reliability - % as of probability that it is working
        @price - investments price in EU
        @efficiency - percentage of efficiency in transmiting or transforming power - expressed for modules in relation to 100% from intial efficency - in inverterst and transfromers and other elements it is effective efficieny of transmission
        @power - current peak power of the system
        @nominal power - peak power at start
        """
        self.state = 0
        self.crucial = True
        self.group_cruical = False
        self.efficiency = power_efficiency
        self.invesment_price = price
        self.reliability = reliability
        self.nominal_power = power
        self.power = power
        self.name = ""

    def isStateWorking(self):
        """return  True if Equipment state Working"""
        if self.getState() == 1:
            return  True
        else :
            return  False

    def isStateFailure(self):
        """return  True if Equipment state Failure"""
        if self.getState() == 2:
            return  True
        else :
            return  False

    def isStateMaintenance(self):
        """return  True if Equipment state Maintance"""
        if self.getState() == 0:
            return  True
        else :
            return  False

    def getState(self):
        """return  state value of equipment"""
        return  self.state

    def isCrucialForSystem(self):
        """return  is this equipment crucial for system"""
        return  self.crucial

    def isCrucialForGroup(self):
        """return  is this equipment crucial for group"""
        return  self.group_cruical

    def __str__(self):
        return "Name: %s  Price: %s  Reliability: %s  Effiency: %s" % (self.name,self.invesment_price, self.reliability, self.efficiency)

    def getParams(self):
        """return  Equipment params dictionary"""
        return  self.__dict__

    def getInvestmentCost(self):
        """return  investment cost (price) of eqipment"""
        return self.invesment_price

    def getElectricityProductionEquipment(self, insolation):
        """Gets electiricity production for equipment"""
        return 0

    def getEfficiency(self):
        """return  equipment effiency"""
        return  self.efficiency


class EquipmentSolarModule(Equipment):
    """Class for holding special info about Solar Modules"""
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, *args, **kwargs)
        self.name = "SolarModule Equipment"

    def getElectricityProductionEquipment(self, insolation):
        """Gets electiricity production for SolarModule"""
        return insolation * self.power / 1000.0

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
    """Class for holding info about equipment group"""
    def __init__(self, group_type):
        self.group_type = group_type
        self.group_equipment = defaultdict(list)  #list for holding content of group equipment
        self.inverters = 0
        self.solar_modules = 0
        self.transformers = 0
        self.connection_grids = 0

        self.transformer_object = None
        self.connectiongrid_object = None

    def getGroupType(self):
        return  self.group_type

    def addConnectionGrid(self, price):
        """Adds connection Grid! Could be only ONE"""
        eq = EquipmentConnectionGrid(reliability=1, price=price, power_efficiency=1, power=None, state=0, system_crucial=False, group_cruical=False) #create Equipment class instance
        self.connectiongrid_object = eq
        self.connection_grids = 1
        self.addEquipment(eq, type='connection_grid')  #adds new created equipment to group with defined type

    def addSolarModule(self, price, reliability, power_efficiency, power):
        eq = EquipmentSolarModule(reliability, price, power_efficiency,power, state=0, system_crucial=False, group_cruical=False) #create Equipment class instance
        self.solar_modules += 1  #increase number of solar modules in group
        self.addEquipment(eq, type='solar_module') #adds new created equipment to group with defined type

    def addInverter(self, price, reliability, power_efficiency):
        eq = EquipmentInverter(reliability, price, power_efficiency, power=None, state=0, system_crucial=False, group_cruical=True ) #create Equipment class instance
        self.inverters += 1  #increase number of inverters in group
        self.addEquipment(eq, type='inverter') #adds new created equipment to group with defined type

    def addTransformer(self, price, reliability, power_efficiency):
        """Adds connection Grid! Could be only ONE"""
        eq = EquipmentTransformer(reliability, price, power_efficiency, power=None, state=0, system_crucial=False, group_cruical=True )  #create Equipment class instance
        self.transformers = 1
        self.transformer_object = eq
        self.addEquipment(eq, type='transformer')  #adds new created equipment to group with defined type

    def addEquipment(self,  equipment, type):
        """Base method to add new equipment - (equipment - class object)"""
        self.group_equipment[type].append(equipment)

    def isGroupUnderMaintenance(self):
        """return  True if one of group equipment is Under Maintance"""
        for equipment in self.group_equipment:
            if equipment.isStateMaintenance():
                return  True
        return False

    def getGroupPower(self):
        """return  solar power of all solar modules in group"""
        return sum([g.getPower() for g in self.getSolarEquipment()])

    def getSolarEquipment(self):
        """return  list of solar modules in current group"""
        return  self.group_equipment['solar_module']

    def getInverterEquipment(self):
        """return  list of inverters  in current group"""
        return  self.group_equipment['inverter']

    def getConnectionGridEquipment(self):
        """return list of grid equipment  in current group"""
        return  self.group_equipment['connection_grid']

    def getTransformerEquipment(self):
        """return  list of transformers  in current group"""
        return  self.group_equipment['transformer']

    def getGroupEquipment(self):
        """return  list of all equipment  in current group"""
        return  (
                self.getSolarEquipment() +
                self.getInverterEquipment() +
                self.getTransformerEquipment() +
                self.getConnectionGridEquipment()
                )

    def getGroupEquipmentParams(self, cls):
        """return  all equipment params in current group"""
        for eq in self.getGroupEquipment():
            if isinstance(eq, cls):
                return eq.getParams()
        else:
            return {}

    def __str__(self):
        """string representation of group"""
        description = []
        if self.solar_modules:
            solar_params = self.getGroupEquipmentParams(EquipmentSolarModule)
            solar_params['solar_modules'] = self.solar_modules
            solar_params['group_power'] = self.solar_modules * solar_params['power']
            solar_params['group_power'] = self.getGroupPower()

            s =  "Group power {group_power}KW ({solar_modules} x Solar Module {power}kW), Reliability: {reliability}, Effiency: {efficiency}".format(**solar_params)
            description.append(s)

        if self.inverters:
            inverter_params = self.getGroupEquipmentParams(EquipmentInverter)
            inverter_params['inverter_modules'] = self.inverters
            i =  "{inverter_modules} x Inverter, Reliability: {reliability}, Effiency: {efficiency}".format(**inverter_params)
            description.append(i)

        if self.transformers:
            transformer_params = self.getGroupEquipmentParams(EquipmentTransformer)
            transformer_params['transformer_modules'] = self.transformers
            t =  "{transformer_modules} x Transformer, Reliability: {reliability}, Effiency: {efficiency}".format(**transformer_params)
            description.append(t)

        if self.connection_grids:
            connection_grid_params = self.getGroupEquipmentParams(EquipmentConnectionGrid)
            connection_grid_params['connection_grids'] = self.connection_grids
            t =  "{connection_grids} x Connection grid".format(**connection_grid_params)
            description.append(t)

        return "  " + "\n  ".join(description)

    def getInvestmentCost(self):
        """return  investment cost of group"""
        total = 0
        for eq in self.getGroupEquipment():
            total += eq.getInvestmentCost()  #calculate sum of all equipment investment costs
        return total

    def getInverterEffiency(self):
        """return  Inverter effiency if available"""
        if self.getInverterEquipment():
            return  self.getInverterEquipment()[0].getEfficiency()  #return  InverterEffiency if we have inverter or 0
        else:
            return 0

    def getElectricityProductionGroup(self, insolation):
        """return  ElectiricityProduction for group"""
        group_production = sum([eq.getElectricityProductionEquipment(insolation) for eq in self.getSolarEquipment()])  #calc sum of all group electricity production
        inverter_efficiency = self.getInverterEffiency()
        return  group_production * inverter_efficiency


################################ PLANT #######################


class PlantEquipment():
    """Class for whole plant equipment"""
    def __init__(self, network_available_probability, country):
        self.groups = defaultdict(list)  #for holding list of groups in plant
        self.network_available_probability = network_available_probability  #probability of AC system network
        self.AC_group = None
        self.country = country

    def addGroup(self, group_type):
        """adds new group and returns link to it"""
        group = EquipmentGroup(group_type)
        self.groups[group_type].append(group)
        return group

    def addSolarGroup(self):
        """adds new group  SOLAR and returns link to it"""
        group_type = 'Solar group'
        return  self.addGroup(group_type)

    def addACGroup(self):
        """adds new group transformer and connection grid group and returns link to it"""
        group_type = 'AC group'
        self.AC_group = self.addGroup(group_type)
        return self.AC_group

    def isSystemOperational(self):
        """isSystemOperational = isNetworkAvailable * isSystemUnderMaintenance"""
        return  self.isNetworkAvailable() * self.isSystemUnderMaintenance()

    def isNetworkAvailable(self):
        """Availability of system network - user input as % of availability e.g. 99,9%
        return  False or True"""
        if random.random() <= self.network_available_probability:  #we generate random (0-1) and if it is > our_prob <= return  True
            return  True
        else:
            return  False  #else if random > our_prob -> EPIC FAIL

    def isSystemUnderMaintenance(self):
        """check for maintenace of components (objects Equipment)"""
        for group in self.groups:
            if group.isGroupUnderMaintenance():  #check for each group is it under maintance, and if one group is -> than all plant is under maintance - CORRECT THIS TO: If AC group is under maintenance or if all arrays are in maintenance then system is in maintenance
                return  True
        return False

    def getPlantGroups(self):
        """return  Plant solar and AC groups"""
        return  self.getPlantSolarGroups() + self.get_AC_group()

    def getPlantSolarGroups(self):
        """return  Plant solar groups"""
        return self.groups['Solar group']

    def get_AC_group(self):
        """return  Plant  AC groups"""
        return self.groups['AC group']

    def getInvestmentCost(self):
        """return  Investment costs of ALL equipment groups"""
        return sum(group.getInvestmentCost() for group in self.getPlantGroups())  #sum of each group IC in Plant

    @memoized
    def getTransformerEffiency(self):
        """returns transformet effiency for AC group, else 0"""
        if self.get_AC_group():  #if we have AC group
            obj = self.get_AC_group()[0].getTransformerEquipment()
            if obj:  #if we have transformer in AC group
                return obj[0].getEfficiency()
        return 0

    @memoized
    def isGridAvailable(self):
        """return  True if connection grid available in plant"""
        if self.get_AC_group(): #if we have AC group
            if self.get_AC_group()[0].getConnectionGridEquipment():
                return True  #return  True if we have connection grid in AC group
        return False

    def getElectricityProductionPlant1Day(self, insolation):
        """return  ElectiricityProduction for whole Plant"""
        if self.isGridAvailable():  #if we have connection grid in plant
            groups_production = sum(g.getElectricityProductionGroup(insolation) for g in self.getPlantSolarGroups())  #calc sum of el.production for all solar groups
            transformer_efficiency = self.getTransformerEffiency()
            return  groups_production * transformer_efficiency
        else:
            return 0

    def getPlantPower(self):
        """return  Total power of plant"""
        return sum(gr.getGroupPower() for gr in self.getPlantSolarGroups())

    def expectedYearProduction(self):
        """calculates aprox expected yealy production of electricity"""
        from config_readers import EnergyModuleConfigReader
        em_config = EnergyModuleConfigReader(self.country)  #load Inputs for Energy Module

        av_insolations = []
        days_in_month = []
        for i in range(1, 13):  #for each month number from 1 to 12
            av_insolations.append(em_config.getAvMonthInsolationMonth(i))  #add to list av.month insollation for 1 day
            days_in_month.append(lastDayMonth(date(2000,  i, 1)).day)  #  add to list number of days in cur month

        one_day_production = numpy.array([self.getElectricityProductionPlant1Day(insolation) for insolation in av_insolations])  #calc one day production for this 12 days
        whole_year_production = numpy.sum(numpy.array(days_in_month) * one_day_production)  #multiply number of days in month * one day production and summarise them all

        return round(whole_year_production, 0)  #return rounded value

    def __str__(self):
        """string representation of Plant object"""
        return  "Installed Power %s kW . Expected yearly energy production %s kWh" % (self.getPlantPower(), self.expectedYearProduction())


if __name__ == '__main__':
    p = PlantEquipment(1, 'NoCountry')
    print p.expectedYearProduction()

