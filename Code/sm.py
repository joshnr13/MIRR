#!/usr/bin/env python
# -*- coding utf-8 -*-

import datetime
import ConfigParser
import os
import random

from annex import add_x_years, add_x_months, get_configs, float_range
from constants import TESTMODE
from base_class import BaseClassConfig
from config_readers import MainConfig, SubsidyModuleConfigReader

class SubsidyModule(BaseClassConfig, SubsidyModuleConfigReader):
    def __init__(self, config_module):
        BaseClassConfig.__init__(self, config_module)
        SubsidyModuleConfigReader.__init__(self)

    def subsidyProduction(self, date):
        """return subsidy in EUR for production 1Kwh on given @date"""
        if date >= self.first_day_subsidy and date <= self.last_day_subsidy:
            return self.kWh_subsidy
        else:
            return 0

if __name__ == '__main__':
    s = SubsidyModule(MainConfig())
    print s.getConfigsValues()