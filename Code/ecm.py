#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
calculateInterests
((debt in previous period + debt in current period) /2) * interest rate * num of days/365

calculateFCF
calculates the free cash flow based on IS nad BS
net earnings + amortisation - investments in long term assests

generateISandBS
parameters: dateStart; dateEnd
"""

import datetime
import math
import random
import ConfigParser
import os
from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from annex import Annuitet, last_day_month,  getDaysNoInMonth, years_between_1Jan, months_between
from annex import add_x_months, add_x_years, month_number_days
from main_config_reader import MainConfig
from base_class import BaseClassConfig

class EconomicModule(BaseClassConfig):

    def __init__(self, config_module, technology_module, subside_module):
        BaseClassConfig.__init__(self, config_module)
        self.technology_module = technology_module
        self.subside_module = subside_module
        self.loadConfig()
        self.calcDebtPercents()

    def isConstructionStarted(self, date):
        """return  True if we recieved all permits and started but not finished
        construction of equipment"""
        if date > self.last_day_permit_procurement and date <= self.last_day_construction:
            return  True
        else:
            return  False

    def isProductionElectricityStarted(self, date):
        """return  True if we recieved all permits, finished construction and can
        sell electricity"""
        if date > self.last_day_construction :
            return  True
        else:
            return  False


    def loadConfig(self, filename='ecm_config.ini'):
        """Reads module config file
        @self.insuranceLastDayEquipment - last day when we need to pay for insurance
        """
        config = ConfigParser.ConfigParser()
        filepath = os.path.join(os.getcwd(), 'configs', filename)
        config.read(filepath)

        self.tax_rate = config.getfloat('Taxes', 'tax_rate') / 100

        self.administrativeCosts = config.getfloat('Costs', 'administrativeCosts')
        self.administrativeCostsGrowth_rate = config.getfloat('Costs', 'administrativeCostsGrowth_rate') / 100
        self.insuranceFeeEquipment = config.getfloat('Costs', 'insuranceFeeEquipment') / 100
        self.insuranceDurationEquipment = config.getfloat('Costs', 'insuranceDurationEquipment')
        self.insuranceLastDayEquipment = add_x_years(self.start_date_project, self.insuranceDurationEquipment)

        self.getDevelopmentCostDuringPermitProcurement = config.getfloat('Costs', 'developmentCostDuringPermitProcurement')
        self.developmentCostDuringConstruction = config.getfloat('Costs', 'developmentCostDuringConstruction')

        self.market_price = config.getfloat('Electricity', 'market_price')
        self.price_groth_rate = config.getfloat('Electricity', 'growth_rate') / 100

        self.investments = config.getfloat('Investments', 'investment_value')
        self.investmentEquipment = config.getfloat('Investments', 'investmentEquipment')

        ######################### DEBT ########################################

        self.debt = config.getfloat('Debt', 'debt_value') * self.investments / 100
        self.debt_rate = config.getfloat('Debt', 'interest_rate') / 100
        self.debt_years = config.getint('Debt', 'periods')

        ######################### DEPRICATION #################################

        self.deprication_duration = config.getfloat('Amortization', 'duration')

    def getRevenue(self, date_start, date_end):
        """return revenue from selling electricity + subsides for given period of time"""
        revenue = 0
        cur_date = date_start

        while cur_date <= date_end:
            electricity_production = self.getElectricityProduction(cur_date)
            day_revenue_electricity = self._getDayRevenue_electricity(cur_date, electricity_production)
            day_revenue_subsidy = self._getDayRevenue_subsidy(cur_date, electricity_production)
            cur_date += datetime.timedelta(days=1)
            revenue += day_revenue_electricity + day_revenue_subsidy
        return revenue

    def getRevenue_elecricity(self, date_start, date_end):
        """return revenue from selling electricity for given period of time"""
        revenue = 0
        cur_date = date_start

        while cur_date <= date_end:
            electricity_production = self.getElectricityProduction(cur_date)
            day_revenue_electricity = self._getDayRevenue_electricity(cur_date, electricity_production)
            cur_date += datetime.timedelta(days=1)
            revenue += day_revenue_electricity
        return revenue

    def getRevenue_subside(self, date_start, date_end):
        """return revenue from subsides for given period of time"""
        revenue = 0
        cur_date = date_start

        while cur_date <= date_end:
            electricity_production = self.getElectricityProduction(cur_date)
            day_revenue_subsidy = self._getDayRevenue_subsidy(cur_date, electricity_production)
            cur_date += datetime.timedelta(days=1)
            revenue += day_revenue_subsidy
        return revenue

    def getElectricityProduction(self,  date):
        """return  production of electricity at given date"""
        return self.technology_module.generateElectiricityProduction(date)

    def _getDayRevenue_electricity(self, cur_date, electricity_production=None):
        """Calc revenue per date part: electricity"""
        if electricity_production is  None:
            electricity_production = self.getElectricityProduction(cur_date)

        if self.isProductionElectricityStarted(cur_date):
            return electricity_production * self.getPriceKwh(cur_date)
        else:
            return 0

    def _getDayRevenue_subsidy(self, cur_date, electricity_production=None):
        """Calc revenue per date part: subsidy"""
        if electricity_production is  None:
            electricity_production = self.getElectricityProduction(cur_date)

        if self.isProductionElectricityStarted(cur_date):
            subside_kwh = self.subside_module.subsidyProduction(cur_date)
            return   electricity_production * subside_kwh
        else:
            return 0


    def calcDepricationMonthly(self, date):
        """Calcultation of amortization in current month"""
        cur_month = months_between(self.start_date_project, date)
        deprication_duration_months = self.deprication_duration * 12

        cur_month = months_between(self.last_day_construction+datetime.timedelta(days=1), date)
        if cur_month <= 0:
            return 0
        elif cur_month <= deprication_duration_months:
            return self.investments / deprication_duration_months
        else:
            return 0

    def calcDebtPercents(self):
        a = Annuitet(self.debt, self.debt_rate, self.debt_years)
        a.calculate()
        self.debt_percents = a.percents

    def getPriceKwh(self, date):
        """return kwh price for electricity at given day"""
        yearNumber = years_between_1Jan(self.start_date_project, date)
        return self.market_price * ((1 + self.price_groth_rate)  ** yearNumber)

    def _getDevelopmentCosts(self, date):
        """costs for developing phase of project at given date (1day)"""
        if self.isProductionElectricityStarted(date):
            return 0  #we have finished with development costs
        elif self.isConstructionStarted(date):
            return self._getDevelopmentCostDuringConstruction(date)
        else:
            return self._getDevelopmentCostDuringPermitProcurement(date)

    def _getDevelopmentCostDuringPermitProcurement(self, date):
        """costs for developing phase of project at given date (1day) - part permit procurement"""
        return self.getDevelopmentCostDuringPermitProcurement / month_number_days(date)

    def _getDevelopmentCostDuringConstruction(self, date):
        """costs for developing phase of project at given date (1day) - part construction"""
        return self.developmentCostDuringConstruction / month_number_days(date)

    def _getOperationalCosts(self, date):
        """Operational costs at given date (1day)"""
        if self.isProductionElectricityStarted(date):
            return self._getInsuranceCosts(date) + self._getAdministrativeCosts(date)
        else:
            return  0

    def _getAdministrativeCosts(self, date):
        """return administrative costs at given date (1day)"""
        yearNumber = years_between_1Jan(self.start_date_project, date)
        return self.administrativeCosts * ((1 + self.administrativeCostsGrowth_rate) ** yearNumber) / getDaysNoInMonth(date)

    def _getInsuranceCosts(self, date):
        """return insurance costs at give date (1day)"""
        return  self.insuranceFeeEquipment * self.investmentEquipment / (getDaysNoInMonth(date) * 12)

    def getCosts(self, date_start, date_end):
        """sum of costs for all days in RANGE period """
        return self.getDevelopmentCosts(date_start, date_end) + self.getOperationalCosts(date_start, date_end)

    def getInsuranceCosts(self, date_start, date_end):
        """sum of Insurance Costs for all days in RANGE period """
        return self.getSomeCostsRange(self._getInsuranceCosts, date_start, date_end)

    def getDevelopmentCosts(self, date_start, date_end):
        """sum of Development Costs for all days in RANGE period """
        return self.getSomeCostsRange(self._getDevelopmentCosts, date_start, date_end)

    def getDevelopmentCostDuringPermitProcurement(self, date_start, date_end):
        """sum of Development Cost DuringPermitProcurement for all days in RANGE period """
        return self.getSomeCostsRange(self._getDevelopmentCostDuringPermitProcurement, date_start, date_end)

    def getDevelopmentCostDuringConstruction(self, date_start, date_end):
        """sum of Development Cost DuringConstruction for all days in RANGE period """
        return self.getSomeCostsRange(self._getDevelopmentCostDuringConstruction, date_start, date_end)

    def getOperationalCosts(self, date_start, date_end):
        """sum of Operational Costs for all days in RANGE period """
        return self.getSomeCostsRange(self._getOperationalCosts, date_start, date_end)

    def getAdministrativeCosts(self, date_start, date_end):
        """sum of Administrative Costs for all days in RANGE period """
        return self.getSomeCostsRange(self._getAdministrativeCosts, date_start, date_end)

    def getSomeCostsRange(self, cost_function, date_start, date_end):
        """basic function to calculate range costs"""
        costs = 0
        cur_date = date_start

        while cur_date <= date_end:
            costs += cost_function(cur_date)
            cur_date += datetime.timedelta(days=1)
        return costs

    def getTaxRate(self):
        """return taxrate in float"""
        return self.tax_rate

    def getMonthlyInvestments(self, date):
        if date.month  ==  self.start_date_project.month and date.year == self.start_date_project.year:
            return self.investments
        else:
            return 0


    def getDebtPayment(self, date_start, date_end):
        """calculate the payment of the debt principal based on constant annuity repayment  - http://en.wikipedia.org/wiki/Fixed_rate_mortgage
        365.25 - average number of days per year"""
        number_of_days = (date_end - date_start).days
        payment = self.debt_rate * self.debt * number_of_days / 365.25
        return payment

    def calculateInterests(self, date):
        """Return monthly debt percents we need to pay"""
        cur_month = months_between(self.start_date_project, date)
        if cur_month < len(self.debt_percents):
            return self.debt_percents[cur_month]
        else:
            return 0

    def getMonthlyInterests(self, date_start, date_end):
        pass

    def calculateFCF(self):
        """  net earnings (revenue - costs) + amortisation - investments in long term assests"""
        """
        operational_results = Revenue + Amortization - Debt_percents - Taxes
        investments_results = Investments (only in 1 period)
        financial_results = returns_of_debts
        FCF = operational_results-

        """

    def calculateReturn(self):
        """calculates IRR and writes it to the database
        inputs are the monthly free cash flows (FCF)  for the whole project
        """

if __name__ == '__main__':
    mainconfig = MainConfig()
    em = EnergyModule(mainconfig)
    technology_module = TechnologyModule(em)
    subside_module = SubsidyModule()
    ecm = EconomicModule(mainconfig, technology_module, subside_module)

    start_date = datetime.date(2000, 1, 1)
    print ecm.getRevenue(start_date, start_date+datetime.timedelta(days=30))










