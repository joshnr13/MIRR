#!/usr/bin/env python
# -*- coding utf-8 -*-

import datetime
import ConfigParser
import os
import numpy as np

from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from annex import Annuitet, getDaysNoInMonth, yearsBetween1Jan, monthsBetween, lastDayMonth, getListDates
from annex import addXYears,addXMonths, nubmerDaysInMonth, lastDayNextMonth, getConfigs,  OrderedDefaultdict, memoize
from config_readers import MainConfig, EconomicModuleConfigReader
from base_class import BaseClassConfig
from collections import OrderedDict
from database import Database


class ElectricityMarketPriceSimulation(EconomicModuleConfigReader):

    def __init__(self, period, simulations_no):
        start_date_project = period[0]
        EconomicModuleConfigReader.__init__(self, start_date_project)
        self.N = len(period)
        self.period = period
        self.simulations_no = simulations_no
        self.db = Database()

    def clean_prev_data(self):
        print "Cleaning previous data"
        self.db.clean_previous_electricity_price_data()

    def write_electricity_price_data(self, data):
        self.db.write_electricity_prices(data)
        print 'Writing electricity price simulation %s' % data["simulation_no"]

    def simulate(self):
        self.clean_prev_data()
        for simulation_no in range(1, self.simulations_no+1):
            data = self.generate_one_simulation(simulation_no)
            self.write_electricity_price_data(data)

    def generate_one_simulation(self, simulation_no):
        days_dict = OrderedDict()
        self.poisson_steps = Poisson_step(self.Lambda, size=self.N)
        prices = self.calc_price_for_period(self.S0)

        for date, price in zip(self.period, prices):
            date_str = date.strftime("%Y-%m-%d")
            days_dict[date_str] = price / 1000.0
        simulation_result = {"simulation_no": simulation_no, "data": days_dict}
        return  simulation_result

    def calc_J(self):
        """Calcultation of J as random with mean=loc and std=scale"""
        return  np.random.normal(loc=0,scale=1)  #loc means - mean, scale -std



    def calc_price_delta(self, prev_price, iteration_no):
        """Calculated delta price based on @prev_price"""
        delta_Z = np.random.normal(loc=0, scale=0.4)
        J = self.calc_J()
        delta_q = self.poisson_steps.get_delta(iteration_no)
        delta_price = self.k * (self.theta * (1 + self.y*iteration_no/365)- prev_price) * self.dt + self.sigma * delta_Z + (J*(1 + self.y*iteration_no/365)) * delta_q
        return  delta_price

    def calc_price_for_period(self, prev_price):
        """Calculate price for whole period"""
        result = []
        for i in range(1, self.N+1):
            price = prev_price + self.calc_price_delta(prev_price, i)
            prev_price = price
            result.append(price)
        return  result

class Poisson_step():
    """class for holding generated Poisson values"""
    def __init__(self, lam, size):
        self.lam = lam
        self.size = size
        self.generate_values()
        self.make_step()
        self.make_function()

    def generate_values(self):
        """Generate poisson values"""
        self.vals = self.poisson_distribution_value(self.size)

    def make_step(self):
        """Make step (path) from generated poisson values"""
        self.step_vals = np.cumsum(self.vals)

    def make_function(self):
        """Make function - dict
        where key in integers from x value,
        value - current iteration no, ie y value
        """
        result = {}
        x0 = 0
        for i, x in enumerate(self.step_vals):
            vals_range = xrange(x0, x)
            for k in vals_range:
                result[k] = i
            x0 = x
        self.function = result

    def get_delta(self, index):
        """return  delta between current index and previous"""
        return  self.function[index] - self.function[index-1]

    def poisson_distribution_value(self, size=None):
        """return  Poisson disribution with @lam
        if size is None - return 1 value (numerical)
        otherwise return list with values with length = size
        """
        return  np.random.poisson(self.lam, size)

class EconomicModule(BaseClassConfig, EconomicModuleConfigReader):

    def __init__(self, config_module, technology_module, subside_module):
        BaseClassConfig.__init__(self, config_module)
        EconomicModuleConfigReader.__init__(self, self.start_date_project)
        self.db = Database()
        self.technology_module = technology_module
        self.subside_module = subside_module
        self.calc_config_values()
        self.calcDebtPercents()
        self.get_electricity_prices_lifetime()
        self.calc_electricity_production_lifetime()


    def calc_config_values(self): #init of the module
        self.investments = self.technology_module.getInvestmentCost() #gets the value of the whole investment from the technology module
        self.investments_monthly = OrderedDefaultdict(int)
        self.investmentEquipment = self.technology_module.getInvestmentCost() #sets the investment in equipment as the whole investment in technology
        self.debt = self.debt_share * self.investments #calculates the amount of debt based on share of debt in financing
        self.capital = self.investments - self.debt #calculates the amount of capital based on the amount of debt

    def calc_electricity_production_lifetime(self): #gets the electricty production for the whole lifetime of the project as provided by the techology module
        self.electricity_production = self.technology_module.generateElectricityProductionLifeTime()

    def get_electricity_prices_lifetime(self): #reads random time sequence of electricity market prices from database
        self.electricity_prices = self.db.get_electricity_prices(self.electricity_prices_rnd_simulation)
        if not self.electricity_prices:
            raise ValueError("Please generate first Electricity prices before using it")

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
        date_list = getListDates(date_start, date_end)

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
        cur_month = monthsBetween(self.start_date_project, date)
        deprication_duration_months = self.deprication_duration * 12

        cur_month = monthsBetween(self.last_day_construction+datetime.timedelta(days=1), date)
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
        start_date1 = lastDayMonth(addXMonths(self.first_day_construction, -2))
        self.calc_paidin_investment(start_date1, part1)

        ####### SECOND - 50% - at start of construction
        part2 = 0.5
        start_date2 = lastDayMonth(self.first_day_construction)
        self.calc_paidin_investment(start_date2, part2)

        ####### THIRD - 20% - at the end of construction
        part3 = 0.2
        start_date3 = lastDayMonth(self.last_day_construction)
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
        return self.developmentCostDuringPermitProcurement / nubmerDaysInMonth(date)

    def _getDevelopmentCostDuringConstruction(self, date):
        """costs for developing phase of project at given date (1day) - part construction"""
        return self.developmentCostDuringConstruction / nubmerDaysInMonth(date)

    def _getOperationalCosts(self, date):
        """Operational costs at given date (1day)"""
        if self.isProductionElectricityStarted(date):
            return self._getInsuranceCosts(date) + self._getAdministrativeCosts(date)
        else:
            return  0

    def _getAdministrativeCosts(self, date):
        """return administrative costs at given date (1day)"""
        yearNumber = yearsBetween1Jan(self.start_date_project, date)
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
        list_dates = getListDates(date_start, date_end)
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












