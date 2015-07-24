#!/usr/bin/env python
# -*- coding utf-8 -*-
from base_class import BaseClassConfig
from config_readers import EnviromentModuleConfigReader


class EnvironmentalModule(BaseClassConfig, EnviromentModuleConfigReader):
    def __init__(self, config_module, country, total_nominal_power):
        BaseClassConfig.__init__(self, config_module)  #loading Main config
        EnviromentModuleConfigReader.__init__(self, country)  #loading Enviroment Config
        self.total_nominal_power = total_nominal_power  # nominal power from tm

    def getEquipmentDisposalCosts(self):
        return self.pvequipment_disposal * self.total_nominal_power  # total nominal power * costs/kW
