#!/usr/bin/env python
# -*- coding utf-8 -*-

import numpy
from em import EnergyModule
from config_readers import MainConfig, TechnologyModuleConfigReader
from base_class import BaseClassConfig
from annex import daysBetween, getResolutionStartEnd, cached_property, get_list_dates
from tm_equipment import PlantEquipment, MaintenanceSchedule
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
        """creates plant object"""
        maintenance_calculator = MaintenanceSchedule(start_production=self.first_day_production,
                                                 end_production=self.end_date_project,
                                                 mtbf_size=self.inverter_mtbf_size,
                                                 mtbf_shape=self.inverter_mtbf_shape,
                                                 mttr_size=self.inverter_mttr_size,
                                                 mttr_shape=self.inverter_mttr_shape)
        self.plant = PlantEquipment(self.network_available_probability, self.country,
                                    maintenance_calculator=maintenance_calculator,
                                    energy_module=self.energy_module)  #new class Plant

    def addSolarModulesAndInverter(self):
        """Adds solar module and inverter in each group"""
        for i in range(self.groups_number):
            eq_group = self.plant.addSolarGroup()
            eq_group.addInverter(self.inverter_price, self.inverter_power_efficiency)
            for j in range(self.modules_in_group):
                self.randomizeSolarModuleParameters(self.country)
                eq_group.addSolarModule(self.module_price, self.module_reliability, self.module_power_efficiency, self.module_power, self.degradation_yearly)

    def addACTransmission(self):
        """add transformer and connection grid to plant"""
        actransmission_group = self.plant.addACGroup()  #adds new group for that kind of equipment
        actransmission_group.addConnectionGrid(self.connection_grid_cost)
        if self.transformer_present:
            actransmission_group.addTransformer(self.transformer_price, self.transformer_reliability, self.transformer_power_efficiency)  #add transformer

    def getInvestmentCost(self):
        """return  investment costs of all plant"""
        return  self.plant.getInvestmentCost() + self.documentation_price

    def getAverageDegradationRate(self):
        """Return average yearly degradation rate over all modules."""
        degradation_rates = []
        for g in self.plant.getPlantSolarGroups():
            for sm in g.getSolarEquipment():
                degradation_rates.append(sm.degradation_yearly)
        return numpy.average(degradation_rates)

    def getAveragePowerRatio(self):
        """Calculates the average ratio between module_power and module_nominal_power."""
        module_powers = []
        for g in self.plant.getPlantSolarGroups():
            for sm in g.getSolarEquipment():
                module_powers.append(sm.power)
        avg_module_power = numpy.average(module_powers)
        return avg_module_power / self.module_nominal_power

    def equipmentDescription(self):
        """Returns string with description of eqipment"""
        description = []
        eqipment_price = self.getInvestmentCost()
        description.append("\nEquipment investment cost - Total: %s" % eqipment_price)
        description.append(str(self.plant))
        for i, group_info in enumerate(self.plant.getPlantGroups()):
            description.append("Group: %s" % (i + 1))
            description.append(str(group_info))
        return "\n".join(description)

    def printEquipmentDescription(self, ):
        """prints all equipment tree"""
        print self.equipmentDescription()

    def generateElectricityProductionLifeTimeUsingInsolation(self):
        """generates electricity production for whole project lifetime"""
        last_day_construction = self.last_day_construction
        insolations = self.energy_module.insolations
        #electricity_production - dict with ideal electricity_production for every date
        electricity_production = OrderedDict(
            (day, self.plant.getElectricityProductionPlant1DayUsingInsolation(insol, daysBetween(self.start_date_project, day))
                if day > last_day_construction else 0) for day, insol in insolations.items())

        return electricity_production

    def generateElectricityProductionLifeTime(self):
        """returns dict with electricity_production for every date of project lifetime"""
        return OrderedDict(
            (day, self.plant.getElectricityProductionPlant1Day(day) if day >= self.first_day_production else 0)
            for day in self.all_project_dates)
