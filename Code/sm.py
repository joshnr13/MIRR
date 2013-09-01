#!/usr/bin/env python
# -*- coding utf-8 -*-

from base_class import BaseClassConfig
from config_readers import MainConfig, SubsidyModuleConfigReader

class SubsidyModule(BaseClassConfig, SubsidyModuleConfigReader):
    """Module for calculation subside values for production electricity"""
    def __init__(self, config_module):
        BaseClassConfig.__init__(self, config_module)  #init base class config to have ability to use all main config values
        SubsidyModuleConfigReader.__init__(self)  #load config values for current module

    def subsidyProduction(self, date):
        """return subsidy in EUR for production 1Kwh on given @date"""
        if date >= self.first_day_subsidy and date <= self.last_day_subsidy:  #if @date in range(start_subside-end_subside) - return subside, else 0
            return self.kWh_subsidy
        else:
            return 0

if __name__ == '__main__':
    s = SubsidyModule(MainConfig())
    print s.getConfigsValues()