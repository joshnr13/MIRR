#!/usr/bin/env python
# -*- coding utf-8 -*-
import numpy
from collections import  OrderedDict
from annex import lastDayMonth, cached_property, lastDayPrevMonth
from annex import isLastDayYear, OrderedDefaultdict
from annex import getOnlyDigits, sameDayLastYear, get_list_dates
from financial_analysis import npvPv, CashFlows
from constants import PROJECT_START
from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from ecm import EconomicModule
from base_class import BaseClassConfig
from config_readers import MainConfig


class Report(BaseClassConfig):
    """Module for calculating Balance, FCF"""
    def __init__(self, config_module, economic_module, iteration_no=None, simulation_no=None):
        """input
        @config_module - link to config module
        @economic_module - link to economic module
        """
        self.iteration_no = iteration_no
        self.simulation_no = simulation_no
        BaseClassConfig.__init__(self, config_module)  #loading Main configs
        self.economic_module = economic_module
        self.technology_module = economic_module.technology_module  #creating short link to TM
        self.subsidy_module = economic_module.subsidy_module #creating short link to SM
        self.energy_module = self.technology_module.energy_module #creating short link to EM

    def calcReportValues(self):
        """Main function to cacl all values for reports"""
        self.initAttrs()  #creating main containers for values
        self.initHelperAttrs()  #creating helper containers for values
        self.initFCFArgs()  #creating containers for FCF

        for start_day, end_day in self.report_dates.items():  #loop for monthly datas - start day month and end date month
            self.calcMonthlyValuesPart1(start_day, end_day)  #calc first part of monthly report values which depends on START and END date of month
            if isLastDayYear(end_day):
                self.calcYearlyValuesPart1(end_day)  #and if date=last_day in year - also calc first part of yearly report values
            self.calcMonthlyValuesPart2(end_day)  #calculate second part of report stats, which depends only on END day month
            self.calcHelperValuesMonthly(end_day)  #calc helper values for proper FCF calculation
            self.calcFCFMonthly(end_day)  #calc FCF values (monthly only)
            self.checkBalanceSheet(end_day)  #cacl Balance checked, which should be 0 for all columns

            if isLastDayYear(end_day):  #and if date=last_day in year - also calc
                self.calcYearlyValuesPart2(end_day)  #Yearly report values part2
                self.calcYearlyValuesPart3(end_day)  #Yearly report values part3

        self.calcIRR()  #after all calculation of IRR, WACC, NPV values based on FCF
        self.calcWACC()
        self.calcNPV()

    def startProjectOrderedDict(self, name=PROJECT_START, value=""):
        """prepare OrderedDict"""
        return OrderedDict({name: value,})  #return Ordered dict with first key = name and value

    def startProjectOrderedDefaultdict(self, name=PROJECT_START, value=""):
        """prepare Ordered Default Dict"""
        return  OrderedDefaultdict(int, {name: value,}) #return Ordered Default INT =0 dict with first key = name and value

    def initAttrs(self):
        """Creating attrs for monthly and yearly values"""
        capital = self.economic_module.initial_paid_in_capital

        ################## SECOND SHEET ###############################
        self.sun_insolation = self.startProjectOrderedDict(name="",value="")  #sum of monthy  sun insolations
        self.sun_insolation_y = self.startProjectOrderedDefaultdict(name="",value="")  #sum of yearly  sun insolations

        self.electricity_production = self.startProjectOrderedDict(name="",value="")  #sum of monthy  electricity production
        self.electricity_production_y = self.startProjectOrderedDefaultdict(name="",value="")  #sum of yearly  electricity production

        self.electricity_prices = self.startProjectOrderedDict(name="",value="")  #yearly electricity prices from start project
        self.electricity_prices_y = self.startProjectOrderedDefaultdict(name="",value="")  #monthly electricity prices from start project

        ################### IS ########################################
        self.revenue = self.startProjectOrderedDict(name=PROJECT_START,value="")  #all revenue
        self.revenue_electricity = self.startProjectOrderedDict(name=PROJECT_START,value="")  #revenue -part electricity
        self.revenue_subsidy = self.startProjectOrderedDict(name=PROJECT_START,value="")  #revenue - part subsidy
        self.cost = self.startProjectOrderedDict(name=PROJECT_START,value="")  #costs
        self.operational_cost = self.startProjectOrderedDict(name=PROJECT_START,value="")  # operational costs
        self.development_cost = self.startProjectOrderedDict(name=PROJECT_START,value="")  #development costs
        self.ebitda = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.ebit = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.ebt = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.iterest_paid = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.depreciation = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.tax = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.net_earning = self.startProjectOrderedDict(name=PROJECT_START,value=0)

        ################### BS ########################################
        self.investment = self.startProjectOrderedDict(name=PROJECT_START,value=0)
        self.fixed_asset = self.startProjectOrderedDict(name=PROJECT_START,value=0)
        self.asset = self.startProjectOrderedDict(name=PROJECT_START,value=capital)
        self.inventory = self.startProjectOrderedDict(name=PROJECT_START,value=0)
        self.operating_receivable = self.startProjectOrderedDict(name=PROJECT_START,value=0)
        self.short_term_investment = self.startProjectOrderedDict(name=PROJECT_START,value=0)
        self.asset_bank_account = self.startProjectOrderedDict(name=PROJECT_START,value=capital)
        self.paid_in_capital = self.startProjectOrderedDict(name=PROJECT_START,value=capital)
        self.current_asset = self.startProjectOrderedDict(name=PROJECT_START,value=0)
        self.retained_earning = self.startProjectOrderedDict(name=PROJECT_START,value=0)
        self.unallocated_earning = self.startProjectOrderedDict(name=PROJECT_START,value=0)
        self.retained_earning = self.startProjectOrderedDict(name=PROJECT_START,value=0)
        self.financial_operating_obligation = self.startProjectOrderedDict(name=PROJECT_START,value=0)
        self.long_term_loan = self.startProjectOrderedDict(name=PROJECT_START,value=0)
        self.short_term_loan = self.startProjectOrderedDict(name=PROJECT_START,value=0)
        self.long_term_operating_liability = self.startProjectOrderedDict(name=PROJECT_START,value=0)
        self.short_term_debt_suppliers = self.startProjectOrderedDict(name=PROJECT_START,value=0)
        self.liability = self.startProjectOrderedDict(name=PROJECT_START,value=capital)
        self.equity = self.startProjectOrderedDict(name=PROJECT_START,value=capital)
        self.control = self.startProjectOrderedDict(name=PROJECT_START,value="")

        ################### IS-Y #######################################
        self.revenue_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.revenue_electricity_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.revenue_subsidy_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.cost_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.operational_cost_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.development_cost_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.ebitda_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.ebit_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.ebt_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.iterest_paid_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.depreciation_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.tax_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.net_earning_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")

        ################### BS-Y #######################################
        self.investment_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=0)
        self.fixed_asset_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=0)
        self.asset_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=capital)
        self.inventory_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=0)
        self.operating_receivable_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=0)
        self.short_term_investment_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=0)
        self.asset_bank_account_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=0)
        self.paid_in_capital_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=capital)
        self.current_asset_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=capital)
        self.retained_earning_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=0)
        self.unallocated_earning_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=0)
        self.retained_earning_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=0)
        self.financial_operating_obligation_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=0)
        self.long_term_loan_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=0)
        self.short_term_loan_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=0)
        self.long_term_operating_liability_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=0)
        self.short_term_debt_suppliers_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=0)
        self.liability_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=capital)
        self.equity_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value=capital)
        self.control_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")

    def initFCFArgs(self):
        """Creating attrs for FCF calculation"""
        self.fcf_project = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.fcf_owners = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.fcf_project_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.fcf_owners_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")

    def initHelperAttrs(self):
        """Initing helper args to calculate correct BS"""
        self.hlp = OrderedDict()
        self.decr_st_loans = OrderedDict()
        self.decr_bank_assets = OrderedDict()
        self.hlp_y = OrderedDefaultdict(int)
        self.decr_st_loans_y = OrderedDefaultdict(int)
        self.decr_bank_assets_y = OrderedDefaultdict(int)

    def calcMonthlyValuesPart1(self, start_day, end_day):
        """Main function to calc montly value for reports P1"""
        M = end_day
        rev_electricity, rev_subsidy = self.economic_module.getRevenue(start_day, end_day)  #revenue for current month

        self.revenue_electricity[M], self.revenue_subsidy[M] = rev_electricity, rev_subsidy
        self.revenue[M] = rev_electricity + rev_subsidy

        self.electricity_production[M] = self.electricity_monthly[M]
        self.sun_insolation[M] = self.solar_insolations_monthly[M]
        self.electricity_prices[M] = self.electricity_prices_monthly[M]

        self.depreciation[M] = self.economic_module.calcDepreciationMonthly(end_day)
        self.iterest_paid[M] = self.economic_module.calculateDebtInterests(end_day)

        self.development_cost[M] = self.economic_module.getDevelopmentCosts(start_day, end_day)
        self.operational_cost[M] = self.economic_module.getOperationalCosts(start_day, end_day)
        self.cost[M] = self.economic_module.getCosts(start_day, end_day)

        self.ebitda[M] = self.calcEbitda(end_day)
        self.ebit[M] = self.calcEbit(end_day)
        self.ebt[M] = self.calcEbt(end_day)

    def calcMonthlyValuesPart2(self, end_day):
        """Main function to calc montly value for reports P2"""
        M = end_day

        self.tax[M] = self.calcTax(end_day)
        self.net_earning[M] = self.calcNetEarning(end_day)

        self.investment[M] = self.economic_module.getMonthlyInvestments(end_day)
        self.fixed_asset[M] = self.calcFixedAssets(end_day)

        self.operating_receivable[M] = self.calcOperatingReceivable(end_day)
        self.inventory[M] = 0 #NOT IMPLEMENTED
        self.short_term_investment[M] = 0 #NOT IMPLEMENTED
        self.asset_bank_account[M] = 0 #NOT IMPLEMENTED
        self.paid_in_capital[M] = self.calcPaidIn(M)

        self.current_asset[M] = self.calcCurrentAssets(M)
        self.retained_earning[M] = self.net_earning[M]
        self.unallocated_earning[M] = self.calcUnallocatedEarnings(M)
        self.asset[M] = self.calcAssets(end_day)

        self.long_term_loan[M] = self.calcLtLoans(end_day)
        self.long_term_operating_liability[M] = self.calcLtOperLiab(end_day)
        self.short_term_loan[M] = self.calcStLoans(end_day)
        self.short_term_debt_suppliers[M] = self.calcShortTermDebtSuppliers(end_day)

        self.financial_operating_obligation[M] = self.calcFinancialOperatingObligations(end_day)
        self.equity[M] = self.calcEquity(end_day)
        self.liability[M] = self.calcLiabilities(end_day)

    def calcYearlyValuesPart1(self, end_day_y):
        """Main function to calc yearly value for reports P1
           increasing current year values each month by month value
           summing every month value
        """
        assert len(self.report_dates_y[end_day_y]) <= 12, "simple check thay Y data has <= 12 M"
        for start_day_m, end_day_m in self.report_dates_y[end_day_y]:  #loop for all months in current year
            Y = end_day_y
            M = end_day_m

            self.revenue_electricity_y[Y] += self.revenue_electricity[M]
            self.revenue_subsidy_y[Y] += self.revenue_subsidy[M]
            self.revenue_y[Y] += self.revenue[M]

            self.depreciation_y[Y] += self.depreciation[M]
            self.iterest_paid_y[Y] += self.iterest_paid[M]
            self.cost_y[Y] += self.cost[M]
            self.development_cost_y[Y] += self.development_cost[M]
            self.operational_cost_y[Y] += self.operational_cost[M]

            self.ebitda_y[Y] += self.ebitda[M]
            self.ebit_y[Y] += self.ebit[M]
            self.ebt_y[Y] += self.ebt[M]

    def calcYearlyValuesPart2(self, end_day_y):
        """Main function to calc yearly value for reports P2
        Start calculating when all month values for current year is calculated
        """

        for start_day_m, end_day_m in self.report_dates_y[end_day_y]: #loop for all months in current year
            Y = end_day_y
            M = end_day_m

            ############## SUM #################
            self.net_earning_y[Y] += self.net_earning[M]
            self.tax_y[Y] += self.tax[M]
            self.retained_earning_y[Y] += self.retained_earning[M]
            self.fcf_owners_y[Y] += self.fcf_owners[M]
            self.fcf_project_y[Y] += self.fcf_project[M]

            self.electricity_production_y[Y] += self.electricity_production[M]
            self.sun_insolation_y[Y] += self.sun_insolation[M]

            ############### NOT USED
            self.inventory_y[Y] += self.inventory[M]
            self.investment_y[Y] += self.investment[M]
            self.long_term_operating_liability_y[Y] += self.long_term_operating_liability[M]

    def calcYearlyValuesPart3(self, end_day_y):
        """Main function to calc yearly value for reports P2
        In this part yearly values = last month values
        """

        Y = end_day_y
        Y1 =  sameDayLastYear(end_day_y)#previous_year

        ########### LAST MONTH ###############
        self.electricity_prices_y[Y] = self.electricity_prices[Y]
        self.fixed_asset_y[Y] = self.fixed_asset[Y]
        self.current_asset_y[Y] = self.current_asset[Y]
        self.operating_receivable_y[Y] =  self.operating_receivable[Y]
        self.asset_bank_account_y[Y] = self.asset_bank_account[Y]
        self.asset_y[Y] = self.asset[Y]
        self.equity_y[Y] = self.equity[Y]
        self.paid_in_capital_y[Y] = self.paid_in_capital[Y]
        self.long_term_loan_y[Y] =self.long_term_loan[Y]
        self.short_term_loan_y[Y] =self.short_term_loan[Y]
        self.short_term_debt_suppliers_y[Y] = self.short_term_debt_suppliers[Y]
        self.financial_operating_obligation_y[Y] =self.financial_operating_obligation[Y]
        self.liability_y[Y] = self.liability[Y]

        prev_un_er =  self.unallocated_earning_y[Y1] if Y1 >= self.start_date_project else 0
        prev_ret_er =  self.retained_earning_y[Y1] if Y1 >= self.start_date_project else 0
        self.unallocated_earning_y[Y] = prev_un_er + prev_ret_er
        self.control_y[Y] = self.asset_y[Y] - self.liability_y[Y]

    def calcReportMonthlyValues1(self, func):
        """Calculates monthly values using 1 date - last_day in month
        return  dict[end_day] = value"""
        return OrderedDict((end_day, func(end_day)) for end_day in self.report_dates.values())

    def calcReportMonthlyValues2(self, func):
        """Calculates monthly values using 2 dates -first_day and last_day in month
        return  dict[end_day] = value
        """
        return OrderedDict((end_day, func(start_day, end_day)) for start_day, end_day in self.report_dates.items())

    def calcReportMonthlyValues3(self, dic):
        """Calculates monthly values using 2 dates -first_day and last_day in month
        return  dict[end_day] = value base on dict with all dates
        """
        results = OrderedDict()
        for start_day, end_day in self.report_dates.items():
            results[end_day] = sum([dic[date] for date in get_list_dates(start_day, end_day)])
        return results

    def calcReportMonthlyValues4(self, dic):
        """Calculates monthly values using 2 dates -first_day and last_day in month
        return  dict[end_day] = value base on dict with all dates
        """
        return OrderedDict((end_day, dic[end_day]) for end_day in self.report_dates.values())

    def getPrevMonthValue(self, obj, date):
        """Get previous month value of @obj with current date @date"""
        pM = lastDayPrevMonth(date)
        if pM < self.start_date_project:
            pM = PROJECT_START
        return obj[pM]

    def getDeltaCurPrev(self,  obj, date):
        """Calculates delta between current month value and previous month value"""
        cur = obj[date]
        prev = self.getPrevMonthValue(obj, date)
        return cur - prev

    def calcHelperValuesMonthly(self, end_day):
        """Calculating of helper values for report monthly"""
        M = end_day
        MIN_OST = 500
        prev_asset_bank_account = self.getPrevMonthValue(self.asset_bank_account, M)  #prev month assest on bank account
        prev_short_term_loan = self.getPrevMonthValue(self.short_term_loan, M) #prev short term loans

        #helper formula
        help = (self.fixed_asset[M] +
                      self.operating_receivable[M] +
                      self.short_term_investment[M] -
                      self.equity[M] -
                      self.long_term_loan[M] -
                      self.short_term_debt_suppliers[M] +
                      prev_asset_bank_account -
                      prev_short_term_loan
                      )
        self.hlp[M] = help

        if self.hlp[M] > 0:
            self.decr_bank_assets[M] = min(help,prev_asset_bank_account-MIN_OST)
            self.decr_st_loans[M] =  min(prev_short_term_loan, -help + max(self.decr_bank_assets[M], 0))
        else:
            self.decr_st_loans[M] = min(prev_short_term_loan, -help)
            self.decr_bank_assets[M] = (help + self.decr_st_loans[M])

        self.short_term_loan[M] = prev_short_term_loan - self.decr_st_loans[M]
        self.asset_bank_account[M] = prev_asset_bank_account - self.decr_bank_assets[M]

        self.current_asset[M] = self.calcCurrentAssets(end_day)
        self.asset[M] = self.calcAssets(end_day)

        self.financial_operating_obligation[M] = self.calcFinancialOperatingObligations(end_day)
        self.liability[M] = self.calcLiabilities(end_day)

    def calcFCFMonthly(self, end_day):
        """Calculation of monthly FCF, it depends what period is now
        - first time or others"""
        M = end_day
        if M == lastDayMonth(self.start_date_project):
            #if @end_day of first month of project
            self.fcf_project[M] = (self.net_earning[M] -
                                   self.getDeltaCurPrev(self.fixed_asset, M) -
                                   self.getDeltaCurPrev(self.operating_receivable, M) +
                                   self.getDeltaCurPrev(self.short_term_debt_suppliers, M) +
                                   self.iterest_paid[M] - self.asset_bank_account[M]
                                   )

            self.fcf_owners[M] = - self.paid_in_capital[M]

        else:
            #if @end_day month > 1 from start project
            self.fcf_project[M] = (self.net_earning[M] -
                                   self.getDeltaCurPrev(self.fixed_asset, M) -
                                   self.getDeltaCurPrev(self.operating_receivable, M) +
                                   self.getDeltaCurPrev(self.short_term_debt_suppliers, M) +
                                   self.iterest_paid[M]
                                   )

            self.fcf_owners[M] = (- self.getDeltaCurPrev(self.paid_in_capital, M) +
                                  self.getDeltaCurPrev(self.asset_bank_account, M)
                                  )

    def irr(self, vals):
        """Function to calculate irr value"""
        return CashFlows(vals, self.iteration_no, self.simulation_no).irr()

    def calcIRR(self):
        """Calculating IRR for project and owners, using numpy.IRR function
        both Montly and Yearly values
        """
        fcf_owners_values = getOnlyDigits(self.fcf_owners)  #filtering FCF values (taking only digit values)
        fcf_project_values = getOnlyDigits(self.fcf_project)

        # fcf_owners_values_y = getOnlyDigits(self.fcf_owners_y)
        # fcf_project_y = getOnlyDigits(self.fcf_project_y)

        self.irr_owners = self.irr(fcf_owners_values)  #calculation of IRR based on FCF  owners
        self.irr_project = self.irr(fcf_project_values) #calculation of IRR based on FCF project

        if self.irr_owners is not None and not numpy.isnan(self.irr_owners):  #calculation of IRR yearly OWNERS
            self.irr_owners_y = ((1 + self.irr_owners) ** 12) - 1 # FORMULA by Borut
        else:
            self.irr_owners_y = float('Nan')

        if self.irr_project is not None and not numpy.isnan(self.irr_project): #calculation of IRR yearly PROJECT
            self.irr_project_y = ((1 + self.irr_project) ** 12) - 1 # FORMULA by Borut
        else:
            self.irr_project_y = float('Nan')

        self.fcf_owners[PROJECT_START] = "IRR = %s" % self.irr_owners_y #adding IRR value to FCF row
        self.fcf_project[PROJECT_START] = "IRR = %s" % self.irr_project_y  #adding IRR value to FCF row
        self.fcf_owners_y[PROJECT_START] = "IRR = %s" % self.irr_owners_y #adding IRR value to FCF row
        self.fcf_project_y[PROJECT_START] = "IRR = %s" % self.irr_project_y #adding IRR value to FCF row

    def calcNPV(self):
        """Calculation of monthly and yearly NPV for owners and project"""

        fcf_owners_values = getOnlyDigits(self.fcf_owners) #filtering FCF values (taking only digit values)
        fcf_project_values = getOnlyDigits(self.fcf_project) #filtering FCF values (taking only digit values)
        fcf_owners_values_y = getOnlyDigits(self.fcf_owners_y)
        fcf_project_y = getOnlyDigits(self.fcf_project_y)

        self.npv_owners, pv_owners_list = npvPv(self.wacc, fcf_owners_values)  #NPV and PV calculation OWNERS
        self.npv_project, pv_project_list = npvPv(self.wacc, fcf_project_values) #NPV and PV calculation PROJECT

        self.npv_owners_y, pv_owners_list_y = npvPv(self.wacc_y, fcf_owners_values_y)#NPV and PV calculation OWNERS YEARLY
        self.npv_project_y, pv_project_list_y = npvPv(self.wacc_y, fcf_project_y) #NPV and PV calculation PROJECT YEARLY

        self.pv_owners = self.mapPVDates(pv_owners_list, [self.wacc, self.npv_owners])  #converting values to dict where key=date
        self.pv_owners_y = self.mapPVDates(pv_owners_list_y, [self.wacc_y,self.npv_owners_y], yearly=True) #converting values to dict where key=date
        self.pv_project =  self.mapPVDates(pv_owners_list, [self.wacc,self.npv_project]) #converting values to dict where key=date
        self.pv_project_y = self.mapPVDates(pv_project_list_y, [self.wacc_y,self.npv_project_y], yearly=True) #converting values to dict where key=date

    def mapPVDates(self, values, initial_value="", yearly=False):
        """Maps list of values to report dates"""
        if yearly:
            dates = self.report_dates_y.keys()
        else:
            dates = self.report_dates.values()

        result = OrderedDict()
        result[PROJECT_START] = "WACC= %0.3f , NPV=%0.1f" % (initial_value[0], initial_value[1])

        for date, val in zip(dates, values):
            result[date] = val

        return  result

    def calcWACC(self):
        """ WACC = share of debt in financing * cost of debt * (1-tax rate) + cost of capital * share of capital
        share of debt + share of capital = 1"""
        cost_capital = self.economic_module.cost_capital  #loading cost capital value from Economic module
        share_debt =  self.economic_module.debt_share #loading debt share value from Economic module
        tax_rate = self.economic_module.tax_rate #loading tax_rate value from Economic module
        cost_debt = self.economic_module.debt_rate #loading cost_debt value from Economic module
        share_capital = 1 - share_debt

        self.wacc_y =  share_debt * cost_debt * (1 - tax_rate) + cost_capital * share_capital  #Borut Formula
        self.wacc =  (1 + self.wacc_y) ** (1 / 12.0) - 1  #WACC formula

    def calcUnallocatedEarnings(self, date):
        """Calculating accumulated earnings = previous (net_earning+unallocated_earning) """
        prev_month_date = lastDayPrevMonth(date)
        if prev_month_date < self.start_date_project:  #finding prev month date
            prev_month_date = PROJECT_START

        prev_unallocated_earning = self.unallocated_earning[prev_month_date]  #getting prev month values
        prev_net_earning = self.net_earning[prev_month_date] #getting prev month values
        return prev_unallocated_earning + prev_net_earning

    def calcAccumulatedEarnings(self, to_date):
        """return accumulated eanings from start project to @to_date -1 day"""
        return  sum(self.calcNetEarning(date) for date in filter(lambda d:d < to_date, self.report_dates.values()))

    @cached_property
    def price(self):
        """return DICT with kwh price for price of electricity MONTHLY -- FOR ALL PROJECT PERIOD"""
        return self.calcReportMonthlyValues1(self.economic_module.getPriceKwh)

    @cached_property
    def electricity_monthly(self):
        """return DICT with volume of for electricity MONTHLY -- FOR ALL PROJECT PERIOD"""
        return self.calcReportMonthlyValues3(self.economic_module.getElectricityProductionLifetime()) #based on daily data

    @cached_property
    def electricity_prices_monthly(self):
        """return DICT for electricity prices MONTHLY -- FOR ALL PROJECT PERIOD"""
        return self.calcReportMonthlyValues4(self.economic_module.electricity_prices) #based on daily prices

    @cached_property
    def solar_insolations_monthly(self):
        """return DICT with volume of for insolations MONTHLY -- FOR ALL PROJECT PERIOD"""
        return self.calcReportMonthlyValues3(self.energy_module.getInsolationsLifetime())  #based on daily Insollations

    def calcLtLoans(self, end_day):
        """Monthly calculation of  Long-Term Loans"""
        return  self.economic_module.debt_rest_payments_wo_percents.get(end_day, 0)

    def calcLtOperLiab(self, end_day):
        """Monthly calculation of Long-Term Operating Liabilities - NOT IMPLEMENTED"""
        return 0

    def calcEquity(self,  end_day):
        """Monthly calculation of equity"""
        return  self.paid_in_capital[end_day] + self.retained_earning[end_day] + self.unallocated_earning[end_day]

    def calcLiabilities(self, end_day):
        """Monthly calculation of Liabilities"""
        return self.equity[end_day] + self.financial_operating_obligation[end_day]

    def calcStLoans(self, end_day):
        """Monthly calculation of Short-Term Loans """
        cur_earn = self.retained_earning[end_day]
        if cur_earn < 0:
            return abs(cur_earn)
        else:
            return 0

    def calcFinancialOperatingObligations(self, date):
        """calculation Financial And Operating Obligations Monthly"""
        return sum([
        self.long_term_loan[date],
        self.long_term_operating_liability[date],
        self.short_term_loan[date],
        self.short_term_debt_suppliers[date],
        ])

    def calcTotalCosts(self, end_day):
        """calculation of total costs Monthly = operational_cost + development_cost"""
        return  self.operational_cost[end_day] + self.development_cost[end_day]

    def calcEbitda(self, date):
        """calculation of ebitda = revenues - costs"""
        return self.revenue[date] - self.cost[date]

    def calcEbit(self, date):
        """calculation of ebit = ebitda - Depreciation"""
        return self.ebitda[date] - self.depreciation[date]

    def calcEbt(self, date):
        """calculation of ebt = ebit - interests paid"""
        return self.ebit[date] - self.iterest_paid[date]

    def calcNetEarning(self, date):
        """calculation of net_earning = ebt - taxes"""
        return self.ebt[date] - self.tax[date]

    def calcTax(self, date):
        """
        tax = EBT in the year * taxrate
        tax = taxrate * max(EBT*50%; EBT - accumulated loss)
        entered only in december
        """
        if not isLastDayYear(date):  #IF @date is NOT LAST DAY of YEAR -> TAX  = 0
            return 0
        else:
            #IF YEARLY EBT BELOW ZERO -> NO TAX
            #IF EBT + ACC EARN < 0 -> NO TAX
            #ELSE MAX 50% of YEAR EBT or EBT - ACC EARN
            accumulated_earnings = self.calcAccumulatedEarnings(date)
            year_ebt = self.ebt_y[date]

            if year_ebt <= 0:
                return 0
            elif year_ebt + accumulated_earnings <= 0:
                return 0
            else:
                tax_rate = self.economic_module.getTaxRate()
                return tax_rate * max(year_ebt/2.0, year_ebt - accumulated_earnings)


    def calcPaidIn(self, date):
        """Paid -in calculation"""
        prev_month_date = lastDayPrevMonth(date)
        if prev_month_date < self.start_date_project:  #finding prev month date
            prev_month_date = PROJECT_START

        prev_paid_in = self.paid_in_capital[prev_month_date]  #prev month paid_in
        return  prev_paid_in + self.economic_module.getPaidInAtDate(date)

    def calcCurrentAssets(self, date):
        """calculating current assests as sum"""
        return (
        self.inventory[date] +
        self.operating_receivable[date] +
        self.short_term_investment[date] +
        self.asset_bank_account[date] )

    def calcAssets(self, date):
        """calculating assests as sum fixed + current"""
        return ( self.current_asset[date] + self.fixed_asset[date] )

    def calcFixedAssets(self, date):
        """calculating fixed assests as diff between investment and Depreciation
        return  cur_investments + prev_fixed_asset - cur_Depreciation
        """
        prev_month_date = lastDayPrevMonth(date)
        if prev_month_date < self.start_date_project:
            prev_month_date = PROJECT_START

        prev_fixed_asset = self.fixed_asset[prev_month_date] #.get(prev_month_last_day, 0)
        cur_investments = self.economic_module.getMonthlyInvestments(date)
        cur_depreciation = self.depreciation[date]

        return (cur_investments + prev_fixed_asset - cur_depreciation)

    def calcOperatingReceivable(self,  date):
        """Calculation Monthly operating_receivable using following rule
        Revenue is paid in 60 days - so at the end of the month you have for two months of recievables
        """
        prev1_date = lastDayPrevMonth(date)

        if prev1_date >= self.start_date_project:
            prev1_value = self.cost[prev1_date]
            cur_value = self.revenue[date]
        else :
            prev1_value = 0
            cur_value = self.revenue[date]

        return  prev1_value + cur_value

    def calcShortTermDebtSuppliers(self,  date):
        """Calculation Monthly Short-Term Debt to Suppliers using same rule as for operating_receivable
        """
        prev1_date = lastDayPrevMonth(date)

        if prev1_date >= self.start_date_project:
            prev1_value = self.cost[prev1_date]
            cur_value = self.cost[date]
        else:
            prev1_value = 0
            cur_value = self.cost[date]

        return  prev1_value + cur_value

    def checkBalanceSheet(self, date):
        """Checks balance sheet Assets - Liabilities should be 0
        return  Nothing if all it OK,
        return  ValueError if check failed
        """
        if self.asset[date] - self.liability[date] == 0:
            self.control[date] = 0
        else:
            self.control[date] = self.asset[date] - self.liability[date]


if __name__ == '__main__':
    mainconfig = MainConfig('ITALY')
    energy_module = EnergyModule(mainconfig)
    technology_module = TechnologyModule(mainconfig, energy_module)
    subsidy_module = SubsidyModule(mainconfig)
    economic_module = EconomicModule(mainconfig, technology_module, subsidy_module)

    r = Report(mainconfig, economic_module)
    import time
    s = time.time()
    for i in range(1):
        r.calcReportValues()

    print time.time() - s

