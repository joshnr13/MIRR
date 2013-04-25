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
import ConfigParser
import os
from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from annex import Annuitet, last_day_month

class EconomicModule:

    def __init__(self, technology_module, subside_module):
        self.technology_module = technology_module
        self.subside_module = subside_module
        self.loadConfig()
        self.loadMainConfig()
        self.calcDebtPercents()

    def loadMainConfig(self, filename='main_config.ini'):
        """Reads main config file """
        config = ConfigParser.ConfigParser()
        filepath = os.path.join(os.getcwd(), 'configs', filename)
        config.read(filepath)
        self.lifetime = config.getint('Main', 'lifetime')
        self.resolution = config.getint('Main', 'resolution')
        self.start_date = datetime.datetime.strptime(config.get('Main', 'start_date'), '%Y/%m/%d').date()
        self.end_date = datetime.date(self.start_date.year + self.lifetime, self.start_date.month, self.start_date.day)

    def loadConfig(self, filename='ecm_config.ini'):
        """Reads module config file"""
        config = ConfigParser.ConfigParser()
        filepath = os.path.join(os.getcwd(), 'configs', filename)
        config.read(filepath)

        self.tax_rate = config.getfloat('Taxes', 'tax_rate')
        self.month_costs = config.getfloat('Costs', 'costs')
        self.costs_groth_rate = config.getfloat('Costs', 'growth_rate') / 100

        self.market_price = config.getfloat('Electricity', 'market_price')
        self.price_groth_rate = config.getfloat('Electricity', 'growth_rate') / 100

        self.investments = config.getfloat('Investments', 'investment_value') * 1000000

        self.debt = config.getfloat('Debt', 'debt_value') * self.investments
        self.debt_rate = config.getfloat('Debt', 'interest_rate')
        self.debt_years = config.getint('Debt', 'periods')

        self.amortization_duration = config.getfloat('Amortization', 'duration')


    def getRevenue(self, date_start, date_end):
        """return revenue from selling electricity + subsides for given period of time"""
        revenue = 0
        electricity_production = 0
        cur_date = date_start

        while cur_date <= date_end:
            electricity_production = self.technology_module.generateElectiricityProduction(cur_date)
            day_revenue = self.getDayRevenue(electricity_production,cur_date)
            subside_kwh = self.subside_module.subsidyProduction(cur_date)
            day_subside = electricity_production * subside_kwh
            revenue += (day_revenue + day_subside)
            cur_date += datetime.timedelta(days=1)

        return revenue


    def getDayRevenue(self, electricity_production, cur_date):
        return electricity_production * self.getPriceKwh(cur_date)

    def calcDepricationMonthly(self, date):
        """Calcultation of amortization in current month"""
        cur_month = self.getMonthNumber(date)
        deprication_duration_months = self.amortization_duration * 12

        if cur_month <= deprication_duration_months:
            return self.investments / deprication_duration_months
        else:
            return 0

    def calcDebtPercents(self):
        a = Annuitet(self.debt, self.debt_rate, self.debt_years)
        a.calculate()
        self.debt_percents = a.percents

    def getYearNumber(self, date):
        return date.year - self.start_date.year

    def getMonthNumber(self, date):
        """return current month number since start_date"""
        days_diff = (date - self.start_date).days
        month_diff = (days_diff / 30.4)
        cur_month = math.ceil(month_diff)
        return cur_month

    def getPriceKwh(self, date):
        """return kwh price for electricity at given day"""
        yearNumber = self.getYearNumber(date)
        return self.market_price * ((1 + self.price_groth_rate)  ** yearNumber)

    def getdailyCosts(self, date):
        """return costs per given day
        30.4 - average number of days per month
        """
        yearNumber = self.getYearNumber(date)
        return self.month_costs * ((1 + self.costs_groth_rate) ** yearNumber) / 30.4

    def getCosts(self, date_start, date_end):
        """sum of costs for all days in period """
        costs = 0
        cur_date = date_start

        while cur_date <= date_end:
            costs += self.getdailyCosts(cur_date)
            cur_date += datetime.timedelta(days=1)
        return costs

    def calculateMonthlyTaxes(self, date, year_revenue):
        """EBT in the year * 20% enetered only in december"""
        if date.month == 12:
            return year_revenue * self.tax_rate
        else:
            return 0

    def calculateMonthlyTaxRate(self, year_revenue):
        """EBT in the year * 20% enetered only in december"""
        return year_revenue * self.tax_rate



    def getDebtPayment(self, date_start, date_end):
        """calculate the payment of the debt principal based on constant annuity repayment  - http://en.wikipedia.org/wiki/Fixed_rate_mortgage
        365.25 - average number of days per year"""
        number_of_days = (date_end - date_start).days
        payment = self.debt_rate * self.debt * number_of_days / 365.25
        return payment

    def calculateInterests(self, date):
        """Return monthly debt percents we need to pay"""
        cur_month = self.getMonthNumber(date)
        if cur_month <= len(self.debt_percents):
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





    def generateISandBS(self): pass

    def calculateReturn(self):
        """calculates IRR and writes it to the database
        inputs are the monthly free cash flows (FCF)  for the whole project
        """

if __name__ == '__main__':
    start_date = datetime.date(2000, 1, 1)
    end_date = datetime.date(2001, 12, 31)
    em = EnergyModule()
    #print em.generatePrimaryEnergyAvaialbilityLifetime()
    technology_module = TechnologyModule(em)
    subside_module = SubsidyModule()
    ecm = EconomicModule(technology_module, subside_module)
    print ecm.getRevenue(start_date, start_date+datetime.timedelta(days=30))










