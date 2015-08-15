#!/usr/bin/env python
# -*- coding utf-8 -*-

import numpy
from em import EnergyModule
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
        self.calcTotalNominalPower()  #calculates Total Nominal Power
        self.getInvestmentCost()  #calc investment costs of all plant + documentation

    def calcTotalNominalPower(self):
        """Calculates total power for whole plant"""
        self.total_nominal_power = self.wind_turbines_number * self.turbine_nominal_power

    def assembleSystem(self):
        """Creates the entire equipment hierarchy:
        creates plant, adds wind turbines and grid connection."""
        self.plant = PlantEquipment(self.start_date_project,
                                    self.end_date_project,
                                    energy_module=self.energy_module)  # new class Plant

        self.turbine_power_efficiency *= (1 + self.modelling_error) # correct module efficiency
        for i in range(self.wind_turbines_number):
            self.randomizeTurbineParameters(self.country)
            self.plant.addWindTurbine(self.turbine_power_efficiency * (1 + self.albedo_error), self.turbine_price, self.turbine_mtbf, self.turbine_mttr, self.turbine_power, self.turbine_nominal_power, self.degradation_yearly)

        self.plant.addConnectionGrid(self.grid_power_efficiency, self.grid_price, self.grid_mtbf, self.grid_mttr)

    def getInvestmentCost(self):
        """Returns investment costs of all plant."""
        return  self.plant.getInvestmentCost() + self.documentation_price

    def getAverageDegradationRate(self):
        """Return average yearly degradation rate over all modules."""
        degradation_rates = []
        for wt in self.plant.wind_turbines:
            degradation_rates.append(wt.degradation_yearly)
        return numpy.average(degradation_rates)

    def getAveragePowerRatio(self):
        """Calculates the average ratio between module_power and module_nominal_power."""
        turbine_powers = []
        for wt in self.plant.wind_turbines:
            turbine_powers.append(wt.power)
        avg_turbine_power = numpy.average(turbine_powers)
        return avg_turbine_power / self.turbine_nominal_power

    def equipmentDescription(self):
        """Returns string with description of equipment."""
        return str(self.plant)

    def generateElectricityProductionLifeTime(self):
        """Returns dict with electricity_production for every date of project lifetime."""
        return OrderedDict(
            (day, self.plant.getElectricityProduction1Day(day) if day >= self.first_day_production else 0)
            for day in self.all_project_dates)
