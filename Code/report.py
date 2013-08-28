#!/usr/bin/env python
# -*- coding utf-8 -*-
import numpy
from collections import  OrderedDict
from annex import lastDayMonth, firstDayMonth, cached_property, lastDayPrevMonth
from annex import memoize, OrderedDefaultdict, isLastDayYear, OrderedDefaultdict
from annex import nubmerDaysInMonth, getOnlyDigits, sameDayLastYear, get_list_dates
from financial_analysis import irr, npvPv
from constants import PROJECT_START, REPORT_ROUNDING
from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from ecm import EconomicModule
from base_class import BaseClassConfig
from config_readers import MainConfig

class Report(BaseClassConfig):
    """Module for calculating Balance, FCF"""
    def __init__(self, config_module, economic_module):
        BaseClassConfig.__init__(self, config_module)

        self.economic_module = economic_module
        self.technology_module =  economic_module.technology_module
        self.subside_module = economic_module.subside_module
        self.energy_module =  self.technology_module.energy_module

    def calcReportValues(self):
        """Main function to cacl all values for reports"""
        self.initAttrs()
        self.initHelperAttrs()
        self.initFCFArgs()
        for start_day, end_day in self.report_dates.items():
            self.calcMonthlyValuesPart1(start_day, end_day)
            if isLastDayYear(end_day):
                self.calcYearlyValuesPart1(end_day)
            self.calcMonthlyValuesPart2(start_day, end_day)
            self.calcHelperValuesMonthly(end_day)
            self.calcFCFMonthly(end_day)
            self.checkBalanceSheet(end_day)

            if isLastDayYear(end_day):
                self.calcYearlyValuesPart2(end_day)
                self.calcYearlyValuesPart3(end_day)

        self.calcIRR()
        self.calcWACC()
        self.calcNPV()

    def startProjectOrderedDict(self, name=PROJECT_START, value=""):
        """prepare OrderedDict"""
        return OrderedDict({name: value,})

    def startProjectOrderedDefaultdict(self, name=PROJECT_START, value=""):
        """prepare Ordered Default Dict"""
        return  OrderedDefaultdict(int, {name: value,})

    def initAttrs(self):
        """Creating attrs for monthly and yearly values"""
        capital = self.economic_module.initial_paid_in_capital

        ################## SECOND SHEET ###############################
        self.sun_insolation = self.startProjectOrderedDict(name="",value="")
        self.electricity_production = self.startProjectOrderedDict(name="",value="")
        self.electricity_prices = self.startProjectOrderedDict(name="",value="")
        self.sun_insolation_y = self.startProjectOrderedDefaultdict(name="",value="")
        self.electricity_production_y = self.startProjectOrderedDefaultdict(name="",value="")
        self.electricity_prices_y = self.startProjectOrderedDefaultdict(name="",value="")

        ################### IS ########################################
        self.revenue = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.revenue_electricity = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.revenue_subsides = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.cost = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.operational_cost = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.development_cost = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.ebitda = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.ebit = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.ebt = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.iterest_paid = self.startProjectOrderedDict(name=PROJECT_START,value="")
        self.deprication = self.startProjectOrderedDict(name=PROJECT_START,value="")
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
        self.revenue_subsides_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.cost_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.operational_cost_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.development_cost_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.ebitda_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.ebit_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.ebt_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.iterest_paid_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
        self.deprication_y = self.startProjectOrderedDefaultdict(name=PROJECT_START,value="")
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

        rev_electricity, rev_subside = self.economic_module.getRevenue(start_day, end_day)
        self.revenue_electricity[M], self.revenue_subsides[M] = rev_electricity, rev_subside
        self.revenue[M] = rev_electricity + rev_subside

        self.electricity_production[M] = self.electricity_monthly[M]
        self.sun_insolation[M] = self.solar_insolations_monthly[M]
        self.electricity_prices[M] = self.electricity_prices_monthly[M]

        self.deprication[M] = self.economic_module.calcDepricationMonthly(end_day)
        self.iterest_paid[M] = self.economic_module.calculateDebtInterests(end_day)

        self.development_cost[M] = self.economic_module.getDevelopmentCosts(start_day, end_day)
        self.operational_cost[M] = self.economic_module.getOperationalCosts(start_day, end_day)
        self.cost[M] = self.economic_module.getCosts(start_day, end_day)

        self.ebitda[M] = self.calcEbitda(end_day)
        self.ebit[M] = self.calcEbit(end_day)
        self.ebt[M] = self.calcEbt(end_day)

    def calcMonthlyValuesPart2(self, start_day, end_day):
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
        """Main function to calc yearly value for reports P1"""

        for start_day_m, end_day_m in self.report_dates_y[end_day_y]:
            Y = end_day_y
            M = end_day_m
            self.revenue_electricity_y[Y] += self.revenue_electricity[M]
            self.revenue_subsides_y[Y] += self.revenue_subsides[M]
            self.revenue_y[Y] += self.revenue[M]

            self.deprication_y[Y] += self.deprication[M]
            self.iterest_paid_y[Y] += self.iterest_paid[M]
            self.cost_y[Y] += self.cost[M]
            self.development_cost_y[Y] += self.development_cost[M]
            self.operational_cost_y[Y] += self.operational_cost[M]

            self.ebitda_y[Y] += self.ebitda[M]
            self.ebit_y[Y] += self.ebit[M]
            self.ebt_y[Y] += self.ebt[M]

    def calcYearlyValuesPart2(self, end_day_y):
        """Main function to calc yearly value for reports P2"""

        for start_day_m, end_day_m in self.report_dates_y[end_day_y]:
            Y = end_day_y
            Y1 =  sameDayLastYear(end_day_y)#previous_year
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
        """Main function to calc yearly value for reports P2"""

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
        M = date
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
        prev_asset_bank_account = self.getPrevMonthValue(self.asset_bank_account, M)
        prev_short_term_loan = self.getPrevMonthValue(self.short_term_loan, M)

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

            self.fcf_project[M] = (self.net_earning[M] -
                                   self.getDeltaCurPrev(self.fixed_asset, M) -
                                   self.getDeltaCurPrev(self.operating_receivable, M) +
                                   self.getDeltaCurPrev(self.short_term_debt_suppliers, M) +
                                   self.iterest_paid[M] - self.asset_bank_account[M]
                                   )

            self.fcf_owners[M] = - self.paid_in_capital[M]

        else:

            self.fcf_project[M] = (self.net_earning[M] -
                                   self.getDeltaCurPrev(self.fixed_asset, M) -
                                   self.getDeltaCurPrev(self.operating_receivable, M) +
                                   self.getDeltaCurPrev(self.short_term_debt_suppliers, M) +
                                   self.iterest_paid[M]
                                   )

            self.fcf_owners[M] = (- self.getDeltaCurPrev(self.paid_in_capital, M) +
                                  self.getDeltaCurPrev(self.asset_bank_account, M)
                                  )

    def calcIRR(self):
        """Calculating IRR for project and owners, using numpy.IRR function
        both Montly and Yearly values
        """
        fcf_owners_values = getOnlyDigits(self.fcf_owners)
        fcf_project_values = getOnlyDigits(self.fcf_project)

        fcf_owners_values_y = getOnlyDigits(self.fcf_owners_y)
        fcf_project_y = getOnlyDigits(self.fcf_project_y)

        self.irr_owners = irr(fcf_owners_values)
        self.irr_project = irr(fcf_project_values)

        if self.irr_owners is not None and not numpy.isnan(self.irr_owners):
            self.irr_owners_y = ((1 + self.irr_owners) ** 12) - 1 # FORMULA by Borut
        else:
            self.irr_owners_y = float('Nan')

        if self.irr_project is not None and not numpy.isnan(self.irr_project):
            self.irr_project_y = ((1 + self.irr_project) ** 12) - 1 # FORMULA by Borut
        else:
            self.irr_project_y = float('Nan')

        self.fcf_owners[PROJECT_START] = "IRR = %s" % self.irr_owners_y #YEARLY IRR FOR MONTHLY REPORT
        self.fcf_project[PROJECT_START] = "IRR = %s" % self.irr_project_y  #YEARLY IRR FOR MONTHLY REPORT

        self.fcf_owners_y[PROJECT_START] = "IRR = %s" % self.irr_owners_y
        self.fcf_project_y[PROJECT_START] = "IRR = %s" % self.irr_project_y

    def calcNPV(self):
        """Calculation of monthly and yearly NPV for owners and project"""

        fcf_owners_values = getOnlyDigits(self.fcf_owners)
        fcf_project_values = getOnlyDigits(self.fcf_project)

        fcf_owners_values_y = getOnlyDigits(self.fcf_owners_y)
        fcf_project_y = getOnlyDigits(self.fcf_project_y)

        self.npv_owners, pv_owners_list = npvPv(self.wacc, fcf_owners_values)
        self.npv_project, pv_project_list = npvPv(self.wacc, fcf_project_values)

        self.npv_owners_y, pv_owners_list_y = npvPv(self.wacc_y, fcf_owners_values_y)
        self.npv_project_y, pv_project_list_y = npvPv(self.wacc_y, fcf_project_y)

        self.pv_owners = self.mapPVDates(pv_owners_list, [self.wacc, self.npv_owners])
        self.pv_owners_y = self.mapPVDates(pv_owners_list_y, [self.wacc_y,self.npv_owners_y], yearly=True)
        self.pv_project =  self.mapPVDates(pv_owners_list, [self.wacc,self.npv_project])
        self.pv_project_y = self.mapPVDates(pv_project_list_y, [self.wacc_y,self.npv_project_y], yearly=True)

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
        cost_capital = self.economic_module.cost_capital
        share_debt =  self.economic_module.debt_share
        share_capital = 1 - share_debt
        tax_rate = self.economic_module.tax_rate
        cost_debt = self.economic_module.debt_rate

        self.wacc_y =  share_debt * cost_debt * (1 - tax_rate) + cost_capital * share_capital  #Borut Formula
        self.wacc =  (1 + self.wacc_y) ** (1 / 12.0) - 1

    def calcUnallocatedEarnings(self, date):
        """Calculating accumulated earnings = previous (net_earning+unallocated_earning) """
        prev_month_date = lastDayPrevMonth(date)
        if prev_month_date < self.start_date_project:
            prev_month_date = PROJECT_START
        prev_unallocated_earning = self.unallocated_earning[prev_month_date]
        prev_net_earning = self.net_earning[prev_month_date]
        return prev_unallocated_earning + prev_net_earning

    def calcAccumulatedEarnings(self, to_date):
        """return accumulated eanings from start project to @to_date -1 day"""
        eanings = 0
        for date in self.report_dates.values():
            if date < to_date:  #!!! NOT EQUAL
                eanings += self.calcNetEarning(date)
        return eanings

    @cached_property
    def price(self):
        """return kwh price for price of electricity MONTHLY"""
        return self.calcReportMonthlyValues1(self.economic_module.getPriceKwh)

    @cached_property
    def electricity_monthly(self):
        """return volume of for electricity MONTHLY"""
        return self.calcReportMonthlyValues3(self.economic_module.getElectricityProductionLifetime())

    @cached_property
    def electricity_prices_monthly(self):
        """return volume of for electricity MONTHLY"""
        return self.calcReportMonthlyValues4(self.economic_module.electricity_prices)

    @cached_property
    def solar_insolations_monthly(self):
        """return volume of for insolations MONTHLY"""
        return self.calcReportMonthlyValues3(self.energy_module.getInsolationsLifetime())

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
        """calculation of ebit = ebitda - deprication"""
        return self.ebitda[date] - self.deprication[date]

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
        if isLastDayYear(date):
            accumulated_earnings = self.calcAccumulatedEarnings(date)
            year_ebt = self.ebt_y[date]

            if year_ebt <= 0:
                return 0
            elif year_ebt + accumulated_earnings <= 0:
                return 0
            else:
                tax_rate = self.economic_module.getTaxRate()
                return tax_rate * max(year_ebt/2.0, year_ebt - accumulated_earnings)
        else:
            return 0

    def calcPaidIn(self, date):
        """Paid -in calculation"""
        prev_month_date = lastDayPrevMonth(date)
        if prev_month_date < self.start_date_project:
            prev_month_date = PROJECT_START
        prev_paid_in = self.paid_in_capital[prev_month_date]
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
        """calculating fixed assests as diff between investment and deprication
        return  cur_investments + prev_fixed_asset - cur_deprication
        """
        prev_month_date = lastDayPrevMonth(date)
        if prev_month_date < self.start_date_project:
            prev_month_date = PROJECT_START
        prev_fixed_asset = self.fixed_asset[prev_month_date] #.get(prev_month_last_day, 0)

        cur_investments = self.economic_module.getMonthlyInvestments(date)
        cur_deprication = self.deprication[date]

        return (cur_investments + prev_fixed_asset - cur_deprication)

    def calcOperatingReceivable(self,  date):
        """Calculation Monthly operating_receivable using following rule
        Revenue is paid in 60 days - so at the end of the month you have for two months of recievables
        """
        prev1_date = lastDayPrevMonth(date)

        if prev1_date < self.start_date_project:
            prev1_value = 0
            cur_value = self.revenue[date]
        else :
            prev1_value = self.cost[prev1_date]
            cur_value = self.revenue[date]

        return  prev1_value + cur_value

    def calcShortTermDebtSuppliers(self,  date):
        """Calculation Monthly Short-Term Debt to Suppliers using same rule as for operating_receivable
        """
        prev1_date = lastDayPrevMonth(date)

        if prev1_date < self.start_date_project:
            prev1_value = 0
            cur_value = self.cost[date]
        else:
            prev1_value = self.cost[prev1_date]
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
    mainconfig = MainConfig()
    energy_module = EnergyModule(mainconfig)
    technology_module = TechnologyModule(mainconfig, energy_module)
    subside_module = SubsidyModule(mainconfig)
    economic_module = EconomicModule(mainconfig, technology_module, subside_module)

    r = Report(mainconfig, economic_module)
    r.calcReportValues()

