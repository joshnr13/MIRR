#!/usr/bin/env python
# -*- coding utf-8 -*-

import datetime
import ConfigParser
import os
from tm import TechnologyModule
from em import EnergyModule
from annex import years_between


class SubsidyModule():
    def __init__(self):
            self.loadConfig()
            self.loadMainConfig()

    def loadMainConfig(self, filename='main_config.ini'):
        """Reads main config file """
        config = ConfigParser.ConfigParser()
        filepath = os.path.join(os.getcwd(), 'configs', filename)
        config.read(filepath)
        self.lifetime = config.getint('Main', 'lifetime')
        self.resolution = config.getint('Main', 'resolution')
        self.start_date = datetime.datetime.strptime(config.get('Main', 'start_date'), '%Y/%m/%d').date()
        self.end_date = datetime.date(self.start_date.year + self.lifetime, self.start_date.month, self.start_date.day)

    def loadConfig(self, filename='sm_config.ini'):
        """Reads module config file"""
        config = ConfigParser.ConfigParser()
        filepath = os.path.join(os.getcwd(), 'configs', filename)
        config.read(filepath)
        self.duration = config.getfloat('Subsidy', 'duration')
        self.kWh_subsidy = config.getfloat('Subsidy', 'kWh_subsidy')

    def subsidyProduction(self, date):
        """return subsidy for production 1Kwh on given date"""
        if years_between(self.start_date, date) <= self.duration:
            return self.kWh_subsidy
        else:
            return 0

