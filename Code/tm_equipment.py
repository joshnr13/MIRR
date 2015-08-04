#!/usr/bin/env python
# -*- coding utf-8 -*-

import random
import numpy
from annex import lastDayMonth, memoized, daysBetween, OrderedDefaultdict
from collections import defaultdict
from datetime import date, timedelta


class Equipment():
    """Is the principal class for all equipment."""
    def __init__(self, reliability, price, power_efficiency, power, degradation_yearly, state, system_crucial, group_cruical):
        """
        @reliability - % as of probability that it is working
        @price - investments price in EU
        @efficiency - percentage of efficiency in transmiting or transforming power - expressed for modules in relation to 100% from intial efficency - in inverterst and transfromers and other elements it is effective efficieny of transmission
        @power - current peak power of the system
        @degradation_yearly - yearly degradation rate, eg. 0.0354
        @state - current state - working, maintance, failure
        @system_crucial - if state is not working then the whole system does not work
        @group_cruical - if crucial then if state is not working then the respective group to which belongs does not work
        """
        self.name = ""
        self.reliability = reliability
        self.investment_price = price
        self.efficiency = power_efficiency
        self.power = power
        self.degradation_yearly = degradation_yearly
        self.state = 0
        self.crucial = True
        self.group_cruical = False
        self.start_power = power

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
        return "Name: %s  Price: %s  Reliability: %s  Effiency: %s" % (self.name,self.investment_price, self.reliability, self.efficiency)

    def getParams(self):
        """return  Equipment params dictionary"""
        return  self.__dict__

    def getInvestmentCost(self):
        """return  investment cost (price) of eqipment"""
        return self.investment_price

    def getElectricityProductionEquipmentUsingInsolation(self, insolation):
        """Gets electiricity production for equipment"""
        return 0

    def getElectricityProductionEquipment(self):
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

    def getElectricityProductionEquipmentUsingInsolation(self, insolation, days_from_start):
        """Gets electiricity production for SolarModule"""
        return insolation * self.power / 1000.0 * self.conservation_coefficient(days_from_start)

    def getElectricityProductionEquipment(self, avg_production_day_per_kW, days_from_start):
        """Gets electiricity production for SolarModule"""
        return avg_production_day_per_kW * self.power * self.conservation_coefficient(days_from_start)

    def conservation_coefficient(self, days_from_start):  #conservation as the opposite of degradation
        """Calculation of degradation coefficients for equipment depending years running.
           If degradation is so large that the production would be negative then it returns zero."""
        return max(0, 1 - days_from_start * (self.degradation_yearly / 365.0))

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
        self.maintenance_schedule = kwargs.pop('maintenance_schedule')
        Equipment.__init__(self, *args, **kwargs)
        self.name = "Inverter Equipment"

    def isWorking(self, day):
        """Return bool is inverter working or not (under maintenance) on current date @day"""
        return self.maintenance_schedule[day]


class EquipmentTransformer(Equipment):
    """Class for holding special info about Transformers"""
    def __init__(self, *args, **kwargs):
        Equipment.__init__(self, *args, **kwargs)
        self.name = "Transformer Equipment"

################################# GROUPS ######################


class EquipmentGroup():
    """Class for holding info about equipment group"""
    def __init__(self, group_type, maintenance_calculator):
        self.group_type = group_type
        self.group_equipment = defaultdict(list)  #list for holding content of group equipment
        self.inverters = 0
        self.solar_modules = 0
        self.transformers = 0
        self.connection_grids = 0

        self.transformer_object = None
        self.connectiongrid_object = None
        self.maintenance_calculator = maintenance_calculator  # for calculating maintenance schedule
        self.first_day_production = self.maintenance_calculator.start_production

    def getGroupType(self):
        return  self.group_type

    def addConnectionGrid(self, price):
        """Adds connection Grid! Could be only ONE"""
        eq = EquipmentConnectionGrid(reliability=1, price=price, power_efficiency=1, power=None, degradation_yearly=None, state=0, system_crucial=False, group_cruical=False) #create Equipment class instance
        self.connectiongrid_object = eq
        self.connection_grids = 1
        self.addEquipment(eq, type='connection_grid')  #adds new created equipment to group with defined type

    def addSolarModule(self, price, reliability, power_efficiency, power, degradation_yearly):
        eq = EquipmentSolarModule(reliability=reliability, price=price, power_efficiency=power_efficiency, power=power, degradation_yearly=degradation_yearly, state=0, system_crucial=False, group_cruical=False) #create Equipment class instance
        self.solar_modules += 1  #increase number of solar modules in group
        self.addEquipment(eq, type='solar_module') #adds new created equipment to group with defined type

    def addInverter(self, price, power_efficiency):
        # generate maintenance for all period for current inverter
        schedule = self.maintenance_calculator.generate_schedule()

        # create Equipment class instance
        eq = EquipmentInverter(reliability=100, price=price, power_efficiency=power_efficiency,
                               power=None, degradation_yearly=None, state=0, system_crucial=False,
                               group_cruical=True, maintenance_schedule=schedule)

        self.inverters += 1  #increase number of inverters in group
        self.addEquipment(eq, type='inverter') #adds new created equipment to group with defined type

    def addTransformer(self, price, reliability, power_efficiency):
        """Adds connection Grid! Could be only ONE"""
        eq = EquipmentTransformer(reliability=reliability, price=price, power_efficiency=power_efficiency, power=None, degradation_yearly=None, state=0, system_crucial=False, group_cruical=True )  #create Equipment class instance
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

    def getPercentInvertersWorking(self, day):
        """return percent (0.0 - 1.0) of inverters not under maintenance at @day"""
        result = []
        for inverter in self.getInverterEquipment():
            result.append(inverter.isWorking(day))
        percent_working = sum(result) / float(len(result))
        return percent_working

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

    def getElectricityProductionGroupUsingInsolation(self, insolation, day):
        """return  ElectricityProduction for group"""
        days_from_start = daysBetween(self.first_day_production, day)
        group_production = sum([eq.getElectricityProductionEquipmentUsingInsolation(insolation, days_from_start) for eq in self.getSolarEquipment()])  #calc sum of all group electricity production
        percent_inverters_working = self.getPercentInvertersWorking(day)
        return group_production * percent_inverters_working

    def getElectricityProductionGroup(self, avg_production_day_per_kW, day):
        """return  ElectricityProduction for group"""
        days_from_start = daysBetween(self.first_day_production, day)
        group_production = sum([eq.getElectricityProductionEquipment(avg_production_day_per_kW, days_from_start)
                                for eq in self.getSolarEquipment()])  #calc sum of all group electricity production
        percent_inverters_working = self.getPercentInvertersWorking(day)
        return group_production * percent_inverters_working

################################ PLANT #######################


class PlantEquipment():
    """Class for whole plant equipment"""
    def __init__(self, network_available_probability, country, maintenance_calculator, energy_module):
        self.groups = defaultdict(list)  #for holding list of groups in plant
        self.network_available_probability = network_available_probability  #probability of AC system network
        self.AC_group = None
        self.country = country
        self.energy_module = energy_module
        self.maintenance_calculator = maintenance_calculator  # for calculating maintenance schedule
        self.first_day_production = self.maintenance_calculator.start_production

    def addGroup(self, group_type):
        """adds new group and returns link to it"""
        group = EquipmentGroup(group_type, maintenance_calculator=self.maintenance_calculator)
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

    def getElectricityProductionPlant1DayUsingInsolation(self, insolation, day):
        """return  ElectiricityProduction for whole Plant"""
        if self.isGridAvailable():  #if we have connection grid in plant
            groups_production = sum(g.getElectricityProductionGroupUsingInsolation(insolation, day) for g in self.getPlantSolarGroups())  #calc sum of el.production for all solar groups
            transformer_efficiency = self.getTransformerEffiency()
            return  groups_production * transformer_efficiency
        else:
            return 0

    def getElectricityProductionPlant1Day(self, day):
        """return  ElectiricityProduction for whole Plant"""
        if self.isGridAvailable():  #if we have connection grid in plant
            avg_production_day_per_kW = self.energy_module.getAvgProductionDayPerKW(day)
            groups_production = sum(g.getElectricityProductionGroup(avg_production_day_per_kW, day)
                                    for g in self.getPlantSolarGroups())  #calc sum of el.production for all solar groups
            transformer_efficiency = self.getTransformerEffiency()
            return groups_production * transformer_efficiency
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

        one_day_production = numpy.array([self.getElectricityProductionPlant1DayUsingInsolation(insolation, self.first_day_production) for insolation in av_insolations])  #calc one day production for this 12 days
        whole_year_production = numpy.sum(numpy.array(days_in_month) * one_day_production)  #multiply number of days in month * one day production and summarise them all

        return round(whole_year_production, 0)  #return rounded value

    def __str__(self):
        """string representation of Plant object"""
        return  "Installed Power %s kW . Expected yearly energy production %s kWh" % (self.getPlantPower(), self.expectedYearProduction())


class MaintenanceSchedule(object):
    def __init__(self, start_production, end_production, mtbf, mttr):
        self.start_production = start_production
        self.end_production = end_production
        self.mtbf = mtbf
        self.mttr = mttr

    def generate_mtbf_days(self):
        """return MTBF - mean time between failures, days"""
        return self.get_value(self.mtbf)

    def generate_mttr_days(self):
        """return MTTR - mean time to repair, days"""
        return self.get_value(self.mttr)

    def generate_next_failure_date(self, start_date):
        """genereate and return date when we will have next falure"""
        mtbf_days = self.generate_mtbf_days()
        next_failure_date = start_date + timedelta(days=mtbf_days + 1)
        return next_failure_date

    def generate_next_date_failure_repaired(self, next_failure_date):
        """genereate and return date when @next_failure_date will be repaired"""
        mttr_days = self.generate_mttr_days()
        next_failure_repaired_date = next_failure_date + timedelta(days=mttr_days + 1)
        return next_failure_repaired_date

    def get_value(self, average):
        """return weibull distribution value, using supplied params rounded to WHOLE DAYS"""
        lambd = 1.0 / average      #calculate lambda as inversion of mean time between events
        return int(random.expovariate(lambd))  # rget value from an exponential distribution

    def generate_schedule(self):
        """return dict with key=date and value = 1(WORKING), 0 (UNDER MAINTENANCE)"""
        day = self.start_production

        # generate initial (first) mtbf and mttr
        next_failure = self.generate_next_failure_date(day)
        next_failure_repaired = self.generate_next_date_failure_repaired(next_failure)
        working = True

        schedule = OrderedDefaultdict(lambda: True)  # default value - working (True)
        while day <= self.end_production:
            if day == next_failure:
                working = False
            elif day == next_failure_repaired:
                working = True

                # re-generate mtbf and mttr after failure repaired
                next_failure = self.generate_next_failure_date(day)
                next_failure_repaired = self.generate_next_date_failure_repaired(next_failure)

            schedule[day] = working  # fill schedule dict values
            day += timedelta(days=1)

        return schedule
