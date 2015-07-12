#!/usr/bin/env python
# -*- coding utf-8 -*-

import numpy
from em import EnergyModule
from config_readers import MainConfig, TechnologyModuleConfigReader
from base_class import BaseClassConfig
from annex import yearsBetween1Jan, getResolutionStartEnd, cached_property, get_list_dates
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
        """creates plant object"""
        self.plant = PlantEquipment(self.network_available_probability, self.country)  #new class Plant

    def addSolarModulesAndInverter(self):
        """Adds solar module and inverter in each group"""
        for i in range(self.groups_number):
            eq_group = self.plant.addSolarGroup()
            eq_group.addInverter(self.inverter_price, self.inverter_reliability, self.inverter_power_efficiency)
            for j in range(self.modules_in_group):
                eq_group.addSolarModule(self.module_price, self.module_reliability, self.module_power_efficiency, self.module_power)

    def addACTransmission(self):
        """add transformer and connection grid to plant"""
        actransmission_group = self.plant.addACGroup()  #adds new group for that kind of equipment
        actransmission_group.addConnectionGrid(self.connection_grid_cost)
        if self.transformer_present:
            actransmission_group.addTransformer(self.transformer_price, self.transformer_reliability, self.transformer_power_efficiency)  #add transformer

    def getInvestmentCost(self):
        """return  investment costs of all plant"""
        return  self.plant.getInvestmentCost() + self.documentation_price

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

    @cached_property
    def conservation_coefficients(self):  #conservation as the opposite of degradation
        """calculation of degradation coefficients for equipment"""
        start_date = self.start_date_project
        koef_degradation = 1-self.degradation_yearly
        return  OrderedDict((date, koef_degradation ** yearsBetween1Jan(start_date, date)) for date in self.all_project_dates)

    def conservationAtDate(self, date):
        """return degradation coefficient at given @date"""
        return  self.conservation_coefficients[date]

    def generateElectiricityProduction(self, date):
        """generates electricity production at given @date"""
        insolation = self.energy_module.getInsolation(date)
        conservation = self.conservationAtDate(date)
        production = self.plant.getElectricityProductionPlant1Day(insolation)
        return  production * conservation

    def getElectricityProduction(self, date_start, date_end):
        """return sum of electricity in kWh for each day for the selected period"""
        s = self.plant.getElectricityProductionPlant1Day
        i = self.energy_module.insolations
        d = self.conservation_coefficients
        return sum([s(1)*i[date]*d[date] for date in get_list_dates(date_start, date_end)])

    def generateElectricityProductionLifeTime(self):
        """generates electricity production for whole project lifetime"""
        last_day_construction = self.last_day_construction
        insolations = self.energy_module.insolations
        #electricity_production - dict with ideal electricity_production for every date
        electricity_production = OrderedDict((day, self.plant.getElectricityProductionPlant1Day(insol) if day > last_day_construction else 0) for day, insol in insolations.items())
        #multiply each electricity_production at degradation coeff
        electricity_production.update((x, electricity_production[x]*y) for x, y in self.conservation_coefficients.items())

        return electricity_production
