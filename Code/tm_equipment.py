#!/usr/bin/env python
# -*- coding utf-8 -*-

import random
import numpy
from annex import lastDayMonth, memoized, daysBetween, OrderedDefaultdict
from collections import defaultdict
from datetime import date, timedelta

class EQ:
    """Enum class to hold equipment types."""
    GRID_CONNECTION = 'solar module'
    WIND_TURBINE = 'wind turbine'

class Equipment:
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

        self.generateFailureIntervals()

    def __str__(self):
        return ("""\
                Type: {eqtype}
                Price: {price}
                Effiency: {efficiency}
                MTBF: {mtbf}
                MTTR: {mttr}""".format(**self.__dict__))

    def getInvestmentCost(self):
        """Return investment cost (price) of equipment."""
        return self.price

    def isWorking(self, day):
        """Returns True is this equpment piece is working on the @day,
        checks if it is not contained in any of the failure intervals."""
        return not any(f <= day < r for f, r in self.failure_intervals)

    def getFailureDate(self, day_of_repair):
        """Returns next failure date from @day_of_repair."""
        return day_of_repair + timedelta(days=int(random.expovariate(1.0 / self.mtbf)) + 1)

    def getRepairDate(self, day_of_failure):
        """Returns repair date from @day_of_failure."""
        return day_of_failure + timedelta(days=int(random.expovariate(1.0 / self.mttr)) + 1)

    def generateFailureIntervals(self):
        """Generates list of [failure, repair) intervals till the end of project."""
        failure_date = self.getFailureDate(self.start_date)
        repair_date = self.getRepairDate(failure_date)
        self.failure_intervals = [(failure_date, repair_date)]
        while self.failure_intervals[-1][1] < self.end_date:
            failure_date = self.getFailureDate(self.failure_intervals[-1][1])
            repair_date = self.getRepairDate(failure_date)
            self.failure_intervals.append((failure_date, repair_date))

class EquipmentWindTurbine(Equipment):
    """Class for holding special info about Solar Modules."""

    def __init__(self, efficiency, price, mtbf, mttr, start_date, end_date, power, nominal_power, degradation_yearly):
        """Additional attributes are:
            @power - module power
            @nominal_power - module nominal power
            @degradation_yearly - yearly degradation_coefficient"""
        Equipment.__init__(self, EQ.WIND_TURBINE, efficiency, price, mtbf, mttr, start_date, end_date)
        self.power = power
        self.nominal_power = nominal_power
        self.degradation_yearly = degradation_yearly

    def getElectricityProduction(self, avg_production_day_per_kW, day):
        """Gets electiricity production for SolarModule."""
        if self.isWorking(day):
            return avg_production_day_per_kW * self.power * self.efficiency * self.conservation_coefficient(day)
        return 0

    def conservation_coefficient(self, day):
        """Calculation of degradation coefficients for equipment depending years running.
           If degradation is so large that the production would be negative then it returns zero."""
        return max(0, 1 - daysBetween(self.start_date, day) * (self.degradation_yearly / 365.0))

    def __str__(self):
        """Returns string representation of a solar module."""
        return ("""\
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

######################### PLANT #######################

class PlantEquipment():
    """Class for whole plant equipment."""

    def __init__(self, start_date, end_date, energy_module):
        self.wind_turbines = []  # list of all solar groups
        self.grid_connection = None
        self.energy_module = energy_module
        self.start_date = start_date
        self.end_date = end_date

    def addConnectionGrid(self, efficiency, price, mtbf, mttr):
        """Adds connection grid. Can be only ONE."""
        assert self.grid_connection is None, "Cannot add a second connection grid."
        self.grid_connection = EquipmentConnectionGrid(efficiency, price, mtbf, mttr, self.start_date, self.end_date)  # create Equipment class instance

    def addWindTurbine(self, efficiency, price, mtbf, mttr, power, nominal_power, degradation_yearly):
        wt = EquipmentWindTurbine(efficiency, price, mtbf, mttr, self.start_date, self.end_date, power, nominal_power, degradation_yearly)
        self.wind_turbines.append(wt)

    def getInvestmentCost(self):
        """Return investment costs of the whole plant."""
        wind_trubine_cost = sum([w.getInvestmentCost() for w in self.wind_turbines])
        return wind_trubine_cost + self.getGridInvestmentCost()

    def getElectricityProduction1Day(self, day):
        """Returns electricity production for whole plant."""
        if self.isGridAvailable(day):
            avg_production_day_per_kW = self.energy_module.getAvgProductionDayPerKW(day)
            production = sum(w.getElectricityProduction(avg_production_day_per_kW, day)
                    for w in self.wind_turbines)
            grid_connection_eff = self.grid_connection.efficiency
            return production * grid_connection_eff
        return 0

    def getPlantPower(self):
        """Returns total power of the plant."""
        return sum([w.power for w in self.wind_turbines])

    def isGridAvailable(self, day):
        """Returns True if we have access to the grid else False."""
        if self.grid_connection is None: return False
        return self.grid_connection.isWorking(day)

    def getGridInvestmentCost(self):
        """Returns True if we have access to the grid else False."""
        if self.grid_connection is None: return 0
        return self.grid_connection.getInvestmentCost()

    def __str__(self):
        """String representation of Plant object."""
        s = """
        PLANT:
            total investment cost: {0}
            total power: {1}
            start production date: {start_date}
            end production date: {end_date}
            """.format(self.getInvestmentCost(), self.getPlantPower(), **self.__dict__)
        s += "\n            WIND TURBINES: ({0}):\n".format(len(self.wind_turbines))
        for i, wt in enumerate(self.wind_turbines):
            s += """
            Wind turbine {0}:
            """.format(i+1)
            s += str(wt)
        s += """\n
            Grid connection:\n"""
        s += str(self.grid_connection)
        return s
