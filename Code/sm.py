#!/usr/bin/env python
# -*- coding utf-8 -*-

import datetime
import ConfigParser
import os
import random

from annex import add_x_years, add_x_months
from constants import TESTMODE
from base_class import BaseClassConfig

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

        delay_lower_limit = config.getfloat('Subsidy', 'delay_lower_limit')
        delay_upper_limit = config.getfloat('Subsidy', 'delay_upper_limit')

        if TESTMODE:
            self.real_delay = 0
        else:
            self.real_delay = random.randrange(delay_lower_limit, delay_upper_limit+1)

        self.first_day_subside = add_x_months(self.last_day_construction+datetime.timedelta(days=1), self.real_delay)
        self.last_day_subside = add_x_years(self.first_day_subside, self.duration)

    def subsidyProduction(self, date):
        """return subsidy for production 1Kwh on given date"""
        if date >= self.first_day_subside and date <= self.last_day_subside:
            return self.kWh_subsidy
        else:
            return 0

