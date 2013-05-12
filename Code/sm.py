#!/usr/bin/env python
# -*- coding utf-8 -*-

import datetime
import ConfigParser
import os
import random

from annex import add_x_years, add_x_months
from annex import get_configs
from constants import TESTMODE
from base_class import BaseClassConfig

class SubsidyModule(BaseClassConfig):
    def __init__(self, config_module):
        BaseClassConfig.__init__(self, config_module)
        self.loadConfig()

    def loadConfig(self, _filename='sm_config.ini'):
        """Reads module config file"""
        _config = ConfigParser.ConfigParser()
        _filepath = os.path.join(os.getcwd(), 'configs', _filename)
        _config.read(_filepath)

        _delay_lower_limit = _config.getfloat('Subsidy', 'delay_lower_limit')
        _delay_upper_limit = _config.getfloat('Subsidy', 'delay_upper_limit')

        self.kWh_subsidy = _config.getfloat('Subsidy', 'kWh_subsidy')
        self.duration = _config.getfloat('Subsidy', 'duration')

        if TESTMODE:
            self.real_delay = 0
        else:
            self.real_delay = random.randrange(_delay_lower_limit, _delay_upper_limit+1)

        self.first_day_subside = add_x_months(self.last_day_construction+datetime.timedelta(days=1), self.real_delay)
        self.last_day_subside = add_x_months(self.first_day_subside, self.duration)

        self.configs = get_configs(locals())

    def subsidyProduction(self, date):
        """return subsidy for production 1Kwh on given date"""
        if date >= self.first_day_subside and date <= self.last_day_subside:
            return self.kWh_subsidy
        else:
            return 0

