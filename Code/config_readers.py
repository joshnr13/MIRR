#!/usr/bin/env python
# -*- coding utf-8 -*-

import os
import random
import datetime
import ConfigParser
from annex import add_x_months, add_x_years, get_report_dates, get_configs, float_range
from constants import TESTMODE

class ModuleConfigReader():
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

        self.last_day_construction = add_x_months(self.start_date, self.real_permit_procurement_duration+self.real_construction_duration)
        self.last_day_permit_procurement = add_x_months(self.start_date, self.real_permit_procurement_duration)
        self.end_date = add_x_years(self.start_date, self.lifetime)
        self.report_dates, self.report_dates_y = get_report_dates(self.start_date, self.end_date)

        self.simulation_number = _config.getint('Simulation', 'simulation_number')
        self.configs = get_configs(self.__dict__)

    def getConfigsValues(self):
        return  self.configs


class MainConfig():
    def __init__(self):
        self.configs = ModuleConfigReader().getConfigsValues()

    def getStartDate(self):
        return self.configs["start_date"]

    def getEndDate(self):
        return self.configs["end_date"]

    def getPermitProcurementDuration(self):
        return  self.configs["real_permit_procurement_duration"]

    def getConstructionDuration(self):
        return  self.configs["real_construction_duration"]

    def getLastDayPermitProcurement(self):
        return  self.configs["last_day_permit_procurement"]

    def getLastDayConstruction(self):
        return  self.configs["last_day_construction"]

    def getResolution(self):
        return  self.configs["resolution"]

    def getLifeTime(self):
        return  self.configs["lifetime"]

    def getReportDates(self):
        return self.configs["report_dates"]

    def getReportDatesY(self):
        return self.configs["report_dates_y"]

    def getConfigsValues(self):
        """return  dict with config names and values
        return  Config values from file + some random generated
        """
        return self.configs

    def getSimulationNumber(self):
        return self.configs["simulation_number"]



class SubsidyModuleConfigReader():
    def __init__(self, _filename='sm_config.ini'):
        """Reads module config file"""
        _config = ConfigParser.ConfigParser()
        _filepath = os.path.join(os.getcwd(), 'configs', _filename)
        _config.read(_filepath)

        _delay_lower_limit = _config.getfloat('Subsidy', 'delay_lower_limit')
        _delay_upper_limit = _config.getfloat('Subsidy', 'delay_upper_limit')

        self._kWh_subsidy_lower_limit = _config.getfloat('Subsidy', 'kWh_subsidy_lower_limit')
        self._kWh_subsidy_upper_limit = _config.getfloat('Subsidy', 'kWh_subsidy_upper_limit')
        self._duration_upper_limit = _config.getfloat('Subsidy', 'duration_upper_limit')
        self._duration_lower_limit = _config.getfloat('Subsidy', 'duration_lower_limit')

        if TESTMODE:
            self.delay = 0
            self.kWh_subsidy = (self._kWh_subsidy_lower_limit + self._kWh_subsidy_upper_limit) / 2.0
            self.duration = (self.duration_upper_limit + self.duration_lower_limit) / 2.0
        else:
            self.delay = random.randrange(_delay_lower_limit, _delay_upper_limit+1)
            self.kWh_subsidy = random.choice(float_range(self._kWh_subsidy_lower_limit ,self._kWh_subsidy_upper_limit, 0.001, True))
            self.duration = random.randint(self._duration_upper_limit, self._duration_lower_limit)

        self.first_day_subside = add_x_months(self.last_day_construction+datetime.timedelta(days=1), self.delay)
        self.last_day_subside = add_x_months(self.first_day_subside, self.duration)

        self.configs = get_configs(self.__dict__)

    def getConfigsValues(self):
        return  self.configs

class TechnologyModuleConfigReader():
    def __init__(self, _filename='tm_config.ini'):
        """Reads module config file"""
        _config = ConfigParser.ConfigParser()
        _filepath = os.path.join(os.getcwd(), 'configs', _filename)
        _config.read(_filepath)

        ######################## BASE ###################
        self.electr_conv_factor = _config.getfloat('Electricity', 'ConversionFactor')
        self.groups_number = _config.getint('Equipment', 'groups_number')
        self.module_power = _config.getfloat('Equipment', 'module_power')
        self.modules_in_group = _config.getint('Equipment', 'modules_in_group')
        self.transformers_number = _config.getint('Equipment', 'transformers_number')
        self.network_available_probability = _config.getfloat('Network', 'network_available_probability') / 100

        ######################## PRICE ###################
        self.module_price = _config.getfloat('Price', 'module_price')
        self.inverter_price = _config.getfloat('Price', 'inverter_price')
        self.transformer_price = _config.getfloat('Price', 'transformer_price')
        self.documentation_price = _config.getfloat('Price', 'documentation_price')
        self.connection_grip_price = _config.getfloat('Price', 'connection_grip_price')

        ####################### RELIABILTY ####################
        self.module_reliability = _config.getfloat('Reliability', 'module_reliability') / 100
        self.inverter_reliability = _config.getfloat('Reliability', 'inverter_reliability') / 100
        self.transformer_reliability = _config.getfloat('Reliability', 'transformer_reliability') / 100

        ####################### EFFICIENCY ####################
        self.module_power_efficiency = _config.getfloat('Efficiency', 'module_power_efficiency') / 100
        self.inverter_power_efficiency = _config.getfloat('Efficiency', 'inverter_power_efficiency') / 100
        self.transformer_power_efficiency = _config.getfloat('Efficiency', 'transformer_power_efficiency') / 100


        ####################### TOTAL_POWER ####################
        self.total_power = 10000

        self.configs = get_configs(self.__dict__)

    def getConfigsValues(self):
        return  self.configs



class EconomicModuleConfigReader():
    def __init__(self,  _filename='ecm_config.ini'):
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
        self.insuranceLastDayEquipment = add_x_years(self.start_date_project, self.insuranceDurationEquipment)

        self.developmentCostDuringPermitProcurement = _config.getfloat('Costs', 'developmentCostDuringPermitProcurement')
        self.developmentCostDuringConstruction = _config.getfloat('Costs', 'developmentCostDuringConstruction')

        self.market_price = _config.getfloat('Electricity', 'market_price')
        self.price_groth_rate = _config.getfloat('Electricity', 'growth_rate') / 100

        ######################### INVESTMENTS #############################################

        #self.investments = _config.getfloat('Investments', 'investment_value')
        #self.investmentEquipment = _config.getfloat('Investments', 'investmentEquipment')

        ######################### DEBT ########################################

        self.debt_part = _config.getfloat('Debt', 'debt_value') / 100
        self.debt_rate = _config.getfloat('Debt', 'interest_rate') / 100
        self.debt_rate_short = _config.getfloat('Debt', 'interest_rate_short') / 100
        self.debt_years = _config.getint('Debt', 'periods')

        ######################### DEPRICATION #################################

        self.deprication_duration = _config.getfloat('Amortization', 'duration')

        self.configs = get_configs(self.__dict__)

    def getConfigsValues(self):
        return  self.configs


class EnergyModuleConfigReader():
    def __init__(self, _filename='em_config.ini'):
        _config = ConfigParser.ConfigParser()
        _filepath = os.path.join(os.getcwd(), 'configs', _filename)
        _config.read(_filepath)

        self.mean = _config.getfloat('NormalDistribution', 'mean')
        self.stdev = _config.getfloat('NormalDistribution', 'stdev')

        self.configs = get_configs(self.__dict__)

    def getConfigsValues(self):
        return  self.configs


if __name__ == '__main__':

    m = ModuleConfigReader()
    print m.getConfigsValues()









