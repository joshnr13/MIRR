#!/usr/bin/env python
# -*- coding utf-8 -*-

import datetime
import ConfigParser
import os
import random

from annex import add_x_years, add_x_months, get_configs, float_range
from constants import TESTMODE
from base_class import BaseClassConfig


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
        self.duration = _config.getfloat('Subsidy', 'duration')

        if TESTMODE:
            self.delay = 0
            self.kWh_subsidy = (self._kWh_subsidy_lower_limit + self._kWh_subsidy_upper_limit) / 2
        else:
            self.delay = random.randrange(_delay_lower_limit, _delay_upper_limit+1)
            self.kWh_subsidy = random.choice(float_range(self._kWh_subsidy_lower_limit ,self._kWh_subsidy_upper_limit, 0.01, True))

        self.first_day_subside = add_x_months(self.last_day_construction+datetime.timedelta(days=1), self.delay)
        self.last_day_subside = add_x_months(self.first_day_subside, self.duration)

        self.configs = get_configs(locals())

class SubsidyModule(BaseClassConfig, SubsidyModuleConfigReader):
    def __init__(self, config_module):
        BaseClassConfig.__init__(self, config_module)
        SubsidyModuleConfigReader.__init__(self)

    def subsidyProduction(self, date):
        """return subsidy in EUR for production 1Kwh on given @date"""
        if date >= self.first_day_subside and date <= self.last_day_subside:
            return self.kWh_subsidy
        else:
            return 0


if __name__ == '__main__':
    from main_config_reader import MainConfig
    s = SubsidyModule(MainConfig())