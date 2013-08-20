#!/usr/bin/env python
# -*- coding utf-8 -*-

from em import EnergyModule
from config_readers import MainConfig, TechnologyModuleConfigReader
from base_class import BaseClassConfig
from annex import yearsBetween1Jan, getResolutionStartEnd
from tm_equipment import PlantEquipment
from collections import OrderedDict

class TechnologyModule(BaseClassConfig, TechnologyModuleConfigReader):
    def __init__(self, config_module, energy_module):
        BaseClassConfig.__init__(self, config_module)
        TechnologyModuleConfigReader.__init__(self)
        self.energy_module = energy_module
        self.calcTotalPower()
        self.assembleSystem()
        self.getInvestmentCost()
        #self.calc_project_datelist()
        self.calcDegradationCoefficients()

    def calcTotalPower(self):
        """Calculates total power for whole plant"""
        self.total_power = self.groups_number * self.modules_in_group * self.module_power

    def assembleSystem(self):
        """generates objects for each solarmodule in plant"""
        self.buildPlant()  #create plant
        self.addSolarModulesAndInverter()  #add solar modules and inverters to plant
        self.addACTransmission()  #add transformer and connection grid to plant

    def buildPlant(self):
        """creates plant object"""
        self.plant = PlantEquipment(self.network_available_probability)

    def addSolarModulesAndInverter(self):
        """Adds solar module and inverter in each group"""
        for i in range(self.groups_number):
            eq_group = self.plant.add_Solar_group()
            eq_group.add_inverter(self.inverter_price, self.inverter_reliability, self.inverter_power_efficiency)
            for j in range(self.modules_in_group):
                eq_group.add_solar_module(self.module_price, self.module_reliability, self.module_power_efficiency, self.module_power)

    def addACTransmission(self):
        """add transformer and connection grid to plant"""
        actransmission_group = self.plant.add_AC_group()  #adds new group for that kind of equipment
        actransmission_group.add_connection_grid(self.connection_grip_cost)
        if self.transformer_present:
            actransmission_group.add_transformer(self.transformer_price, self.transformer_reliability, self.transformer_power_efficiency)  #add transformer

    def getInvestmentCost(self):
        """return  investment costs of all plant"""
        return  self.plant.getInvestmentCost() + self.documentation_price

    def equipmentDescription(self):
        """Returns string with description of eqipment"""
        description = []
        eqipment_price = self.getInvestmentCost()
        description.append("\nEquipment investment cost - Total: %s" % eqipment_price)
        description.append(str(self.plant))
        for i, group_info in enumerate(self.plant.get_groups()):
            description.append("Group: %s" % (i + 1))
            description.append(str(group_info))
        return "\n".join(description)

    def printEquipmentDescription(self, ):
        """prints all equipment tree"""
        print self.equipmentDescription()

    def calcDegradationCoefficients(self):
        """calculation of degradation coefficients for equipment"""
        degradation_coefficients = OrderedDict()
        for date in self.all_project_dates:
            degradation_coefficients[date] = (1-self.degradation_yearly)**yearsBetween1Jan(self.start_date_project, date)
        self.degradation_coefficients = degradation_coefficients

    def degradationAtDate(self, date):
        """return degradation coefficient at given @date"""
        return  self.degradation_coefficients[date]

    def generateElectiricityProduction(self, date):
        """generates electricity production at given @date"""
        insolation = self.energy_module.get_insolation(date)
        degradation = self.degradationAtDate(date)
        production = self.plant.getElectricityProductionPlant1Day(insolation)
        return  production * degradation

    def getElectricityProduction(self, date_start, date_end):
        """return sum of electricity in kWh for each day for the selected period"""
        s = self.plant.getElectricityProductionPlant1Day
        i = self.energy_module.insolations
        d = self.degradation_coefficients
        return sum([s(1)*i[date]*d[date] for date in self.all_project_dates])

    def generateElectricityProductionLifeTime(self):
        """generates electricity production for whole project lifetime"""
        dates = self.all_dates
        sun_values = numpy.array([self.plant.getElectricityProductionPlant1Day(1) if day > self.last_day_construction else 0 for day in dates ])
        insolations = self.energy_module.insolations.values()
        degrodations = numpy.array(self.degradation_coefficients.values())
        total_values = sun_values*degrodations*insolations
        dic_result = OrderedDict((date, value) for date, value in zip(dates, total_values))
        return dic_result

