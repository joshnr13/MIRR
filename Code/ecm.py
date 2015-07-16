#!/usr/bin/env python
# -*- coding utf-8 -*-

import datetime
import numpy as np
from rm import calcStatistics

from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from annex import Annuitet, getDaysNoInMonth, yearsBetween1Jan, monthsBetween, lastDayMonth, get_list_dates, cached_property, \
    setupPrintProgress, isFirstDayMonth, lastDayPrevMonth, nubmerDaysInMonth, OrderedDefaultdict, \
    lastDayNextMonth
from config_readers import MainConfig, EconomicModuleConfigReader
from base_class import BaseClassConfig
from collections import OrderedDict
from database import Database


class ElectricityMarketPriceSimulation(EconomicModuleConfigReader):
    """class for generating Electricity prices"""
    def __init__(self, country, period, simulations_no):
        """
        @period - list of dates from start to end
        @simulations_no - number of needed simulations
        """
        self.period = period
        self.N = len(period)  #number of days
        self.simulations_no = simulations_no
        self.start_date_project = self.period[0]
        self.db = Database()
        self.country = country

    def cleanPreviousData(self):
        print "Cleaning previous ElectricityPriceData for %r" % self.country
        self.db.cleanPreviousElectricityPriceData(self.country)  #before each Simulatation, we should clean previous data

    def writeElectricityPriceData(self, data, silent=True):
        """writing to database Electricity Prices"""
        data['country'] = self.country
        self.db.writeElectricityPrices(data)
        if not silent:
            print 'Writing electricity price simulation %s' % data["simulation_no"]

    def simulate(self):
        print_progress = setupPrintProgress('%d')
        self.cleanPreviousData() #before each Simulatation, we should clean previous data
        for simulation_no in range(1, self.simulations_no+1):  #loop for simulations numbers starting from 1
            # re-loading EconomicModule Configs, with passing start date of project
            # self.y will have new value each time
            EconomicModuleConfigReader.__init__(self, self.country, start_date_project=self.start_date_project)
            data = self.generateOneSimulation(simulation_no)  #generating each simulation
            self.writeElectricityPriceData(data)  #writing each simulation to DB
            print_progress(simulation_no)  # print progress bar with simulation_no
        print_progress(stop=True)

    def generateOneSimulation(self, simulation_no):
        """Main method for generating prices and preparing them to posting to database"""
        days_dict = OrderedDict()
        self.poisson_steps = Poisson_step(self.Lambda, size=self.N)
        prices = self.calcPriceWholePeriod(self.S0)
        prices = [p/1000.0 for p in prices]  # because price in configs for MEGAWT

        for date, price in zip(self.period, prices):  #loop for date, electricity price
            date_str = date.strftime("%Y-%m-%d")
            days_dict[date_str] = price

        stats = calcStatistics(prices)
        simulation_result = {"simulation_no": simulation_no, "data": days_dict, "stats": stats}
        return simulation_result

    def calcJ(self):
        """Calcultation of J (normaly distibuted Jump size) as random with mean=loc and std=scale"""
        return  np.random.normal(loc=0,scale=1)  #loc means - mean, scale -std

    def calcPriceDelta(self, prev_price, iteration_no, y):
        """Calculated delta price (dp) based on @prev_price"""
        delta_Z = np.random.normal(loc=0, scale=0.4)  #random value distribution
        J = self.calcJ()
        delta_q = self.poisson_steps.getDelta(iteration_no)

        # formulat 2.2 from book
        delta_price = self.k * (self.theta * (1 + y * iteration_no / 365) - prev_price) * self.dt + \
                      self.sigma * delta_Z + (J * (1 + y * iteration_no / 365)) * delta_q
        return  delta_price

    def calcPriceWholePeriod(self, prev_price):
        """Calculate price for whole period from start date to end - return  list with prices for all project days"""
        result = []
        y = self.makeInterannualVariabilityY()
        for i, date in enumerate(self.period):
            if isFirstDayMonth(date):  # recalculate y for each new month
                y = self.makeInterannualVariabilityY()
            price = prev_price + self.calcPriceDelta(prev_price, i+1, y)
            prev_price = price
            result.append(price)
        return result

    def makeInterannualVariabilityY(self):
        """interannual variability of y"""
        return self.y * np.random.normal(self.y_annual_mean, self.y_annual_std)


class Poisson_step():
    """class for holding generated Poisson values"""
    def __init__(self, lam, size):
        self.lam = lam  #Lambda
        self.size = size  #number of values
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

    def __init__(self, config_module, technology_module, subsidy_module, country):
        """
        @config_module - link to main config module
        @technology_module - link to technology module
        @subsidy_module - link to subsidy module
        """
        BaseClassConfig.__init__(self, config_module)  #loading Main config
        EconomicModuleConfigReader.__init__(self, country, self.start_date_project)  #loading Economic Config
        self.db = Database()  #connection to DB
        self.technology_module = technology_module
        self.subsidy_module = subsidy_module
        self.country = country
        self.investments_monthly = OrderedDefaultdict(int)
        self.calcBaseValues()
        self.calcInvestmentAndFinancing()

    def calcBaseValues(self):
        """caclulation of initial values"""
        self.investments = self.technology_module.getInvestmentCost() #gets the value of the whole investment from the technology module
        self.debt = self.debt_share * self.investments #calculates the amount of debt based on share of debt in financing
        self.capital = self.investments - self.debt #calculates the amount of capital based on the amount of debt
        self.Depreciation_monthly = self.investments / self.Depreciation_duration  #Calc monthly value for Depreciation

    @cached_property
    def electricity_production(self):
        """This is cached attribute, it is calculated only one time per session"""
        return  self.technology_module.generateElectricityProductionLifeTime()

    @cached_property
    def electricity_prices(self):
        """This is cached attribute, it is calculated only one time per session
        reads random time sequence of electricity market prices from database"""
        result = self.db.getElectricityPrices(self.electricity_prices_rnd_simulation,
                                              country=self.country)
        if not result:
            raise ValueError("Please generate first Electricity prices before using it")
        return  result

    def getElectricityProductionLifetime(self):
        """return  all values dict [date]=electricity production for that date"""
        return  self.electricity_production

    def isConstructionStarted(self, date):
        """return  True if we recieved all permits and started but not finished construction of equipment"""
        return  (date > self.last_day_permit_procurement and date <= self.last_day_construction)

    def isProductionElectricityStarted(self, date):
        """return  True if we recieved all permits, finished construction and can
        sell electricity"""
        return  (date > self.last_day_construction)

    def getRevenue(self, date_start, date_end):
        """return revenue from selling electricity and subsidy for given period of time"""
        revenue_electricity = 0
        revenue_subsidy = 0
        cur_date = date_start

        for cur_date in get_list_dates(date_start, date_end):  # loop for user defined date range
            electricity_production = self.getElectricityProduction(cur_date)  #get electricity production at current date
            electricity_price = self.getPriceKwh(cur_date)  #electricity price at cur_date
            day_revenue_electricity = electricity_production * electricity_price  #calc revenue = price * production
            revenue_electricity += day_revenue_electricity  #increment revenue for period  date_start - date_end
        
        return revenue_electricity, revenue_subsidy

    def getElectricityProduction(self,  date):
        """return  production of electricity at given date"""
        return  self.electricity_production[date]

    def calcDepreciationMonthly(self, date):
        """Calcultation of amortization in current month"""
        cur_month = monthsBetween(self.last_day_construction+datetime.timedelta(days=1), date)  #calculating number of months between last_day_construction and cur date
        if cur_month > 0 and cur_month <= self.Depreciation_duration:
            return self.Depreciation_monthly
        else:
            return 0

    def calcInvestmentAndFinancing(self):
        """The investment is spread as follows:
             30% - 2 month before the start of construction
             50% - at start of construction
             20% - at the end of construction
        """
        self.paid_in_rest = self.initial_paid_in_capital  #initial value of paid_in, this will be shared

        self.debt_rest_payments_wo_percents = OrderedDefaultdict(int)  #init container for rest_payments without percents
        self.debt_percents = OrderedDefaultdict(int)  #init container for dept percents $ value
        self.paid_in_monthly = OrderedDefaultdict(int)  #init container for paid-in monthly values in $ value

        min_payment_date = lastDayMonth(self.start_date_project)

        ####### FIRST - 30% 2 month before the start of construction
        part1 = 0.3
        start_date1 = lastDayPrevMonth(self.first_day_construction, 2)  #get start date of first step
        start_date1 = max(min_payment_date, start_date1)  # limit payment date to be inside project
        self.calcPaidInCapitalDebtInvestment(start_date1, part1)  #calculation of paid-in for first step

        ####### SECOND - 50% - at start of construction (end of month before contruction starts)
        part2 = 0.5
        start_date2 = lastDayPrevMonth(self.first_day_construction, 1)  # get start date of second step
        start_date2 = max(min_payment_date, start_date2)  # limit payment date to be inside project
        self.calcPaidInCapitalDebtInvestment(start_date2, part2)  #calculation of paid-in for second step

        ####### THIRD - 20% - at the end of construction (on next month since last_day_construction)
        part3 = 0.2
        start_date3 = lastDayNextMonth(self.last_day_construction)  #get start date of third step
        start_date3 = max(min_payment_date, start_date3)  # limit payment date to be inside project
        self.calcPaidInCapitalDebtInvestment(start_date3, part3)  #calculation of paid-in for third step

    def getPaidInAtDate(self, date):
        """return  current month new value of paid-in capital"""
        return  self.paid_in_monthly[date]

    def calcPaidInCapitalDebtInvestment(self, date, share):
        """Calculation of PaidIn and Investments for every month"""
        capital_paid_in = self.calcPaidInCapitalPart(share)  #Calculation of inverstment value for current part of payment
        debt_value = self.debt * share  #debt values for current investment paid-in

        #saving paidin and investments for report
        self.investments_monthly[date] += capital_paid_in + debt_value  # saving+updating monthly investments
        self.paid_in_monthly[date] += capital_paid_in  # saving+updating monthly paid-in

        a = Annuitet(debt_value, self.debt_rate, self.debt_years, date)
        a.calculate()  #calculation on Annuitet

        percent_payments_with_dates = a.percent_payments.items()  #short links to annuitet calculation
        debt_rest_payments_with_dates = a.rest_payments_wo_percents.items() #short links to annuitet calculation

        for debt_date, value in percent_payments_with_dates:
            self.debt_percents[debt_date] += value  #increasing debt_percents [date] += percent payments for cur date

        for debt_date, value in debt_rest_payments_with_dates:
            self.debt_rest_payments_wo_percents[debt_date] += value #increasing debt_rest_payments_wo_percents [date] += debt rest payments for cur date

    def calcPaidInCapitalPart(self, part):
        """return  inverstment value for current part of payments (1,2,3)
        @part - float value [0.0-1.0] share of current part
        """
        capital_share = (1 - self.debt_share)
        capital_value = capital_share * part * self.investments  #calc investment value in $

        if self.paid_in_rest > 0:  #if we have not paid all sum

            if capital_value > self.paid_in_rest:
                self.paid_in_rest = 0  #we dont need to pay more
            else:
                self.paid_in_rest -= capital_value  #decreses rest payments
            return capital_value
        else:
            return capital_value

    def getPriceKwh(self, date):
        """return kwh price for electricity at given day"""
        fit = self.subsidy_module.valueOfFeedInTarrifPerkWh(date)
        if fit == 0 :
           return  self.electricity_prices[date]     #if FIT is zero, take market price else take FIT
        else :
           return  fit


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
            return self.insuranceCosts + self._getAdministrativeCosts(date)  #sum of INSURANCE COSTS and AMDINISTR COSTS at given date
        return  0

    def _getAdministrativeCosts(self, date):
        """return administrative costs at given date (1day)"""
        yearNumber = yearsBetween1Jan(self.start_date_project, date)  #nuber of current year since start project
        #we increase initial administrativeCosts each year on administrativeCostsGrowth_rate
        return self.administrativeCosts * ((1 + self.administrativeCostsGrowth_rate) ** yearNumber) / getDaysNoInMonth(date)

    @cached_property
    def insuranceCosts(self):
        """return insurance costs at give date (1day)
        because it is fixed value, we calculate it only one time"""
        return self.insuranceFeeEquipment * self.investments / 365  #deviding by 365 days in year

    def getCosts(self, date_start, date_end):
        """sum of costs for all days in RANGE period """
        return self.getDevelopmentCosts(date_start, date_end) + self.getOperationalCosts(date_start, date_end)

    def getInsuranceCosts(self, date_start, date_end):
        """sum of Insurance Costs for all days in RANGE period """
        return self.insuranceCosts * (date_end - date_start).days

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
    country = 'SLOVENIA'
    mainconfig = MainConfig(country)
    em = EnergyModule(mainconfig, country)
    technology_module = TechnologyModule(mainconfig, em, country)
    subsidy_module = SubsidyModule(mainconfig, country)

    ecm = EconomicModule(mainconfig, technology_module, subsidy_module, country)
    print ecm.investments_monthly
    print sum(ecm.investments_monthly.values())
