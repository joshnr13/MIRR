#!/usr/bin/env python
# -*- coding utf-8 -*-

import numpy
from em import EnergyModule
from datetime import timedelta
from config_readers import MainConfig, TechnologyModuleConfigReader
from base_class import BaseClassConfig
from annex import daysBetween, getResolutionStartEnd, cached_property, get_list_dates
from tm_equipment import PlantEquipment
from collections import OrderedDict


class TechnologyModule(BaseClassConfig, TechnologyModuleConfigReader):
    def __init__(self, config_module, energy_module, country):
        BaseClassConfig.__init__(self, config_module)  #loading main configs
        TechnologyModuleConfigReader.__init__(self, country)  #loading Technology module configs
        self.country = country
        self.energy_module = energy_module
        self.assembleSystem()  #creates Plant
        self.calcTotalPower()  #calculates Total Power
        self.calcTotalNominalPower()  #calculates Total Nominal Power
        self.getInvestmentCost()  #calc investment costs of all plant + documentation

    def calcTotalPower(self):
        """Calculates total power for whole plant"""
        self.total_power = self.groups_number * self.modules_in_group * self.module_power

    def calcTotalNominalPower(self):
        """Calculates total power for whole plant"""
        self.total_nominal_power = self.groups_number * self.modules_in_group * self.module_nominal_power


    def assembleSystem(self):
        """generates objects for each solarmodule in plant"""
        self.buildPlant()  #create plant
        self.addSolarModulesAndInverter()  #add solar modules and inverters to plant
        self.addACTransmission()  #add transformer and connection grid to plant

    def buildPlant(self):
        """Creates plant object."""
        self.plant = PlantEquipment(
            self.first_day_production, self.end_date_project,
            energy_module=self.energy_module,
            additional_investment_costs=self.documentation_price + self.other_investment_costs) # new class Plant

    def addSolarModulesAndInverter(self):
        """Adds solar module and inverter in each group."""
        self.module_power_efficiency *= (1 + self.modelling_error) # correct module efficiency
        for i in range(self.groups_number):
            eq_group = self.plant.addSolarGroup()
            eq_group.addInverter(self.inverter_power_efficiency, self.inverter_price, self.inverter_mttf, self.inverter_mttr)
            for j in range(self.modules_in_group):
                self.randomizeSolarModuleParameters(self.country)
                eq_group.addSolarModule(self.module_power_efficiency * (1 + self.albedo_error), self.module_price, self.module_mttf, self.module_mttr, self.module_power, self.module_nominal_power, self.degradation_yearly)

    def addACTransmission(self):
        """Add transformer and connection grid to plant."""
        actransmission_group = self.plant.addACGroup()  # adds new group for that kind of equipment
        actransmission_group.addConnectionGrid(self.grid_power_efficiency, self.grid_price, self.grid_mttf, self.grid_mttr)
        if self.transformer_present:
            actransmission_group.addTransformer(self.transformer_power_efficiency, self.transformer_price, self.transformer_mttf, self.transformer_mttr)  # add transformer

    def getInvestmentCost(self):
        """Returns investment costs of all plant."""
        return self.plant.getInvestmentCost()

    def getRepairCostsModules(self):
        repair_costs = OrderedDict([(day, 0) for day in self.all_project_dates])
        for g in self.plant.solar_groups:
            for sm in g.solar_modules:
                for (fail, rep) in sm.failure_intervals:
                    self.randomizeRepairCosts(self.country)
                    repair_costs[rep] += self.module_repair_costs
                    if rep - self.first_day_construction > timedelta(days=365*self.module_guarantee_length): # not in guarantee period
                         repair_costs[rep] += self.module_price
        return repair_costs

    def getRepairCostsInverters(self):
        repair_costs = OrderedDict([(day, 0) for day in self.all_project_dates])
        for g in self.plant.solar_groups:
            if g.inverter is not None:
                for (fail, rep) in g.inverter.failure_intervals:
                    self.randomizeRepairCosts(self.country)
                    repair_costs[rep] += self.inverter_repair_costs
                    if rep - self.first_day_construction > timedelta(days=365*self.inverter_guarantee_length): # not in guarantee period
                       repair_costs[rep] += self.inverter_price
        return repair_costs

    def getAverageDegradationRate(self):
        """Return average yearly degradation rate over all modules."""
        degradation_rates = []
        for g in self.plant.solar_groups:
            for sm in g.solar_modules:
                degradation_rates.append(sm.degradation_yearly)
        return numpy.average(degradation_rates)

    def getAveragePowerRatio(self):
        """Calculates the average ratio between module_power and module_nominal_power."""
        module_powers = []
        for g in self.plant.solar_groups:
            for sm in g.solar_modules:
                module_powers.append(sm.power)
        avg_module_power = numpy.average(module_powers)
        return avg_module_power / self.module_nominal_power

    def equipmentDescription(self):
        """Returns string with description of equipment."""
        return str(self.plant)

    def generateElectricityProductionLifeTimeUsingInsolation(self):
        """Generates electricity production for whole project lifetime."""
        last_day_construction = self.last_day_construction
        insolations = self.energy_module.insolations
        # electricity_production - dict with ideal electricity_production for every date
        electricity_production = OrderedDict(
            (day, self.plant.getElectricityProductionPlant1DayUsingInsolation(insol, daysBetween(self.start_date_project, day))
                if day > last_day_construction else 0) for day, insol in insolations.items())

        return electricity_production

    def generateElectricityProductionLifeTime(self):
        """Returns dict with electricity_production for every date of project lifetime."""
        return OrderedDict(
            (day, self.plant.getElectricityProduction1Day(day) if day >= self.first_day_production else 0)
            for day in self.all_project_dates)
