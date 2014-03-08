#!/usr/bin/env python
# -*- coding utf-8 -*-

import os
import random
import datetime
import ConfigParser

import numpy

from annex import addXMonths, addXYears, getReportDates, getConfigs, floatRange, getListDates, cached_property
from config_yaml_reader import parse_yaml, get_config_value
from constants import TESTMODE


class MainConfig():
    """Module for reading configs from main config file"""

    def __init__(self, _country, _filename='main_config.ini'):
        """Reads main config file """

        _config = parse_yaml(_filename, _country)

        self.lifetime = get_config_value(_config, 'MAIN.lifetime', int)  #load values from section Main with value lifetime
        self.resolution = get_config_value(_config, 'MAIN.resolution', int)
        self.start_date = get_config_value(_config, 'MAIN.start_date', 'date')

        ######################### DELAYS ######################################
        _permit_procurement_duration = get_config_value(_config, 'DELAYS.permit_procurement_duration', int)
        _construction_duration = get_config_value(_config, 'DELAYS.construction_duration', int)

        if TESTMODE:  #In case testmode sets permit and construction duration fixed
            self.real_permit_procurement_duration = 0
            self.real_construction_duration = 0
        else:  #In case real mode sets permit and construction duration RANDOM from user range
            self.real_permit_procurement_duration = _permit_procurement_duration
            self.real_construction_duration = _construction_duration

        #calculates last day of construction by adding real_construction_duration + real_permit_procurement_duration to start date
        self.last_day_construction = addXMonths(self.start_date, self.real_permit_procurement_duration + self.real_construction_duration)
        self.last_day_permit_procurement = addXMonths(self.start_date, self.real_permit_procurement_duration)  #calculates last day of permit
        self.end_date = addXYears(self.start_date, self.lifetime)
        self.report_dates, self.report_dates_y = getReportDates(self.start_date, self.end_date)  #dict with Monthly report dates

        self.simulation_number = get_config_value(_config, 'SIMULATION.simulation_number', int)
        self.configs = getConfigs(self.__dict__)

    def getStartDate(self):
        return self.start_date

    def getEndDate(self):
        return self.end_date

    def getPermitProcurementDuration(self):
        return self.real_permit_procurement_duration

    def getConstructionDuration(self):
        return self.real_construction_duration

    def getLastDayPermitProcurement(self):
        return self.last_day_permit_procurement

    def getFirstDayConstruction(self):
        return self.last_day_permit_procurement + datetime.timedelta(days=1)

    def getLastDayConstruction(self):
        return self.last_day_construction

    def getResolution(self):
        return self.resolution

    def getLifeTime(self):
        return self.lifetime

    def getReportDates(self):
        return self.report_dates

    def getReportDatesY(self):
        return self.report_dates_y

    def getAllDates(self):
        return getListDates(self.getStartDate(), self.getEndDate())  #return list of ALL dates within start and end dates

    def getConfigsValues(self):
        """return  dict with config names and values
        return  Config values from file + some random generated
        """
        return self.configs

    @cached_property
    def weather_data_rnd_simulation(self):
        """return  random number which weather simulation will be used
        calculated only 1 time
        if test mode return fixed 1st simulation
        """
        if TESTMODE:
            return 1
        else:
            return random.randint(1, 100)


    @cached_property
    def electricity_price_rnd_simulation(self):
        """return  random number which electricity simulation will be used
        calculated only 1 time
        if test mode return fixed 1st simulation
        """
        if TESTMODE:
            return 1
        else:
            return random.randint(1, 100)


class SubsidyModuleConfigReader():
    """Module for reading Subsidy configs from file"""

    def __init__(self, _country, last_day_construction, _filename='sm_config.ini'):
        """Reads module config file"""
        _config = parse_yaml(_filename, _country) #loads config to memory

        self.kWh_subsidy = get_config_value(_config, 'SUBSIDY.kWh_subsidy', float)
        self.subsidy_duration = get_config_value(_config, 'SUBSIDY.subsidy_duration', int)
        _subsidy_delay = get_config_value(_config, 'SUBSIDY.subsidy_delay', float)  #reciving values from config
        self.subsidy_delay = _subsidy_delay if not TESTMODE else 0

        #calculate first day of subside by adding subsidy_delay to last_day_construction+1
        self.first_day_subsidy = addXMonths(last_day_construction + datetime.timedelta(days=1), self.subsidy_delay)
        self.last_day_subsidy = addXMonths(self.first_day_subsidy, self.subsidy_duration)

        self.configs = getConfigs(self.__dict__)  #load all configs started not with _ to dict

    def getConfigsValues(self):
        return self.configs


class TechnologyModuleConfigReader():
    """Module fore reading Technology configs from file"""

    def __init__(self, _country, _filename='tm_config.ini'):

        _config = parse_yaml(_filename, _country)  #loads config to memory

        ######################## BASE ###################
        self.groups_number = get_config_value(_config, 'EQUIPMENT.groups_number', int)
        self.modules_in_group = get_config_value(_config, 'EQUIPMENT.modules_in_group', int)
        self.transformer_present = get_config_value(_config, 'EQUIPMENT.transformer_present', bool)
        self.network_available_probability = get_config_value(_config, 'NETWORK.network_available_probability', 'float_percent')
        self.degradation_yearly = get_config_value(_config, 'SOLAR_MODULE.PV_degradation_rate', 'float_percent')
        self.module_power = get_config_value(_config, 'SOLAR_MODULE.module_power', float)

        ######################## PRICE ###################
        self.module_price = get_config_value(_config, 'SOLAR_MODULE.module_price', float)
        self.inverter_price = get_config_value(_config, 'INVERTER.inverter_price', float)
        self.transformer_price = get_config_value(_config, 'TRANSFORMER.transformer_price', float)
        self.documentation_price = get_config_value(_config, 'ADDITIONAL_PRICE.documentation_price', float)
        self.connection_grip_cost = get_config_value(_config, 'ADDITIONAL_PRICE.connection_grip_cost', float)

        ####################### RELIABILTY ####################
        self.module_reliability = get_config_value(_config, 'SOLAR_MODULE.module_reliability', 'float_percent')
        self.inverter_reliability = get_config_value(_config, 'INVERTER.inverter_reliability', 'float_percent')
        self.transformer_reliability = get_config_value(_config, 'TRANSFORMER.transformer_reliability', 'float_percent')

        ####################### EFFICIENCY ####################
        self.module_power_efficiency = get_config_value(_config, 'SOLAR_MODULE.module_power_efficiency', 'float_percent')
        self.inverter_power_efficiency = get_config_value(_config, 'INVERTER.inverter_power_efficiency', 'float_percent')
        self.transformer_power_efficiency = get_config_value(_config, 'TRANSFORMER.transformer_power_efficiency', 'float_percent')

        self.configs = getConfigs(self.__dict__)  #load all configs started not with _ to dict

    def getConfigsValues(self):
        return self.configs


class EconomicModuleConfigReader():
    """Module for reading Economic configs from file"""

    def __init__(self, _country, start_date_project, _filename='ecm_config.ini'):
        """Reads module config file
        @self.insuranceLastDayEquipment - last day when we need to pay for insurance
        """

        _config = parse_yaml(_filename, _country)

        self.tax_rate = get_config_value(_config, 'TAXES.tax_rate', 'float_percent')
        self.administrativeCosts = get_config_value(_config, 'COSTS.administrativeCosts')
        self.administrativeCostsGrowth_rate = get_config_value(_config, 'COSTS.administrativeCostsGrowth_rate', 'float_percent')
        self.insuranceFeeEquipment = get_config_value(_config, 'COSTS.insuranceFeeEquipment', 'float_percent')
        self.insuranceDurationEquipment = get_config_value(_config, 'COSTS.insuranceDurationEquipment', float)

        #calculate last day of Insuarence by adding insuranceDurationEquipment to start project date
        self.insuranceLastDayEquipment = addXYears(start_date_project, self.insuranceDurationEquipment)

        self.developmentCostDuringPermitProcurement = get_config_value(_config, 'COSTS.developmentCostDuringPermitProcurement')
        self.developmentCostDuringConstruction = get_config_value(_config, 'COSTS.developmentCostDuringConstruction')

        self.market_price = get_config_value(_config, 'ELECTRICITY.market_price', float)
        self.price_growth_rate = get_config_value(_config, 'ELECTRICITY.growth_rate', 'float_percent')

        ######################### INVESTMENTS #############################################

        self.cost_capital = get_config_value(_config, 'INVESTMENTS.cost_capital', 'float_percent')
        self.initial_paid_in_capital = get_config_value(_config, 'INVESTMENTS.initial_paid_in_capital', float)

        ######################### DEBT ########################################

        self.debt_share = get_config_value(_config, 'DEBT.debt_share', 'float_percent')
        self.debt_rate = get_config_value(_config, 'DEBT.interest_rate', 'float_percent')
        self.debt_rate_short = get_config_value(_config, 'DEBT.interest_rate_short', 'float_percent')
        self.debt_years = get_config_value(_config, 'DEBT.periods', int)

        ######################### DEPRICATION #################################
        #gets deprication_duration and convert it to months
        self.debt_years = 12 * get_config_value(_config, 'AMORTIZATION.duration', float)

        ######################### ElectricityMarketPriceSimulation ############
        # loading varibales needed to ElectricityMarketPriceSimulation

        self.S0 = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.S0', float)
        self.dt = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.dt', float)
        self.Lambda = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.Lambda', float)
        self.y = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.y', float)
        self.delta_q = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.delta_q', float)
        self.theta = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.theta', float)
        self.k = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.k', float)
        self.sigma = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.sigma', float)

        self.configs = getConfigs(self.__dict__)  #load all configs started not with _ to dict

    def getConfigsValues(self):
        return self.configs


class EnergyModuleConfigReader():
    """Module fore reading Energy configs from file"""

    def __init__(self, _country, _filename='em_config.ini'):

        _config = parse_yaml(_filename, _country)

        #mean value for distribution of random factor for generating temperature
        self.mean = get_config_value(_config, 'NORMAL_DISTRIBUTION.mean', float)

        #stdev value for distribution of random factor for generating temperature
        self.stdev = self.mean * get_config_value(_config, 'NORMAL_DISTRIBUTION.stdev_percent', 'float_percent')

        self.TMin = get_config_value(_config, 'WEATHER_SIMULATION.TMin', float)
        self.TMax = get_config_value(_config, 'WEATHER_SIMULATION.TMin', float)

        self.configs = getConfigs(self.__dict__)  #load all configs started not with _ to dict

    def getConfigsValues(self):
        return self.configs


class RiskModuleConfigReader():
    """Module fore reading Risk configs from file"""

    def __init__(self, _filename='rm_config.ini'):
        _config = ConfigParser.ConfigParser()
        _filepath = os.path.join(os.getcwd(), 'configs', _filename)
        _config.read(_filepath)

        self.riskFreeRate = _config.getfloat('RISK', 'riskFreeRate')
        self.benchmarkSharpeRatio = _config.getfloat('RISK', 'benchmarkSharpeRatio')
        self.benchmarkModifiedSharpeRatio = _config.getfloat('RISK', 'benchmarkModifiedSharpeRatio')

        self.configs = getConfigs(self.__dict__)  #load all configs started not with _ to dict

    def getConfigsValues(self):
        return self.configs


class EmInputsReader():
    """Module for reading Inputs for Energy Module"""

    def __init__(self):
        """Loads inputs to memory"""
        filepath = os.path.join(os.getcwd(), 'inputs', 'em_input.txt')  #finds file path to inputs
        self.inputs = numpy.genfromtxt(filepath, dtype=None, delimiter=';', names=True)  #reads file content to memory
        self.inputs_insolations = [i[1] for i in self.inputs]  #gets values insolations to list
        self.inputs_temperature = [i[2] for i in self.inputs]  #get values - temperature to list where list_id - month_no-1

    def getAvMonthInsolationMonth(self, month):
        """Returns average daily insolation in given date"""
        return self.inputs_insolations[month]

    def getAvMonthTemperatureMonth(self, month):
        """Returns average daily insolation in given date"""
        return self.inputs_temperature[month]


if __name__ == '__main__':
    m = MainConfig()
    print m.getConfigsValues()

    ecm = EconomicModuleConfigReader(datetime.date(2000, 1, 1))
    print ecm.getConfigsValues()

    print parse_list_and_get_random('1')
    print parse_list_and_get_random('1,11')
    print parse_list_and_get_random('1,11,0.5', value_type=float)
    print parse_list_and_get_random('1,11,0.01', value_type=float)







