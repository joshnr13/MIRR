#!/usr/bin/env python
# -*- coding utf-8 -*-

import os
import random
import datetime
import ConfigParser
from annex import addXMonths, addXYears, getReportDates, getConfigs, floatRange, getListDates, cached_property
from constants import TESTMODE
import numpy

class MainConfig():
    """Module for reading configs from main config file"""

    def __init__(self, _filename='main_config.ini'):
        """Reads main config file """

        _config = ConfigParser.ConfigParser()
        _filepath = os.path.join(os.getcwd(), 'configs', _filename)
        _config.read(_filepath)

        self.lifetime = _config.getint('Main', 'lifetime')
        self.resolution = _config.getint('Main', 'resolution')
        self.start_date = datetime.datetime.strptime(_config.get('Main', 'start_date'), '%Y/%m/%d').date()

        ######################### DELAYS ######################################
        _permit_procurement_duration_lower_limit = _config.getfloat('Delays', 'permit_procurement_duration_lower_limit')
        _permit_procurement_duration_upper_limit = _config.getfloat('Delays', 'permit_procurement_duration_upper_limit')
        _construction_duration_lower_limit = _config.getfloat('Delays', 'construction_duration_lower_limit')
        _construction_duration_upper_limit = _config.getfloat('Delays', 'construction_duration_upper_limit')

        if TESTMODE:
            self.real_permit_procurement_duration = 0
            self.real_construction_duration = 0
        else :
            self.real_permit_procurement_duration = random.randrange(_permit_procurement_duration_lower_limit, _permit_procurement_duration_upper_limit+1)
            self.real_construction_duration = random.randrange(_construction_duration_lower_limit, _construction_duration_upper_limit+1)

        self.last_day_construction = addXMonths(self.start_date, self.real_permit_procurement_duration+self.real_construction_duration)
        self.last_day_permit_procurement = addXMonths(self.start_date, self.real_permit_procurement_duration)
        self.end_date = addXYears(self.start_date, self.lifetime)
        self.report_dates, self.report_dates_y = getReportDates(self.start_date, self.end_date)

        self.simulation_number = _config.getint('Simulation', 'simulation_number')
        self.configs = getConfigs(self.__dict__)

    def getStartDate(self):
        return self.start_date

    def getEndDate(self):
        return self.end_date

    def getPermitProcurementDuration(self):
        return  self.real_permit_procurement_duration

    def getConstructionDuration(self):
        return  self.real_construction_duration

    def getLastDayPermitProcurement(self):
        return  self.last_day_permit_procurement

    def getFirstDayConstruction(self):
        return  self.last_day_permit_procurement + datetime.timedelta(days=1)

    def getLastDayConstruction(self):
        return  self.last_day_construction

    def getResolution(self):
        return  self.resolution

    def getLifeTime(self):
        return  self.lifetime

    def getReportDates(self):
        return self.report_dates

    def getReportDatesY(self):
        return self.report_dates_y

    def getAllDates(self):
        return  getListDates(self.getStartDate(), self.getEndDate())

    def getConfigsValues(self):
        """return  dict with config names and values
        return  Config values from file + some random generated
        """
        return self.configs

    @cached_property
    def weather_data_rnd_simulation(self):
        """return  random number which weather simulation will be used
        calculated only 1 time """
        return random.randint(1, 100)

    @cached_property
    def electricity_price_rnd_simulation(self):
        """return  random number which electricity simulation will be used
        calculated only 1 time
        """
        return random.randint(1, 100)

    def getConfigsValues(self):
        return  self.configs

class SubsidyModuleConfigReader():
    """Module for reading Subsidy configs from file"""
    def __init__(self, _filename='sm_config.ini'):
        """Reads module config file"""
        _config = ConfigParser.ConfigParser()
        _filepath = os.path.join(os.getcwd(), 'configs', _filename)
        _config.read(_filepath)

        _subsidy_delay_lower_limit = _config.getfloat('Subsidy', 'subsidy_delay_lower_limit')
        _subsidy_delay_upper_limit = _config.getfloat('Subsidy', 'subsidy_delay_upper_limit')

        _kWh_subsidy_lower_limit = _config.getfloat('Subsidy', 'kWh_subsidy_lower_limit')
        _kWh_subsidy_upper_limit = _config.getfloat('Subsidy', 'kWh_subsidy_upper_limit')
        _subsidy_duration_upper_limit = _config.getfloat('Subsidy', 'subsidy_duration_upper_limit')
        _subsidy_duration_lower_limit = _config.getfloat('Subsidy', 'subsidy_duration_lower_limit')

        if TESTMODE:
            self.subsidy_delay = 0
            self.kWh_subsidy = (_kWh_subsidy_lower_limit + _kWh_subsidy_upper_limit) / 2.0
            self.subsidy_duration = (_subsidy_duration_upper_limit + _subsidy_duration_lower_limit) / 2.0
        else:
            self.subsidy_delay = random.randint(_subsidy_delay_lower_limit, _subsidy_delay_upper_limit)
            self.kWh_subsidy = random.choice(floatRange(_kWh_subsidy_lower_limit ,_kWh_subsidy_upper_limit, 0.001, True))
            self.subsidy_duration = random.randint(_subsidy_duration_lower_limit, _subsidy_duration_upper_limit )

        self.first_day_subsidy = addXMonths(self.last_day_construction+datetime.timedelta(days=1), self.subsidy_delay)
        self.last_day_subsidy = addXMonths(self.first_day_subsidy, self.subsidy_duration)

        self.configs = getConfigs(self.__dict__)

    def getConfigsValues(self):
        return  self.configs



class TechnologyModuleConfigReader():
    """Module fore reading Technology configs from file"""
    def __init__(self, _filename='tm_config.ini'):
        _config = ConfigParser.ConfigParser()
        _filepath = os.path.join(os.getcwd(), 'configs', _filename)
        _config.read(_filepath)

        ######################## BASE ###################
        self.groups_number = _config.getint('Equipment', 'groups_number')
        self.modules_in_group = _config.getint('Equipment', 'modules_in_group')
        self.transformer_present = _config.getboolean('Equipment', 'transformer_present')
        self.network_available_probability = _config.getfloat('Network', 'network_available_probability') / 100
        self.degradation_yearly = _config.getfloat('SolarModule', 'PV_degradation_rate') / 100
        self.module_power = _config.getfloat('SolarModule', 'module_power')

        ######################## PRICE ###################
        self.module_price = _config.getfloat('SolarModule', 'module_price')
        self.inverter_price = _config.getfloat('Inverter', 'inverter_price')
        self.transformer_price = _config.getfloat('Transformer', 'transformer_price')

        self.documentation_price = _config.getfloat('AdditionalPrice', 'documentation_price')
        self.connection_grip_cost = _config.getfloat('AdditionalPrice', 'connection_grip_cost')

        ####################### RELIABILTY ####################
        self.module_reliability = _config.getfloat('SolarModule', 'module_reliability') / 100
        self.inverter_reliability = _config.getfloat('Inverter', 'inverter_reliability') / 100
        self.transformer_reliability = _config.getfloat('Transformer', 'transformer_reliability') / 100

        ####################### EFFICIENCY ####################
        self.module_power_efficiency = _config.getfloat('SolarModule', 'module_power_efficiency') / 100
        self.inverter_power_efficiency = _config.getfloat('Inverter', 'inverter_power_efficiency') / 100
        self.transformer_power_efficiency = _config.getfloat('Transformer', 'transformer_power_efficiency') / 100

        self.configs = getConfigs(self.__dict__)

    def getConfigsValues(self):
        return  self.configs


class EconomicModuleConfigReader():
    """Module for reading Economic configs from file"""
    def __init__(self, start_date_project, _filename='ecm_config.ini'):
        """Reads module config file
        @self.insuranceLastDayEquipment - last day when we need to pay for insurance
        """
        _config = ConfigParser.ConfigParser()
        _filepath = os.path.join(os.getcwd(), 'configs', _filename)
        _config.read(_filepath)

        self.tax_rate = _config.getfloat('Taxes', 'tax_rate') / 100
        self.administrativeCosts = _config.getfloat('Costs', 'administrativeCosts')
        self.administrativeCostsGrowth_rate = _config.getfloat('Costs', 'administrativeCostsGrowth_rate') / 100
        self.insuranceFeeEquipment = _config.getfloat('Costs', 'insuranceFeeEquipment') / 100
        self.insuranceDurationEquipment = _config.getfloat('Costs', 'insuranceDurationEquipment')

        self.insuranceLastDayEquipment = addXYears(start_date_project, self.insuranceDurationEquipment)

        self.developmentCostDuringPermitProcurement = _config.getfloat('Costs', 'developmentCostDuringPermitProcurement')
        self.developmentCostDuringConstruction = _config.getfloat('Costs', 'developmentCostDuringConstruction')

        self.market_price = _config.getfloat('Electricity', 'market_price')
        self.price_groth_rate = _config.getfloat('Electricity', 'growth_rate') / 100

        ######################### INVESTMENTS #############################################

        self.cost_capital = _config.getfloat('Investments', 'cost_capital') / 100
        self.initial_paid_in_capital = _config.getfloat('Investments', 'initial_paid_in_capital')

        #self.investments = _config.getfloat('Investments', 'investment_value')
        #self.investmentEquipment = _config.getfloat('Investments', 'investmentEquipment')

        ######################### DEBT ########################################

        self.debt_share = _config.getfloat('Debt', 'debt_share') / 100
        self.debt_rate = _config.getfloat('Debt', 'interest_rate') / 100
        self.debt_rate_short = _config.getfloat('Debt', 'interest_rate_short') / 100
        self.debt_years = _config.getint('Debt', 'periods')

        ######################### DEPRICATION #################################

        self.deprication_duration = _config.getfloat('Amortization', 'duration')

        ######################### ElectricityMarketPriceSimulation ############

        self.S0 = _config.getfloat('ElectricityMarketPriceSimulation', 'S0')
        self.dt =  _config.getfloat('ElectricityMarketPriceSimulation', 'dt')
        self.Lambda = _config.getfloat('ElectricityMarketPriceSimulation', 'Lambda')
        self.y = _config.getfloat('ElectricityMarketPriceSimulation', 'y')
        self.delta_q = _config.getfloat('ElectricityMarketPriceSimulation', 'delta_q')
        self.theta = _config.getfloat('ElectricityMarketPriceSimulation', 'theta')
        self.k = _config.getfloat('ElectricityMarketPriceSimulation', 'k')
        self.sigma = _config.getfloat('ElectricityMarketPriceSimulation', 'sigma')

        self.configs = getConfigs(self.__dict__)

    def getConfigsValues(self):
        return  self.configs


class EnergyModuleConfigReader():
    """Module fore reading Energy configs from file"""
    def __init__(self, _filename='em_config.ini'):
        _config = ConfigParser.ConfigParser()
        _filepath = os.path.join(os.getcwd(), 'configs', _filename)
        _config.read(_filepath)

        self.mean = _config.getfloat('NormalDistribution', 'mean')  #mean value for distribution of random factor for generating temperature
        self.stdev = _config.getfloat('NormalDistribution', 'stdev_percent') * self.mean / 100 #stdev value for distribution of random factor for generating temperature
        self.TMin = _config.getfloat('WeatherSimulation', 'TMin')
        self.TMax = _config.getfloat('WeatherSimulation', 'TMax')

        self.configs = getConfigs(self.__dict__)

    def getConfigsValues(self):
        return  self.configs

class RiskModuleConfigReader():
    """Module fore reading Risk configs from file"""
    def __init__(self, _filename='rm_config.ini'):
        _config = ConfigParser.ConfigParser()
        _filepath = os.path.join(os.getcwd(), 'configs', _filename)
        _config.read(_filepath)

        self.riskFreeRate = _config.getfloat('RISK', 'riskFreeRate')
        self.benchmarkSharpeRatio = _config.getfloat('RISK', 'benchmarkSharpeRatio')
        self.benchmarkModifiedSharpeRatio = _config.getfloat('RISK', 'benchmarkModifiedSharpeRatio')

        self.configs = getConfigs(self.__dict__)

    def getConfigsValues(self):
        return  self.configs


class EmInputsReader():
    """Module for reading Inputs for Energy Module"""
    def __init__(self):
        """Loads inputs to memory"""
        filepath = os.path.join(os.getcwd(), 'inputs', 'em_input.txt')
        self.inputs = numpy.genfromtxt(filepath, dtype=None, delimiter=';',  names=True)
        self.inputs_insolations = [i[1] for i in self.inputs]
        self.inputs_temperature = [i[2] for i in self.inputs]

    def getAvMonthInsolationMonth(self, month):
        """Returns average daily insolation in given date"""
        return self.inputs_insolations[month]

    def getAvMonthTemperatureMonth(self, month):
        """Returns average daily insolation in given date"""
        return self.inputs_temperature[month]

if __name__ == '__main__':

    m = MainConfig()
    print m.getConfigsValues()









