#!/usr/bin/env python
# -*- coding utf-8 -*-

import datetime
from dateutil.relativedelta import relativedelta
import numpy as np
import random
from math import exp, log, log1p

from rm import calcStatistics
from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from annex import getDaysNoInMonth, yearsBetween1Jan, monthsBetween, lastDayMonth, get_list_dates, cached_property, \
    setupPrintProgress, isFirstDayMonth, lastDayPrevMonth, nubmerDaysInMonth, OrderedDefaultdict, \
    lastDayNextMonth, PMT, isLastDayYear, convertDictDates
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
        EconomicModuleConfigReader.__init__(self, country, start_date_project=period[0])
        self.period = period
        self.N = len(period)  #number of days
        self.simulations_no = simulations_no
        self.db = Database()
        self.country = country
        self.start_date_project = period[0]

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
        prices = self.calcPriceWholePeriod(self.S0) # save prices in MW

        for date, price in zip(self.period, prices):  #loop for date, electricity price
            date_str = date.strftime("%Y-%m-%d")
            days_dict[date_str] = price

        stats = calcStatistics(prices)
        simulation_result = {"simulation_no": simulation_no, "data": days_dict, "stats": stats}
        return simulation_result

    def calcPriceLogDeltaNoJump(self, prev_price_log, theta_log):
        """Calculates delta price (dp) based on @prev_price without a price jump"""
        #delta_Z = np.random.normal(loc=0, scale=0.9)  #random value distribution
        delta_Z = np.random.normal(loc=0, scale=self.sigma_log)

        delta_price_log = self.lambda_log * (theta_log - prev_price_log) + delta_Z
        return  delta_price_log

    def calcPriceWholePeriod(self, start_price):
        """Calculate price for whole period from start date to end - return  list with prices for all project days"""
        result = []
        y = self.makeInterannualVariabilityY()
        theta_log = self.theta_log
        prev_price_log = log(start_price)

        for i, date in enumerate(self.period):
            if date.weekday() < 5:
                price_log = prev_price_log + self.calcPriceLogDeltaNoJump(prev_price_log, theta_log)

            theta_log += log1p(y/365)
            prev_price_log = price_log
            result.append(exp(price_log))
            if isLastDayYear(date):  # recalculate y each new year
                y = self.makeInterannualVariabilityY()

        return result

    def calcJumpOld(self):
        """Calcultation of J (normaly distibuted Jump size) as random with mean=loc and std=scale
        loc means - mean, scale -std """
        return np.random.normal(loc=self.jump_size_average, scale=self.jump_size_std)

    def calcPriceDeltaNoJumpOld(self, prev_price, iteration_no, theta):
        """Calculates delta price (dp) based on @prev_price without a price jump"""
        #delta_Z = np.random.normal(loc=0, scale=0.9)  #random value distribution
        delta_Z = random.choice([-1, 1]) * exp(np.random.normal(loc=-1.31, scale=1.1) )

        delta_price = self.k * (theta - prev_price) + delta_Z
        return  delta_price

    def calcPriceDeltaWithJumpOld(self, prev_price, iteration_no, theta):
        """Calculated delta price (dp) based on @prev_price with a price jump"""

        J = self.calcJumpOld() #calculate jump

        delta_price = self.calcPriceDeltaNoJumpOld(prev_price, iteration_no, theta)  + J  #add jump to delta price
        return  delta_price

    def calcPriceWholePeriodOld(self, start_price):
        """Calculate price for whole period from start date to end - return  list with prices for all project days"""
        result = []
        date_next_jump = int(random.expovariate(self.Lambda)) #calculate the first date of price jump
        y = self.makeInterannualVariabilityY()
        theta = self.theta

        prev_price = start_price

        for i, date in enumerate(self.period):
            if date.weekday() < 5:
                if i == date_next_jump:
                    price = prev_price + self.calcPriceDeltaNoJumpOld(prev_price, i+1, theta)
                    date_next_jump += int(random.expovariate(self.Lambda)) + 1 # add one if interval is 0
                    theta = theta * (1 + y/260)
                else:
                    price = prev_price + self.calcPriceDeltaNoJumpOld(prev_price, i+1, theta)
                    theta = theta * (1 + y/260)


            prev_price = price
            result.append(price)
            if isLastDayYear(date):  # recalculate y each new year
                y = self.makeInterannualVariabilityY()

        return result

    def makeInterannualVariabilityY(self):
        """Interannual variability of y"""
        return self.y * np.random.normal(self.y_annual_mean, self.y_annual_std)


class EconomicModule(BaseClassConfig, EconomicModuleConfigReader):
    """Module for holding all economic values calculation"""

    def __init__(self, config_module, technology_module, subsidy_module, enviroment_module, country):
        """
        @config_module - link to main config module
        @technology_module - link to technology module
        @subsidy_module - link to subsidy module
        @enviroment_module - link to enviroment module
        """
        BaseClassConfig.__init__(self, config_module)  #loading Main config
        EconomicModuleConfigReader.__init__(self, country, self.start_date_project)  #loading Economic Config
        self.db = Database()  #connection to DB
        self.technology_module = technology_module
        self.subsidy_module = subsidy_module
        self.enviroment_module = enviroment_module
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
        simulations_no = 1
        period = self.all_project_dates
        price_simulation = ElectricityMarketPriceSimulation(self.country, period, simulations_no)
        data = price_simulation.generateOneSimulation(1)['data']  # generated electricity prices
        result = convertDictDates(data)
        return result

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
            electricity_price = self.getPriceMWh(cur_date)  #electricity price at cur_date
            day_revenue_electricity = electricity_production * electricity_price / 1000.0 # calc revenue = price [EUR / MWh] * production [kWh] / 1000
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

        self.debt_rest_payments_principal = OrderedDefaultdict(int)  #init container for rest_payments without percents
        self.debt_percents = OrderedDefaultdict(int)  #init container for dept percents $ value
        self.paid_in_monthly = OrderedDefaultdict(int)  #init container for paid-in monthly values in $ value

        min_payment_date = lastDayMonth(self.start_date_project)

        ####### FIRST - 30% 2 month before the start of construction
        part1 = 0.3
        start_date1 = lastDayPrevMonth(self.first_day_construction, 2)  #get start date of first step
        start_date1 = max(min_payment_date, start_date1)  # limit payment date to be inside project

        invest_value1, paid_from_initial_capital1, debt_value1 = \
            self.getInvestCaptitalDeptValues(start_date1, part1)  #calculation of paid-in for first step

        self.calcInvestmentsAndPaidIn(start_date1, invest_value1, paid_from_initial_capital1, debt_value1)

        ####### SECOND - 50% - at start of construction (end of month before contruction starts)
        part2 = 0.5
        start_date2 = lastDayPrevMonth(self.first_day_construction, 1)  # get start date of second step
        start_date2 = max(min_payment_date, start_date2)  # limit payment date to be inside project

        invest_value2, paid_from_initial_capital2, debt_value2 =\
            self.getInvestCaptitalDeptValues(start_date2, part2)  #calculation of paid-in for second step

        self.calcInvestmentsAndPaidIn(start_date2, invest_value2, paid_from_initial_capital2, debt_value2)

        ####### THIRD - 20% - at the end of construction (on next month since last_day_construction)
        part3 = 0.2
        start_date3 = lastDayNextMonth(self.last_day_construction)  #get start date of third step
        start_date3 = max(min_payment_date, start_date3)  # limit payment date to be inside project

        invest_value3, paid_from_initial_capital3, debt_value3 = \
            self.getInvestCaptitalDeptValues(start_date3, part3)  #calculation of paid-in for third step

        self.calcInvestmentsAndPaidIn(start_date3, invest_value3, paid_from_initial_capital3, debt_value3)

        ####### Calc debt and payments (interests and principal)
        # before repayment of the principal - we pay just interests
        only_percent_pairs = [
            (start_date1, debt_value1),
            (start_date2, debt_value2),
            (start_date3, debt_value3)
        ]

        #the start of repayment of the principal is delayed for specified amount of time
        first_date_principal_repayment = lastDayNextMonth(start_date3, self.delay_of_principal_repayment)
        last_date_interest_payment = lastDayPrevMonth(first_date_principal_repayment)
        principal = debt_value1 + debt_value2 + debt_value3

        # calculate self.debt_percents and self.debt_rest_payments_principal
        self.payOnlyInterests(only_percent_pairs, last_date=last_date_interest_payment)
        self.payInterestsWithPrincipal(principal, date=last_date_interest_payment)

    def getPaidInAtDate(self, date):
        """return  current month new value of paid-in capital"""
        return  self.paid_in_monthly[date]

    def getInvestCaptitalDeptValues(self, date, share):
        """Calculation of PaidIn and Investments for every month"""
        invest_value, paid_from_initial_capital = self.calcPaidInCapitalPart(share)  #Calculation of inverstment value for current part of payment
        debt_value = self.debt * share  #debt values for current investment paid-in
        return invest_value, paid_from_initial_capital, debt_value

    def calcInvestmentsAndPaidIn(self, date, invest_value, paid_from_initial_capital, debt_value):
        #saving paidin and investments for report
        self.investments_monthly[date] += invest_value + debt_value  # saving+updating monthly investments
        self.paid_in_monthly[date] += invest_value - paid_from_initial_capital  # saving+updating monthly paid-in

    def payOnlyInterests(self, only_percent_pairs, last_date):
        """Pay only interest payments until @last_date"""
        current_dept = 0
        for date in self.report_dates.values():
            pay_interest_date = lastDayNextMonth(date)
            if pay_interest_date > last_date:   # exit , next payments will be with payInterestsWithPrincipal
                return

            for debt_date, value in only_percent_pairs:
                if date == debt_date:
                    current_dept += value  # calculate total dept at current date

            debt_interest = current_dept * self.debt_rate / 12  # calculate monthly interest
            self.debt_percents[pay_interest_date] += debt_interest  # increasing debt_percents [date] += percent payments for cur date
            self.debt_rest_payments_principal[date] += current_dept

    def payInterestsWithPrincipal(self, debt_value, date):
        # short links to principal_repayment in calculations calculation
        ppm = PMT(debt_value, yrate=self.debt_rate, yperiods=self.debt_years, date=date)
        ppm.calculate()

        for debt_date, value in ppm.percent_payments.items():
            self.debt_percents[debt_date] += value   # increasing debt_percents [date] += percent payments for cur date

        for debt_date, value in ppm.rest_payments_wo_percents.items():
            self.debt_rest_payments_principal[debt_date] += value  # increasing debt_rest_payments_principal [date]

    def calcPaidInCapitalPart(self, part):
        """return  inverstment value for current part of payments (1,2,3)
        @part - float value [0.0-1.0] share of current part
        """
        capital_share = (1 - self.debt_share)
        capital_value = capital_share * part * self.investments  #calc investment value in $

        if self.paid_in_rest > 0:  #if we have not paid all sum

            if capital_value > self.paid_in_rest:
                paid_from_initial_capital = self.paid_in_rest
                self.paid_in_rest = 0  #we dont need to pay more
            else:
                paid_from_initial_capital = capital_value
                self.paid_in_rest -= capital_value  #decreses rest payments
        else:
            paid_from_initial_capital = 0

        return capital_value, paid_from_initial_capital

    @cached_property
    def actual_electricity_prices(self):
        """All logic of electricity price calculation"""
        prices = OrderedDict()
        subsidy_start, subsidy_end = self.subsidy_module.first_day_subsidy, self.subsidy_module.last_day_subsidy
        contract_prices = list(reversed(self.contract_electricity_prices.items()))
        electricity_price_first_day_constuction = self.electricity_prices[self.first_day_construction]

        for date in self.all_project_dates:
            if date < subsidy_start:
                # period before subsidy - take price on the 1 day of production
                prices[date] = electricity_price_first_day_constuction
            elif date >= subsidy_start and date <= subsidy_end:
                prices[date] = self.subsidy_module.kWhFIT  # if we have FIT - take it
            else:
                # else take current contract price
                for d, p in contract_prices:  # contract in reversed by date order
                    if date >= d:
                        prices[date] = p
                        break

        return prices

    @cached_property
    def contract_electricity_prices(self):
        prices = OrderedDict()
        new_price_start_date = self.subsidy_module.last_day_subsidy + relativedelta(days=1)
        while new_price_start_date <= self.end_date_project:
            new_price_sign_date = new_price_start_date - relativedelta(months=3) - relativedelta(days=1)
            price_at_sign_date = self.electricity_prices[new_price_sign_date]
            prices[new_price_start_date] = price_at_sign_date

            next_year = new_price_start_date.year + 1
            try:
                new_price_start_date = new_price_start_date.replace(year=next_year)
            except:
                new_price_start_date = new_price_start_date.replace(
                    year=next_year, day=new_price_start_date.day - 1)
        return prices

    def getPriceMWh(self, date):
        """return MWh price for electricity at given day"""
        return self.actual_electricity_prices[date]

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
            costs = self.getInsuranceCost(date) + self._getAdministrativeCosts(date)  #sum of INSURANCE COSTS and AMDINISTR COSTS at given date
            if date == self.end_date_project:
                # at the last month of operation add costs for equimpent disposal
                costs += self.enviroment_module.getEquipmentDisposalCosts()
            return costs
        return 0

    def _getAdministrativeCosts(self, date):
        """return administrative costs at given date (1day)"""
        yearNumber = yearsBetween1Jan(self.start_date_project, date)  #nuber of current year since start project
        #we increase initial administrativeCosts each year on administrativeCostsGrowth_rate
        return self.administrativeCosts * ((1 + self.administrativeCostsGrowth_rate) ** yearNumber) / getDaysNoInMonth(date)

    def getInsuranceCost(self, date):
        """return insurance costs at give date (1day) because it is fixed value, we calculate it only one time
        Isurance can be only after starting production electricity and before end of insurance"""
        if self.isProductionElectricityStarted(date) and date <= self.insuranceLastDayEquipment:
            return self.insuranceFeeEquipment * self.investments / 365  #deviding by 365 days in year
        else:
            return 0

    def getCosts(self, date_start, date_end):
        """sum of costs for all days in RANGE period"""
        return self.getDevelopmentCosts(date_start, date_end) + self.getOperationalCosts(date_start, date_end)

    def getDevelopmentCosts(self, date_start, date_end):
        """sum of Development Costs for all days in RANGE period"""
        return self.getSomeCostsRange(self._getDevelopmentCosts, date_start, date_end)

    def getDevelopmentCostDuringPermitProcurement(self, date_start, date_end):
        """sum of Development Cost DuringPermitProcurement for all days in RANGE period"""
        return self.getSomeCostsRange(self._getDevelopmentCostDuringPermitProcurement, date_start, date_end)

    def getDevelopmentCostDuringConstruction(self, date_start, date_end):
        """sum of Development Cost DuringConstruction for all days in RANGE period"""
        return self.getSomeCostsRange(self._getDevelopmentCostDuringConstruction, date_start, date_end)

    def getOperationalCosts(self, date_start, date_end):
        """sum of Operational Costs for all days in RANGE period"""
        return self.getSomeCostsRange(self._getOperationalCosts, date_start, date_end)

    def getAdministrativeCosts(self, date_start, date_end):
        """sum of Administrative Costs for all days in RANGE period"""
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
        return  self.debt_rest_payments_principal.get(date, 0)

if __name__ == '__main__':
    country = 'SLOVENIA'
    mainconfig = MainConfig(country)
    em = EnergyModule(mainconfig, country)
    technology_module = TechnologyModule(mainconfig, em, country)
    subsidy_module = SubsidyModule(mainconfig, country)

    ecm = EconomicModule(mainconfig, technology_module, subsidy_module, country)
    print ecm.investments_monthly
    print sum(ecm.investments_monthly.values())
