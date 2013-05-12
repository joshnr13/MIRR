#!/usr/bin/env python
# -*- coding utf-8 -*-

import os
import random
import datetime
import ConfigParser
from annex import add_x_months, add_x_years, get_report_dates, get_configs
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

    def getConfigValues(self):
        """return  dict with config names and values
        return  Config values from file + some random generated
        """
        return self.configs

    def getSimulationNumber(self):
        return self.configs["simulation_number"]









