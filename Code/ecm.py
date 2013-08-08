#!/usr/bin/env python
# -*- coding utf-8 -*-

import datetime
import ConfigParser
import os
from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from annex import Annuitet, getDaysNoInMonth, years_between_1Jan, months_between, last_day_month, get_list_dates
from annex import add_x_years,add_x_months, month_number_days, last_day_next_month, get_configs,  OrderedDefaultdict, memoize
from config_readers import MainConfig, EconomicModuleConfigReader
from base_class import BaseClassConfig
from collections import OrderedDict
from database import Database


class EconomicModule(BaseClassConfig, EconomicModuleConfigReader):

    def __init__(self, config_module, technology_module, subside_module):
        BaseClassConfig.__init__(self, config_module)
        EconomicModuleConfigReader.__init__(self)
        self.db = Database()
        self.technology_module = technology_module
        self.subside_module = subside_module
        self.calc_config_values()
        self.calcDebtPercents()
        self.get_electricity_prices_lifetime()
        self.calc_electricity_production_lifetime()


    def calc_config_values(self):
        self.investments = self.technology_module.getInvestmentCost()
        self.investments_monthly = OrderedDefaultdict(int)
        self.investmentEquipment = self.investments
        self.debt = self.debt_share * self.investments
        self.capital = self.investments - self.debt

    def calc_electricity_production_lifetime(self):
        self.electricity_production = self.technology_module.generateElectricityProductionLifeTime()

    def get_electricity_prices_lifetime(self):
        self.electricity_prices = self.db.get_electricity_prices(self.electricity_prices_rnd_simulation)
        if not self.electricity_prices:
            raise ValueError("Please generate first Electricity prices before using it")
        #price = self.market_price
        #growth = 1 + self.price_groth_rate
        #dates = self.all_dates
        #start_year = self.start_date_project.year
        #last_day_construction = self.last_day_construction

        #self.electricity_prices = OrderedDict((date, price* (growth**(date.year-start_year) if date>last_day_construction else 0))  for date in dates)

    def get_electricity_production_lifetime(self):
        return  self.electricity_production

    def isConstructionStarted(self, date):
        """return  True if we recieved all permits and started but not finished
        construction of equipment"""
        if date > self.last_day_permit_procurement and date <= self.last_day_construction:
            return  True
        else:
            return  False

    #@memoize
    def isProductionElectricityStarted(self, date):
        """return  True if we recieved all permits, finished construction and can
        sell electricity"""
        if date > self.last_day_construction :
            return  True
        else:
            return  False

    def getRevenue(self, date_start, date_end):
        """return revenue from selling electricity and subsides for given period of time"""
        revenue_electricity = 0
        revenue_subside = 0
        cur_date = date_start
        date_list = get_list_dates(date_start, date_end)

        for cur_date in date_list:
            electricity_production = self.getElectricityProduction(cur_date)
            day_revenue_electricity = electricity_production * self.getPriceKwh(cur_date)
            day_revenue_subsidy = electricity_production * self.subside_module.subsidyProduction(cur_date)

            revenue_electricity += day_revenue_electricity
            revenue_subside += day_revenue_subsidy

        return revenue_electricity, revenue_subside

    def getElectricityProduction(self,  date):
        """return  production of electricity at given date"""
        return  self.electricity_production[date]


    def _getDayRevenue_electricity(self, cur_date, electricity_production=None):
        """Calc revenue per date part: electricity"""
        return

        if self.isProductionElectricityStarted(cur_date):
            return electricity_production * self.getPriceKwh(cur_date)
        else:
            return 0

    def _getDayRevenue_subsidy(self, cur_date, electricity_production=None):
        """Calc revenue per date part: subsidy"""

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
        """The investment is spread as follows:
             30% - 2 month before the start of construction
             50% - at start of construction
             20% - at the end of construction
        """

        self.paid_in_rest = self.initial_paid_in_capital
        self.debt_rest_payments_wo_percents = OrderedDefaultdict(int)
        self.debt_percents = OrderedDefaultdict(int)
        self.paid_in_monthly = OrderedDefaultdict(int)

        ####### FIRST - 30% 2 month before the start of construction
        part1 = 0.3
        start_date1 = last_day_month(add_x_months(self.first_day_construction, -2))
        self.calc_paidin_investment(start_date1, part1)

        ####### SECOND - 50% - at start of construction
        part2 = 0.5
        start_date2 = last_day_month(self.first_day_construction)
        self.calc_paidin_investment(start_date2, part2)

        ####### THIRD - 20% - at the end of construction
        part3 = 0.2
        start_date3 = last_day_month(self.last_day_construction)
        self.calc_paidin_investment(start_date3, part3)

    def getPaidInDelta(self, date):
        """return  current month delta of paid-in capital"""
        return  self.paid_in_monthly[date]

    def calc_paidin_investment(self, date, part):
        investment_paid_in = self._calc_paid_investment_part(part)
        debt_value = self.debt * part - investment_paid_in

        a = Annuitet(debt_value, self.debt_rate, self.debt_years, date)
        a.calculate()

        self.investments_monthly[date] = investment_paid_in + debt_value
        self.paid_in_monthly[date] = investment_paid_in

        for k, v in a.percent_payments.items():
            self.debt_percents[k] += v

        for k, v in a.rest_payments_wo_percents.items():
            self.debt_rest_payments_wo_percents[k] += v


        #self.debt_percents[date] += a.percent_payments.values()
        #self.debt_rest_payments_wo_percents += a.rest_payments_wo_percents.values()


    def _calc_paid_investment_part(self, part):
        investment_share = (1 - self.debt_share)
        invest_value = investment_share*part *self.debt

        if self.paid_in_rest > 0:
            if invest_value > self.paid_in_rest:
                self.paid_in_rest = 0
                invest_value = invest_value - self.paid_in_rest
            else:
                self.paid_in_rest -= invest_value
                invest_value = self.paid_in_rest

        return  invest_value

    def getPriceKwh(self, date):
        """return kwh price for electricity at given day"""
        #if isinstance(date, datetime.date):
            #date = date.strftime('%Y-%m-%d')
        return  self.electricity_prices[date]

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
        return self.developmentCostDuringPermitProcurement / month_number_days(date)

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
        cur_date = date_start
        list_dates = get_list_dates(date_start, date_end)
        return sum([cost_function(date) for date in list_dates])

        #while cur_date <= date_end:
            #costs += cost_function(cur_date)
            #cur_date += datetime.timedelta(days=1)
        #return costs

    def getTaxRate(self):
        """return taxrate in float"""
        return self.tax_rate

    def getMonthlyInvestments(self, date):
        """Gets investments of current date (on month of that date)"""
        return  self.investments_monthly[date]

        #last_day = last_day_month(date)
        #start_construction = self.first_day_construction

        #if date.month  ==  start_construction.month and date.year == start_construction.year:
            #return self.investments
        #else:
            #return 0

    def getDebtPayment(self, date_start, date_end):
        """calculate the payment of the debt principal based on constant annuity repayment  - http://en.wikipedia.org/wiki/Fixed_rate_mortgage
        365.25 - average number of days per year"""
        number_of_days = (date_end - date_start).days
        payment = self.debt_rate * self.debt * number_of_days / 365.25
        return payment

    def calculateDebtInterests(self, date):
        """Return monthly debt percents we need to pay"""
        return  self.debt_percents.get(date, 0)

    def calculateDebtBody(self, date):
        """Return monthly debt percents we need to pay"""
        return  self.debt_rest_payments_wo_percents.get(date, 0)

if __name__ == '__main__':
    mainconfig = MainConfig()
    em = EnergyModule(mainconfig)
    technology_module = TechnologyModule(mainconfig, em)
    subside_module = SubsidyModule(mainconfig)
    from annex import timer

    @timer
    def test1():
        ecm = EconomicModule(mainconfig, technology_module, subside_module)

    test1()












