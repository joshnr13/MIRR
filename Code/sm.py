#!/usr/bin/env python
# -*- coding utf-8 -*-

import datetime
import ConfigParser
import os
from tm import TechnologyModule
from em import EnergyModule
from annex import years_between
from main_config_reader import MainConfig
from base_class import BaseClassConfig
from annex import add_x_years

class SubsidyModule(BaseClassConfig):
    def __init__(self, config_module):
            BaseClassConfig.__init__(self, config_module)
            self.loadConfig()

    def loadConfig(self, filename='sm_config.ini'):
        """Reads module config file"""
        config = ConfigParser.ConfigParser()
        filepath = os.path.join(os.getcwd(), 'configs', filename)
        config.read(filepath)
        self.kWh_subsidy = config.getfloat('Subsidy', 'kWh_subsidy')
        self.duration = config.getfloat('Subsidy', 'duration')
        self.last_day_subside = add_x_years(self.last_day_construction, self.duration)

    def subsidyProduction(self, date):
        """return subsidy for production 1Kwh on given date"""
        if date > self.last_day_construction and date <= self.last_day_subside:
            return self.kWh_subsidy
        else:
            return 0

