#!/usr/bin/env python
# -*- coding utf-8 -*-

import random
import numpy
from annex import lastDayMonth, memoized, daysBetween, OrderedDefaultdict
from collections import defaultdict
from datetime import date, timedelta

class EQ:
    """Enum class to hold equpment types."""
    SOLAR_MODULE = 'solar module'
    INVERTER = 'inverter'
    TRANSFORMER = 'transformer'
    GRID_CONNECTION = 'grid connection'

class Equipment():
    """Is the principal class for all equipment.
    It holds things that all pieces of equipment must posses:
        * name
        * efficiency
        * price
        * MTBF
        * MTTR
    and provides interface description."""

    def __init__(self, eqtype, efficiency, price, mtbf, mttr, start_date, end_date):
        """
        @name - name of the equipment, for display purposes
        @efficiency - percentage of efficiency in transmiting or transforming power - expressed for modules in relation to 100% from intial efficiency - in inverters and transfromers and other elements it is effective efficieny of transmission
        @price - investment price in EU
        @mtbf - mean time between failures -- v fails in random time distributed as exp(1/mtbf)
        @mttr - mean time to repair -- repairs in random time distributes as exp(1/mttr) since failure
        """
        self.eqtype = eqtype
        self.efficiency = efficiency
        self.price = price
        self.mtbf = mtbf
        self.mttr = mttr
        self.start_date = start_date
        self.end_date = end_date

    def __str__(self):
        return ("""
            Equipment:
                Type: {eqtype}
                Price: {price}
                Effiency: {efficiency}
                MTBF: {mtbf}
                MTTR: {mttr}""".format(**self.__dict__))

    def getInvestmentCost(self):
        """Return investment cost (price) of equipment."""
        return self.price

    def getElectricityProduction(self):
        """Gets electiricity production for equipment."""
        return 0

    def isWorking(self, day):
        return True

class EquipmentSolarModule(Equipment):
    """Class for holding special info about Solar Modules."""

    def __init__(self, efficiency, price, mtbf, mttr, start_date, end_date, power, nominal_power, degradation_yearly):
        """Additional attributes are:
            @power - module power
            @nominal_power - module nominal power
            @degradation_yearly - yearly degradation_coefficient"""
        Equipment.__init__(self, EQ.SOLAR_MODULE, efficiency, price, mtbf, mttr, start_date, end_date)
        self.power = power
        self.nominal_power = nominal_power
        self.degradation_yearly = degradation_yearly

    def getElectricityProductionUsingInsolation(self, insolation, day):
        """Gets electiricity production for SolarModule."""
        if self.isWorking(day):
            return insolation * self.power / 1000.0 * self.efficiency *  self.conservation_coefficient(day)
        return 0

    def getElectricityProduction(self, avg_production_day_per_kW, day):
        """Gets electiricity production for SolarModule."""
        if self.isWorking(day):
            return avg_production_day_per_kW * self.power * self.efficiency * self.conservation_coefficient(day)
        return 0

    def conservation_coefficient(self, day):  #conservation as the opposite of degradation
        """Calculation of degradation coefficients for equipment depending years running.
           If degradation is so large that the production would be negative then it returns zero."""
        return max(0, 1 - daysBetween(self.start_date, day) * (self.degradation_yearly / 365.0))

    def __str__(self):
        return ("""
            Solar module:
                Price: {price}
                Effiency: {efficiency}
                MTBF: {mtbf}
                MTTR: {mttr}
                Power: {power}
                Nominal power: {nominal_power}
                degradation_yearly: {degradation_yearly}""".format(**self.__dict__))

class EquipmentConnectionGrid(Equipment):
    """Class for holding special info about connection grid."""
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, EQ.GRID_CONNECTION, *args, **kwargs)


class EquipmentInverter(Equipment):
    """Class for holding special info about Inverters"""
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, EQ.INVERTER, *args, **kwargs)


class EquipmentTransformer(Equipment):
    """Class for holding special info about Transformers"""
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, EQ.TRANSFORMER, *args, **kwargs)


################################# GROUPS ######################

class SolarGroup():
    """Class for holding info about solar module groups."""
    def __init__(self, start_date, end_date):
        self.solar_modules = [] # list of solar modules
        self.inverter = None
        self.start_date = start_date
        self.end_date = end_date

    def addSolarModule(self, efficiency, price, mtbf, mttr, power, nominal_power, degradation_yearly):
        """Adds a Solar module."""
        eq = EquipmentSolarModule(efficiency, price, mtbf, mttr, self.start_date, self.end_date, power, nominal_power, degradation_yearly)  # create Equipment class instance
        self.solar_modules.append(eq)

    def addInverter(self, efficiency, price, mtbf, mttr):
        """Adds an inverter, complains if one exists."""
        assert self.inverter is None, "Cannot add a second inverter."
        self.inverter = EquipmentInverter(efficiency, price, mtbf, mttr, self.start_date, self.end_date)

    def __str__(self):
        """String representation of group."""
        s = """
            #########################
            SOLAR GROUP:
            """
        s += """\n
            -------------------------
            Solar modules:
            """
        for sm in self.solar_modules:
            s += str(sm)
        s += """\n
            -------------------------
            Inverter:
            """
        s += str(self.inverter)
        return s

    def getInvestmentCost(self):
        """Returns investment cost of solar group."""
        solar_modules_cost = sum(eq.getInvestmentCost() for eq in self.solar_modules)
        return solar_modules_cost + self.inverter.getInvestmentCost()

    def isInverterWorking(self, day):
        """Returns inverter effiency if we have an inverter else 0."""
        if self.inverter is None: return False
        return self.inverter.isWorking(day)

    def getPower(self):
        """Returns total power of all solar modules in a group."""
        return sum(sm.power for sm in self.solar_modules)

    def getElectricityProductionGroupUsingInsolation(self, insolation, day):
        """return  ElectricityProduction for group"""
        if self.isInverterWorking(day):
            group_production = sum([
                eq.getElectricityProductionUsingInsolation(insolation, day)
                    for eq in self.solar_modules])
            return group_production * self.inverter.efficiency
        return group_production * percent_inverters_working

    def getElectricityProduction(self, avg_production_day_per_kW, day):
        """Returns electricity production for group - sum of equipment productions
        multiplied by inverter efficiency."""
        if self.isInverterWorking(day):
            group_production = sum([
                eq.getElectricityProduction(avg_production_day_per_kW, day)
                    for eq in self.solar_modules])
            return group_production * self.inverter.efficiency
        return 0

class ACGroup():
    """Class to hold info about AC elements."""

    def __init__(self, start_date, end_date):
        """AC elements are transformer and grid connection."""
        self.grid_connection = None
        self.transformer = None
        self.start_date = start_date
        self.end_date = end_date

    def addTransformer(self, efficiency, price, mtbf, mttr):
        """Adds transformer. Can be only ONE."""
        assert self.transformer is None, "Cannot add a second transformer."
        self.transformer = EquipmentTransformer(efficiency, price, mtbf, mttr, self.start_date, self.end_date)  # create Equipment class instance

    def addConnectionGrid(self, efficiency, price, mtbf, mttr):
        """Adds connection grid. Can be only ONE."""
        assert self.grid_connection is None, "Cannot add a second connection grid."
        self.grid_connection = EquipmentConnectionGrid(efficiency, price, mtbf, mttr, self.start_date, self.end_date)  # create Equipment class instance

    def __str__(self):
        s = """
            #########################
            SOLAR GROUP:
            """
        s += """\n
            -------------------------
            Transformer:
            """
        s += str(self.transformer)
        s += """\n
            -------------------------
            Grid connection:
            """
        s += str(self.grid_connection)
        return s

    def getInvestmentCost(self):
        """Returns investment cost of AC group."""
        return self.transformer.getInvestmentCost() + self.grid_connection.getInvestmentCost()

    def isTransformerWorking(self, day):
        """Returns transformer effiency for AC group if we have one else 0."""
        if self.transformer is None: return False
        return self.transformer.isWorking(day)

    def isGridAvailable(self, day):
        """Returns True if we have access to the grid else False."""
        if self.grid_connection is None: return False
        return self.grid_connection.isWorking(day)

################################ PLANT #######################

class PlantEquipment():
    """Class for whole plant equipment"""
    def __init__(self, country, start_date, end_date, energy_module):
        self.solar_groups = []  # list of all solar groups
        self.AC_group = None
        self.country = country
        self.energy_module = energy_module
        self.start_date = start_date
        self.end_date = end_date

    def addSolarGroup(self):
        """Adds new solar group and returns link to it."""
        self.solar_groups.append(SolarGroup(self.start_date, self.end_date))
        return self.solar_groups[-1]

    def addACGroup(self):
        """Adds AC group. Can only be one."""
        assert self.AC_group is None, "Cannot add a second AC group"
        self.AC_group = ACGroup(self.start_date, self.end_date)
        return self.AC_group

    def getInvestmentCost(self):
        """Return investment costs of the whole plant."""
        solar_groups_cost = sum(group.getInvestmentCost() for group in self.solar_groups)
        return solar_groups_cost + self.AC_group.getInvestmentCost()

    def getElectricityProductionPlant1DayUsingInsolation(self, insolation, day):
        """Returns electricity production for whole plant"""
        if self.AC_group.isTransformerWorking(day) and self.AC_group.isGridAvailable(day):
            avg_production_day_per_kW = self.energy_module.getAvgProductionDayPerKW(day)
            groups_production = sum(
                g.getElectricityProductionGroupUsingInsolation(insolation, day)
                    for g in self.solar_groups)   # calc sum of el.production for all solar groups
            transformer_eff = self.AC_group.transformer.efficiency
            grid_connection_eff = self.AC_group.grid_connection.efficiency
            return groups_production * transformer_eff * grid_connection_eff

    def getElectricityProduction1Day(self, day):
        """Returns electricity production for whole plant."""
        if self.AC_group.isTransformerWorking(day) and self.AC_group.isGridAvailable(day):
            avg_production_day_per_kW = self.energy_module.getAvgProductionDayPerKW(day)
            groups_production = sum(
                g.getElectricityProduction(avg_production_day_per_kW, day)
                    for g in self.solar_groups)   # calc sum of el.production for all solar groups
            transformer_eff = self.AC_group.transformer.efficiency
            grid_connection_eff = self.AC_group.grid_connection.efficiency
            return groups_production * transformer_eff * grid_connection_eff

        return 0

    def getPlantPower(self):
        """return  Total power of plant"""
        return sum(gr.getPower() for gr in self.solar_groups)

    def expectedYearProduction(self):
        """calculates aprox expected yealy production of electricity"""
        from config_readers import EnergyModuleConfigReader
        em_config = EnergyModuleConfigReader(self.country)  #load Inputs for Energy Module

        av_insolations = []
        days_in_month = []
        for i in range(1, 13):  #for each month number from 1 to 12
            av_insolations.append(em_config.getAvMonthInsolationMonth(i))  #add to list av.month insollation for 1 day
            days_in_month.append(lastDayMonth(date(2000,  i, 1)).day)  #  add to list number of days in cur month

        one_day_production = numpy.array([self.getElectricityProductionPlant1DayUsingInsolation(insolation, self.start_date) for insolation in av_insolations])  #calc one day production for this 12 days
        whole_year_production = numpy.sum(numpy.array(days_in_month) * one_day_production)  #multiply number of days in month * one day production and summarise them all

        return round(whole_year_production, 0)  #return rounded value

    def __str__(self):
        """string representation of Plant object"""
        s = """
            PLANT:
                total investment cost: {0}
                total power: {1}
                expected year production: {2}
            """.format(self.getInvestmentCost(), self.getPlantPower(), self.expectedYearProduction(), **self.__dict__)
        s += "\nSolar groups:\n"
        for sg in self.solar_groups:
            s += str(sg)

        s += str(self.AC_group)
        return s
