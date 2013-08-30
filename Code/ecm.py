#!/usr/bin/env python
# -*- coding utf-8 -*-

import datetime
import numpy as np

from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from annex import Annuitet, getDaysNoInMonth, yearsBetween1Jan, monthsBetween, lastDayMonth, get_list_dates, cached_property
from annex import addXMonths, nubmerDaysInMonth, getConfigs,  OrderedDefaultdict
from config_readers import MainConfig, EconomicModuleConfigReader
from base_class import BaseClassConfig
from collections import OrderedDict
from database import Database



class ElectricityMarketPriceSimulation(EconomicModuleConfigReader):
    """class for generating Electricity prices"""
    def __init__(self, period, simulations_no):
        """
        @period - list of dates from start to end
        @simulations_no - number of needed simulations
        """
        EconomicModuleConfigReader.__init__(self, period[0])
        self.period = period
        self.N = len(period)  #number of days
        self.simulations_no = simulations_no
        self.db = Database()

    def cleanPreviousData(self):
        print "Cleaning previous data"
        self.db.cleanPreviousElectricityPriceData()

    def writeElectricityPriceData(self, data):
        """writing to database Electricity Prices"""
        self.db.writeElectricityPrices(data)
        print 'Writing electricity price simulation %s' % data["simulation_no"]

    def simulate(self):
        self.cleanPreviousData()
        for simulation_no in range(1, self.simulations_no+1):
            data = self.generateOneSimulation(simulation_no)
            self.writeElectricityPriceData(data)

    def generateOneSimulation(self, simulation_no):
        """Main method for generating prices and preparing them to posting to database"""
        days_dict = OrderedDict()
        self.poisson_steps = Poisson_step(self.Lambda, size=self.N)
        prices = self.calcPriceWholePeriod(self.S0)

        for date, price in zip(self.period, prices):
            date_str = date.strftime("%Y-%m-%d")
            days_dict[date_str] = price / 1000.0
        simulation_result = {"simulation_no": simulation_no, "data": days_dict}
        return  simulation_result

    def calcJ(self):
        """Calcultation of J (normaly distibuted Jump size) as random with mean=loc and std=scale"""
        return  np.random.normal(loc=0,scale=1)  #loc means - mean, scale -std

    def calcPriceDelta(self, prev_price, iteration_no):
        """Calculated delta price (dp) based on @prev_price"""
        delta_Z = np.random.normal(loc=0, scale=0.4)
        J = self.calcJ()
        delta_q = self.poisson_steps.getDelta(iteration_no)
        delta_price = self.k * (self.theta * (1 + self.y*iteration_no/365)- prev_price) * self.dt + self.sigma * delta_Z + (J*(1 + self.y*iteration_no/365)) * delta_q
        return  delta_price

    def calcPriceWholePeriod(self, prev_price):
        """Calculate price for whole period from start date to end"""
        result = []
        for i in range(1, self.N+1):
            price = prev_price + self.calcPriceDelta(prev_price, i)
            prev_price = price
            result.append(price)
        return  result

class Poisson_step():
    """class for holding generated Poisson values"""
    def __init__(self, lam, size):
        self.lam = lam
        self.size = size
        self.generatePoissonDistributionValues()
        self.makeStep()
        self.makeFunction()

    def makeStep(self):
        """Make step (path) from generated poisson values"""
        self.step_vals = np.cumsum(self.vals)

    def makeFunction(self):
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

    def getDelta(self, index):
        """return  delta between current index and previous"""
        return  self.function[index] - self.function[index-1]

    def generatePoissonDistributionValues(self):
        """Generate poisson values
        return  Poisson disribution with @lam
        if size is None - return 1 value (numerical)
        otherwise return list with values with length = size
        """
        self.vals =  np.random.poisson(self.lam, self.size)

class EconomicModule(BaseClassConfig, EconomicModuleConfigReader):
    """Module for holding all economic values calculation"""

    def __init__(self, config_module, technology_module, subside_module):
        """
        @config_module - link to main config module
        @technology_module - link to technology module
        @subside_module - link to subside module
        """
        BaseClassConfig.__init__(self, config_module)
        EconomicModuleConfigReader.__init__(self, self.start_date_project)
        self.__electricity_production = []
        self.db = Database()
        self.technology_module = technology_module
        self.subside_module = subside_module
        self.calcBaseValues()
        self.calcDebtPercents()

    def calcBaseValues(self):
        """caclulation of initial values"""
        self.investments = self.technology_module.getInvestmentCost() #gets the value of the whole investment from the technology module
        self.investments_monthly = OrderedDefaultdict(int)
        self.investmentEquipment = self.technology_module.getInvestmentCost() #sets the investment in equipment as the whole investment in technology
        self.debt = self.debt_share * self.investments #calculates the amount of debt based on share of debt in financing
        self.capital = self.investments - self.debt #calculates the amount of capital based on the amount of debt
        self.deprication_monthly = self.investments / self.deprication_duration  #Calc monthly value for deprication

    @cached_property
    def electricity_production(self):
        return  self.technology_module.generateElectricityProductionLifeTime()

    @cached_property
    def electricity_prices(self):
        """reads random time sequence of electricity market prices from database"""
        result = self.db.getElectricityPrices(self.electricity_prices_rnd_simulation)
        if not result:
            raise ValueError("Please generate first Electricity prices before using it")
        return  result

    def getElectricityProductionLifetime(self):
        """return  all values dict [date]=electricity production for that date"""
        return  self.electricity_production

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
        return  (date > self.last_day_construction)

    def getRevenue(self, date_start, date_end):
        """return revenue from selling electricity and subsides for given period of time"""
        revenue_electricity = 0
        revenue_subside = 0
        cur_date = date_start

        for cur_date in get_list_dates(date_start, date_end):
            electricity_production = self.getElectricityProduction(cur_date)  #get electricity production at current date
            day_revenue_electricity = electricity_production * self.getPriceKwh(cur_date)  #calc revenue = price*production
            day_revenue_subsidy = electricity_production * self.subside_module.subsidyProduction(cur_date)  #calc subside

            revenue_electricity += day_revenue_electricity  #increment revenue for period  date_start - date_end
            revenue_subside += day_revenue_subsidy  #increment subside for period  date_start - date_end

        return revenue_electricity, revenue_subside


    def getElectricityProduction(self,  date):
        """return  production of electricity at given date"""
        return  self.electricity_production[date]

    def calcDepricationMonthly(self, date):
        """Calcultation of amortization in current month"""
        cur_month = monthsBetween(self.last_day_construction+datetime.timedelta(days=1), date)  #calculating number of months between last_day_construction and cur date
        if cur_month > 0 and cur_month <= self.deprication_duration:
            return self.deprication_monthly
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
        start_date1 = lastDayMonth(addXMonths(self.first_day_construction, -2))  #get start date of first step
        self.calcPaidInInvestment(start_date1, part1)  #calculation of paid-in for first step

        ####### SECOND - 50% - at start of construction
        part2 = 0.5
        start_date2 = lastDayMonth(self.first_day_construction)  # get start date of second step
        self.calcPaidInInvestment(start_date2, part2)  #calculation of paid-in for second step

        ####### THIRD - 20% - at the end of construction
        part3 = 0.2
        start_date3 = lastDayMonth(self.last_day_construction)  #get start date of third step
        self.calcPaidInInvestment(start_date3, part3)  #calculation of paid-in for third step

    def getPaidInAtDate(self, date):
        """return  current month new value of paid-in capital"""
        return  self.paid_in_monthly[date]

    def calcPaidInInvestment(self, date, part):
        """Calculation of PaidIn and Investments for every month"""
        investment_paid_in = self.calcPaidInInvestmentPart(part)
        debt_value = self.debt * part - investment_paid_in

        a = Annuitet(debt_value, self.debt_rate, self.debt_years, date)
        a.calculate()  #calculation on Annuitet

        for date, value in a.percent_payments.items():
            self.debt_percents[date] += value  #making dict [date]=total payments for cur date

        for date, value in a.rest_payments_wo_percents.items():
            self.debt_rest_payments_wo_percents[date] += value #making dict [date]=total rest payments for cur date

        self.savePaidInInvestment(investment_paid_in, debt_value, date)

    def savePaidInInvestment(self, investment_paid_in, debt_value, date):
        """saving paidin and investments for report"""
        self.investments_monthly[date] = investment_paid_in + debt_value  #saving monthly investments
        self.paid_in_monthly[date] = investment_paid_in  #saveing monthly paid-in

    def calcPaidInInvestmentPart(self, part):
        """Calculation of inverstment value for current part of payments (1,2,3)
        @part - float value [0.0-1.0] share of current part
        """
        investment_share = (1 - self.debt_share)
        invest_value = investment_share * part * self.debt  #calc investment value in $

        if self.paid_in_rest > 0:  #if we have not paid all sum

            if invest_value > self.paid_in_rest:
                self.paid_in_rest = 0  #we dont need to pay more
                invest_value = invest_value - self.paid_in_rest
            else:
                self.paid_in_rest -= invest_value  #decreses rest payments
                invest_value = self.paid_in_rest
            return  invest_value
        else:
            return 0

    def getPriceKwh(self, date):
        """return kwh price for electricity at given day"""
        return  self.electricity_prices[date]

    def _getDevelopmentCosts(self, date):
        """costs for developing phase of project at given date (1day)"""
        if self.isProductionElectricityStarted(date):
            return 0  #we have finished with development costs
        elif self.isConstructionStarted(date):
            return self._getDevelopmentCostDuringConstruction(date)  #calculate
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
        return sum([cost_function(date) for date in get_list_dates(date_start, date_end)])

    def getTaxRate(self):
        """return taxrate in float"""
        return self.tax_rate

    def getMonthlyInvestments(self, date):
        """Gets investments of current date (on month of that date)"""
        return  self.investments_monthly[date]

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












