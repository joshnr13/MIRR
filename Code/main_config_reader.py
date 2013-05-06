#!/usr/bin/env python
# -*- coding utf-8 -*-

import os
import random
import datetime
import ConfigParser
from annex import add_x_months, add_x_years
from constants import TESTMODE

class MainConfig():
    def __init__(self):
        self.load()

    def load(self, filename='main_config.ini'):
        """Reads main config file """

        config = ConfigParser.ConfigParser()
        filepath = os.path.join(os.getcwd(), 'configs', filename)
        config.read(filepath)
        self.lifetime = config.getint('Main', 'lifetime')
        self.resolution = config.getint('Main', 'resolution')
        self.start_date = datetime.datetime.strptime(config.get('Main', 'start_date'), '%Y/%m/%d').date()

        ######################### DELAYS ######################################
        permit_procurement_duration_lower_limit = config.getfloat('Delays', 'permit_procurement_duration_lower_limit')
        permit_procurement_duration_upper_limit = config.getfloat('Delays', 'permit_procurement_duration_upper_limit')
        construction_duration_lower_limit = config.getfloat('Delays', 'construction_duration_lower_limit')
        construction_duration_upper_limit = config.getfloat('Delays', 'construction_duration_upper_limit')

        if TESTMODE:
            self.real_permit_procurement_duration = 0
            self.real_construction_duration = 0
        else :
            self.real_permit_procurement_duration = random.randrange(permit_procurement_duration_lower_limit, permit_procurement_duration_upper_limit+1)
            self.real_construction_duration = random.randrange(construction_duration_lower_limit, construction_duration_upper_limit+1)

        self.last_day_construction = add_x_months(self.start_date, self.real_permit_procurement_duration+self.real_construction_duration)
        self.last_day_permit_procurement = add_x_months(self.start_date, self.real_permit_procurement_duration)

        self.end_date = add_x_years(self.start_date, self.lifetime)

    def getStartDate(self):
        return self.start_date

    def getEndDate(self):
        return self.end_date

    def getPermitProcurementDuration(self):
        return  self.real_permit_procurement_duration

    def getConstructionDuration(self):
        return  self.real_construction_duration

    def getLastDayPermitProcurement(self):
        return  self.last_day_permit_procurement

    def getLastDayConstruction(self):
        return  self.last_day_construction

    def getResolution(self):
        return  self.resolution

    def getLifeTime(self):
        return  self.lifetime


