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


ITERATION_NO = 0


def silent():
    if ITERATION_NO in (0, 1):
        return False
    return True


def start_iteration(iteration):
    global ITERATION_NO
    ITERATION_NO = iteration


class MainConfig():
    """Module for reading configs from main config file"""

    def __init__(self, country, _filename='main_config.ini'):
        """Reads main config file"""

        _config = parse_yaml(_filename, country, silent())

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

    def getFirstDayProduction(self):
        return self.last_day_construction + datetime.timedelta(days=1)

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
            return random.randint(1, 500)


class SubsidyModuleConfigReader():
    """Module for reading Subsidy configs from file"""

    def __init__(self, country, last_day_construction, _filename='sm_config.ini'):
        """Reads module config file"""
        _config = parse_yaml(_filename, country, silent()) #loads config to memory

        self.kWhFIT = get_config_value(_config, 'SUBSIDY.kWhFIT', float)
        self.subsidy_duration = get_config_value(_config, 'SUBSIDY.subsidy_duration', int)
        _subsidy_delay = get_config_value(_config, 'SUBSIDY.subsidy_delay', float)  #reciving values from config
        self.subsidy_delay = _subsidy_delay if not TESTMODE else 0

        #calculate first day of subsidy by adding subsidy_delay to last_day_construction+1
        self.first_day_subsidy = addXMonths(last_day_construction + datetime.timedelta(days=1),
                                            self.subsidy_delay, minus_day=False)
        self.last_day_subsidy = addXMonths(self.first_day_subsidy, self.subsidy_duration)

        self.configs = getConfigs(self.__dict__)  #load all configs started not with _ to dict

    def getConfigsValues(self):
        return self.configs


class TechnologyModuleConfigReader():
    """Module for reading Technology configs from file"""

    def __init__(self, country, _filename='tm_config.ini'):

        _config = parse_yaml(_filename, country, silent())  #loads config to memory

        ######################## BASE ###################
        self.groups_number = get_config_value(_config, 'EQUIPMENT.groups_number', int)
        self.modules_in_group = get_config_value(_config, 'EQUIPMENT.modules_in_group', int)
        self.transformer_present = get_config_value(_config, 'EQUIPMENT.transformer_present', bool)
        self.network_available_probability = get_config_value(_config, 'NETWORK.network_available_probability', 'float_percent')
        self.degradation_yearly = get_config_value(_config, 'SOLAR_MODULE.PV_degradation_rate', 'float_percent')
        self.module_power = get_config_value(_config, 'SOLAR_MODULE.module_power', float)
        self.module_nominal_power = get_config_value(_config, 'SOLAR_MODULE.module_nominal_power', float)

        ######################## PRICE ###################
        self.module_price = get_config_value(_config, 'SOLAR_MODULE.module_price', float)
        self.inverter_price = get_config_value(_config, 'INVERTER.inverter_price', float)
        self.transformer_price = get_config_value(_config, 'TRANSFORMER.transformer_price', float)
        self.documentation_price = get_config_value(_config, 'ADDITIONAL_PRICE.documentation_price', float)
        self.connection_grid_cost = get_config_value(_config, 'ADDITIONAL_PRICE.connection_grid_cost', float)

        ####################### RELIABILTY ####################
        self.module_reliability = get_config_value(_config, 'SOLAR_MODULE.module_reliability', 'float_percent')
        self.transformer_reliability = get_config_value(_config, 'TRANSFORMER.transformer_reliability', 'float_percent')

        self.inverter_mtbf = get_config_value(_config, 'INVERTER.MTBF', int)
        self.inverter_mttr = get_config_value(_config, 'INVERTER.MTTR', int)

        ####################### EFFICIENCY ####################
        self.module_power_efficiency = get_config_value(_config, 'SOLAR_MODULE.module_power_efficiency', 'float_percent')
        self.inverter_power_efficiency = get_config_value(_config, 'INVERTER.inverter_power_efficiency', 'float_percent')
        self.transformer_power_efficiency = get_config_value(_config, 'TRANSFORMER.transformer_power_efficiency', 'float_percent')

        self.configs = getConfigs(self.__dict__)  #load all configs started not with _ to dict

    def getConfigsValues(self):
        return self.configs

    def randomizeSolarModuleParameters(self, country, _filename='tm_config.ini'):
        _config = parse_yaml(_filename, country, silent())  #loads config to memory
        self.degradation_yearly = get_config_value(_config, 'SOLAR_MODULE.PV_degradation_rate', 'float_percent')
        self.module_power = get_config_value(_config, 'SOLAR_MODULE.module_power', float)


class EconomicModuleConfigReader():
    """Module for reading Economic configs from file"""

    def __init__(self, country, start_date_project, _filename='ecm_config.ini'):
        """Reads module config file
        @self.insuranceLastDayEquipment - last day when we need to pay for insurance
        """

        _config = parse_yaml(_filename, country, silent())

        self.tax_rate = get_config_value(_config, 'TAXES.tax_rate', 'float_percent')
        self.administrativeCosts = get_config_value(_config, 'COSTS.administrativeCosts')
        self.administrativeCostsGrowth_rate = get_config_value(_config, 'COSTS.administrativeCostsGrowth_rate', 'float_percent')
        self.insuranceFeeEquipment = get_config_value(_config, 'COSTS.insuranceFeeEquipment', 'float_percent')
        self.insuranceDurationEquipment = get_config_value(_config, 'COSTS.insuranceDurationEquipment', float)

        #calculate last day of Insuarence by adding insuranceDurationEquipment to start project date
        self.insuranceLastDayEquipment = addXYears(start_date_project, self.insuranceDurationEquipment)

        self.developmentCostDuringPermitProcurement = get_config_value(_config, 'COSTS.developmentCostDuringPermitProcurement')
        self.developmentCostDuringConstruction = get_config_value(_config, 'COSTS.developmentCostDuringConstruction')

        ######################### INVESTMENTS #############################################

        self.cost_capital = get_config_value(_config, 'INVESTMENTS.cost_capital', 'float_percent')
        self.initial_paid_in_capital = get_config_value(_config, 'INVESTMENTS.initial_paid_in_capital', float)

        ######################### DEBT ########################################

        self.debt_share = get_config_value(_config, 'DEBT.debt_share', 'float_percent')
        self.debt_rate = get_config_value(_config, 'DEBT.interest_rate', 'float_percent')
        self.debt_rate_short = get_config_value(_config, 'DEBT.interest_rate_short', 'float_percent')
        self.debt_years = get_config_value(_config, 'DEBT.periods', int)
        self.delay_of_principal_repayment = get_config_value(_config, 'DEBT.start_of_principal_repayment', int)

        ######################### Depreciation #################################
        #gets Depreciation_duration and convert it to months
        self.Depreciation_duration = 12 * get_config_value(_config, 'AMORTIZATION.duration', float)

        ######################### ElectricityMarketPriceSimulation ############
        # loading varibales needed to ElectricityMarketPriceSimulation

        self.S0 = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.S0', float)
        self.dt = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.dt', float)
        self.Lambda = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.Lambda', float)
        self.y = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.y', float)
        self.y_annual_mean = get_config_value(
            _config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.interannual_variability_of_y_mean', float)
        self.y_annual_std = get_config_value(
            _config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.interannual_variability_of_y_std', float)
        self.theta = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.theta', float)
        self.k = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.k', float)
        self.sigma = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.sigma', float)

        self.jump_size_average = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.jump_size_average', float)
        self.jump_size_std = get_config_value(_config, 'ELECTRICITY_MARKET_PRICE_SIMULATION.jump_size_std', float)

        self.configs = getConfigs(self.__dict__)  #load all configs started not with _ to dict

    def getConfigsValues(self):
        return self.configs


class EnergyModuleConfigReader():
    """Module for reading Energy configs from file"""

    def __init__(self, country, _filename='em_config.ini', silently=False):
        silently = silently or silent()
        _config = parse_yaml(_filename, country, silently)

        #mean value for distribution of random factor for generating temperature
        self.mean = get_config_value(_config, 'NORMAL_DISTRIBUTION.mean', float)

        #stdev value for distribution of random factor for generating temperature
        self.stdev = self.mean * get_config_value(_config, 'NORMAL_DISTRIBUTION.stdev_percent', 'float_percent')

        self.TMin = get_config_value(_config, 'WEATHER_SIMULATION.TMin', float)
        self.TMax = get_config_value(_config, 'WEATHER_SIMULATION.TMin', float)

        self.data_uncertainty = get_config_value(_config, 'IRRADIATION_UNCERTAINTY.uncertainty_of_data', float)
        self.transposition_model_uncertainty = get_config_value(_config, 'IRRADIATION_UNCERTAINTY.transposition_model_uncertainty', float)
        self.interannual_variability_std = get_config_value(_config, 'IRRADIATION_UNCERTAINTY.interannual_variability_std', float)
        self.long_term_irradiation_uncertainty = get_config_value(_config, 'IRRADIATION_UNCERTAINTY.uncertainty_of_long_term_irradiation', float)
        self.dust_uncertainty_std = get_config_value(_config, 'IRRADIATION_UNCERTAINTY.dust_uncertainty_std', float)
        self.snow_uncertainty_std = get_config_value(_config, 'IRRADIATION_UNCERTAINTY.snow_uncertainty_std', float)

        self.inputs = self._parse_inputs(_config)

        self.configs = getConfigs(self.__dict__)  #load all configs started not with _ to dict

    def getConfigsValues(self):
        return self.configs

    def _parse_inputs(self, _config):
        dic = {}
        for month_no, values in _config['INPUTS'].items():
            ins = int(values['ins'])
            temp = round(float(values['temp']), 1)
            prod = float(values['prod'])
            dic[str(month_no)] = ([ins, temp, prod])
        return dic

    def getAvMonthInsolationMonth(self, month):
        """Returns average daily insolation on given date"""
        return self.inputs[str(month)][0]

    def getAvMonthTemperatureMonth(self, month):
        """Returns average daily insolation on given date"""
        return self.inputs[str(month)][1]

    def getAvProductionDayPerKw(self, month):
        """Returns average daily producion of electricty per kW on given date"""
        return self.inputs[str(month)][2]


class RiskModuleConfigReader():
    """Module for reading Risk configs from file"""

    def __init__(self, country, _filename='rm_config.ini'):
        _config = parse_yaml(_filename, country, silent())

        self.riskFreeRate = get_config_value(_config, 'RISK.riskFreeRate', float)
        self.benchmarkSharpeRatio = get_config_value(_config, 'RISK.benchmarkSharpeRatio', float)
        self.benchmarkModifiedSharpeRatio = get_config_value(_config, 'RISK.benchmarkModifiedSharpeRatio', float)

        self.configs = getConfigs(self.__dict__)  #load all configs started not with _ to dict

    def getConfigsValues(self):
        return self.configs


class EnviromentModuleConfigReader():
    """Module for reading Risk configs from file"""

    def __init__(self, country, _filename='enm_config.ini'):
        _config = parse_yaml(_filename, country, silent())

        self.pvequipment_disposal = get_config_value(_config, 'DISPOSAL.pvequipment_disposal', float)
        self.configs = getConfigs(self.__dict__)  #load all configs started not with _ to dict

    def getConfigsValues(self):
        return self.configs
