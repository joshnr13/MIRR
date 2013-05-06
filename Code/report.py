import datetime
import pylab
import numpy
import csv
import os.path

from constants import report_directory, REPORT_ROUNDING

from collections import defaultdict, OrderedDict
from annex import Annuitet, last_day_month, next_month, first_day_month, cached_property, uniquify_filename, transponse_csv, add_header_csv, last_day_previous_month
from annex import accumulate, memoize, OrderedDefaultdict, is_last_day_year
from annex import add_start_project_values, get_months_range, csv2xlsx, month_number_days
from annex import OrderedDefaultdict, convert2excel, combine_files
from constants import BS, IS, CF, PROJECT_START
from numbers import Number
from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from ecm import EconomicModule
from base_class import BaseClassConfig
from main_config_reader import MainConfig



class Report(BaseClassConfig):
    def __init__(self, config_module, economic_module):
        BaseClassConfig.__init__(self, config_module)
        self.economic_module = economic_module
        self.report_get_dates()

    def calc_report_values(self):
        """Main function to cacl all values for reports"""

        self.init_attrs()
        self.init_helper_attrs()
        self.init_fcf_args()

        for start_day, end_day in self.report_dates.items():
            self.calc_monthly_values_part1(start_day, end_day)
            if is_last_day_year(end_day):
                self.calc_yearly_values_part1(end_day)
            self.calc_monthly_values_part2(start_day, end_day)
            self.calc_helper_values_monthly(end_day)
            self.calc_fcf_monthly(end_day)
            self.check_balance_sheet(end_day)

            if is_last_day_year(end_day):
                self.calc_yearly_values_part2(end_day)

        self.calc_irr()

    def start_project_OrderedDict(self, name=PROJECT_START, value=""):
        return OrderedDict({name: value,})

    def start_project_OrderedDefaultdict(self, name=PROJECT_START, value=""):
        return  OrderedDefaultdict(int, {name: value,})

    def init_attrs(self):
        """Creating attrs for monthly and yearly values"""
        capital = self.economic_module.capital

        ################### IS ########################################
        self.revenue = self.start_project_OrderedDict(name=PROJECT_START,value="")
        self.revenue_electricity = self.start_project_OrderedDict(name=PROJECT_START,value="")
        self.revenue_subsides = self.start_project_OrderedDict(name=PROJECT_START,value="")
        self.cost = self.start_project_OrderedDict(name=PROJECT_START,value="")
        self.operational_cost = self.start_project_OrderedDict(name=PROJECT_START,value="")
        self.development_cost = self.start_project_OrderedDict(name=PROJECT_START,value="")
        self.ebitda = self.start_project_OrderedDict(name=PROJECT_START,value="")
        self.ebit = self.start_project_OrderedDict(name=PROJECT_START,value="")
        self.ebt = self.start_project_OrderedDict(name=PROJECT_START,value="")
        self.iterest_paid = self.start_project_OrderedDict(name=PROJECT_START,value="")
        self.deprication = self.start_project_OrderedDict(name=PROJECT_START,value="")
        self.tax = self.start_project_OrderedDict(name=PROJECT_START,value="")
        self.net_earning = self.start_project_OrderedDict(name=PROJECT_START,value=0)

        ################### BS ########################################
        self.investment = self.start_project_OrderedDict(name=PROJECT_START,value=0)
        self.fixed_asset = self.start_project_OrderedDict(name=PROJECT_START,value=0)
        self.asset = self.start_project_OrderedDict(name=PROJECT_START,value=capital)
        self.inventory = self.start_project_OrderedDict(name=PROJECT_START,value=0)
        self.operating_receivable = self.start_project_OrderedDict(name=PROJECT_START,value=0)
        self.short_term_investment = self.start_project_OrderedDict(name=PROJECT_START,value=0)
        self.asset_bank_account = self.start_project_OrderedDict(name=PROJECT_START,value=capital)
        self.paid_in_capital = self.start_project_OrderedDict(name=PROJECT_START,value=capital)
        self.current_asset = self.start_project_OrderedDict(name=PROJECT_START,value=capital)
        self.retained_earning = self.start_project_OrderedDict(name=PROJECT_START,value=0)
        self.unallocated_earning = self.start_project_OrderedDict(name=PROJECT_START,value=0)
        self.retained_earning = self.start_project_OrderedDict(name=PROJECT_START,value=0)
        self.financial_operating_obligation = self.start_project_OrderedDict(name=PROJECT_START,value=0)
        self.long_term_loan = self.start_project_OrderedDict(name=PROJECT_START,value=0)
        self.short_term_loan = self.start_project_OrderedDict(name=PROJECT_START,value=0)
        self.long_term_operating_liability = self.start_project_OrderedDict(name=PROJECT_START,value=0)
        self.short_term_debt_suppliers = self.start_project_OrderedDict(name=PROJECT_START,value=0)
        self.liability = self.start_project_OrderedDict(name=PROJECT_START,value=capital)
        self.equity = self.start_project_OrderedDict(name=PROJECT_START,value=capital)
        self.control = self.start_project_OrderedDict(name=PROJECT_START,value="")

        ################### IS-Y #######################################
        self.revenue_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")
        self.revenue_electricity_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")
        self.revenue_subsides_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")
        self.cost_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")
        self.operational_cost_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")
        self.development_cost_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")
        self.ebitda_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")
        self.ebit_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")
        self.ebt_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")
        self.iterest_paid_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")
        self.deprication_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")
        self.tax_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")
        self.net_earning_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")

        ################### BS-Y #######################################
        self.investment_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=0)
        self.fixed_asset_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=0)
        self.asset_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=capital)
        self.inventory_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=0)
        self.operating_receivable_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=0)
        self.short_term_investment_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=0)
        self.asset_bank_account_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=0)
        self.paid_in_capital_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=capital)
        self.current_asset_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=capital)
        self.retained_earning_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=0)
        self.unallocated_earning_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=0)
        self.retained_earning_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=0)
        self.financial_operating_obligation_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=0)
        self.long_term_loan_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=0)
        self.short_term_loan_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=0)
        self.long_term_operating_liability_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=0)
        self.short_term_debt_suppliers_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=0)
        self.liability_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=capital)
        self.equity_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value=capital)
        self.control_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")

    def init_fcf_args(self):

        self.fcf_project = self.start_project_OrderedDict(name=PROJECT_START,value="")
        self.fcf_owners = self.start_project_OrderedDict(name=PROJECT_START,value="")

        self.fcf_project_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")
        self.fcf_owners_y = self.start_project_OrderedDefaultdict(name=PROJECT_START,value="")

    def init_helper_attrs(self):
        """Initing helper args to calculate correct BS"""
        self.hlp = OrderedDict()
        self.decr_st_loans = OrderedDict()
        self.decr_bank_assets = OrderedDict()

        self.hlp_y = OrderedDefaultdict(int)
        self.decr_st_loans_y = OrderedDefaultdict(int)
        self.decr_bank_assets_y = OrderedDefaultdict(int)

    def calc_monthly_values_part1(self, start_day, end_day):
        """Main function to calc montly value for reports P1"""
        M = end_day

        self.revenue_electricity[M] = self.economic_module.getRevenue_elecricity(start_day, end_day)
        self.revenue_subsides[M] = self.economic_module.getRevenue_subside(start_day, end_day)
        #self.revenue[M] = self.economic_module.getRevenue(start_day, end_day)
        self.revenue[M] = self.revenue_electricity[M] + self.revenue_subsides[M]

        self.deprication[M] = self.economic_module.calcDepricationMonthly(end_day)
        self.iterest_paid[M] = self.economic_module.calculateDebtInterests(end_day)

        self.development_cost[M] = self.economic_module.getDevelopmentCosts(start_day, end_day)
        self.operational_cost[M] = self.economic_module.getOperationalCosts(start_day, end_day)
        self.cost[M] = self.economic_module.getCosts(start_day, end_day)

        self.ebitda[M] = self._calc_ebitda(end_day)
        self.ebit[M] = self._calc_ebit(end_day)
        self.ebt[M] = self._calc_ebt(end_day)


    def calc_monthly_values_part2(self, start_day, end_day):
        """Main function to calc montly value for reports P2"""
        M = end_day


        self.tax[M] = self._calc_tax(end_day)
        self.net_earning[M] = self._calc_net_earning(end_day)

        self.investment[M] = self.economic_module.getMonthlyInvestments(end_day)
        self.fixed_asset[M] = self._calc_fixed_assets(end_day)

        self.operating_receivable[M] = self._calc_operating_receivable(end_day)
        self.inventory[M] = 0 #NOT IMPLEMENTED
        self.short_term_investment[M] = 0 #NOT IMPLEMENTED
        self.asset_bank_account[M] = 0 #NOT IMPLEMENTED
        self.paid_in_capital[M] = self.paid_in_capital[PROJECT_START]

        self.current_asset[M] = self._calc_current_assets(end_day)
        self.retained_earning[M] = self.net_earning[M]
        self.unallocated_earning[M] = self._calc_unallocated_earnings(M)
        self.asset[M] = self._calc_assets(end_day)

        self.long_term_loan[M] = self._calc_lt_loans(end_day)
        self.long_term_operating_liability[M] = self._calc_lt_operliab(end_day)
        self.short_term_loan[M] = self._calc_st_loans(end_day)
        self.short_term_debt_suppliers[M] = self._calc_short_term_debt_suppliers(end_day)

        self.financial_operating_obligation[M] = self._calc_foo(end_day)
        self.equity[M] = self._calc_equity(end_day)
        self.liability[M] = self._calc_liabilities(end_day)



    def calc_yearly_values_part1(self,  end_day_y):
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
            self.current_asset_y

            self.ebitda_y[Y] += self.ebitda[M]
            self.ebit_y[Y] += self.ebit[M]
            self.ebt_y[Y] += self.ebt[M]


    def calc_yearly_values_part2(self, end_day_y):
        """Main function to calc yearly value for reports P2"""

        for start_day_m, end_day_m in self.report_dates_y[end_day_y]:
            Y = end_day_y
            M = end_day_m
            self.tax_y[Y] += self.tax[M]
            self.net_earning_y[Y] += self.net_earning[M]

            self.investment_y[Y] += self.investment[M]
            self.fixed_asset_y[Y] += self.fixed_asset[M]

            self.current_asset_y[Y] +=  self.current_asset[M]
            self.operating_receivable_y[Y] +=  self.operating_receivable[M]
            self.asset_bank_account_y[Y] += self.asset_bank_account[M]
            self.asset_y[Y] += self.asset[M]

            self.inventory_y[Y] += self.inventory[M]
            self.equity_y[Y] += self.equity[M]
            self.paid_in_capital_y[Y] += self.paid_in_capital[M]
            self.retained_earning_y[Y] += self.retained_earning[M]
            self.unallocated_earning_y[Y] += self.unallocated_earning[M]

            self.long_term_loan_y[Y] +=self.long_term_loan[M]
            self.long_term_operating_liability_y[Y] +=self.long_term_operating_liability[M]
            self.short_term_loan_y[Y] +=self.short_term_loan[M]
            self.short_term_debt_suppliers_y[Y] +=self.short_term_debt_suppliers[M]
            self.financial_operating_obligation_y[Y] +=self.financial_operating_obligation[M]
            self.liability_y[Y] += self.liability[M]
            self.control_y[Y] += self.control[M]

            self.fcf_owners_y[Y] += self.fcf_owners[M]
            self.fcf_project_y[Y] += self.fcf_project[M]

    def get_prev_month_value(self, obj, date):
        """Get previous month value of @obj with current date @date"""
        M = date
        pM = last_day_previous_month(date)
        if pM < self.start_date_project:
            pM = PROJECT_START
        return obj[pM]

    def get_delta_cur_prev(self,  obj, date):
        """Calculates delta between current month value and previous month value"""
        cur = obj[date]
        prev = self.get_prev_month_value(obj, date)
        return cur - prev

    def calc_helper_values_monthly(self, end_day):
        M = end_day
        MIN_OST = 500
        prev_asset_bank_account = self.get_prev_month_value(self.asset_bank_account, M)
        prev_short_term_loan = self.get_prev_month_value(self.short_term_loan, M)

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

        self.current_asset[M] = self._calc_current_assets(end_day)
        self.asset[M] = self._calc_assets(end_day)

        self.financial_operating_obligation[M] = self._calc_foo(end_day)
        self.liability[M] = self._calc_liabilities(end_day)


    def calc_fcf_monthly(self, end_day):
        M = end_day
        self.fcf_project[M] = (self.net_earning[M] -
                               self.get_delta_cur_prev(self.fixed_asset, M) -
                               self.get_delta_cur_prev(self.operating_receivable, M) +
                               self.get_delta_cur_prev(self.short_term_debt_suppliers, M) +
                               self.iterest_paid[M] - self.asset_bank_account[M]
                               )

        self.fcf_owners[M] = (- self.get_delta_cur_prev(self.paid_in_capital, M) +
                              self.net_earning[M] +
                              self.deprication[M]
                              )

    def calc_irr(self):
        """Calculating IRR for project and owners, using numpy.IRR function
        both Montly and Yearly values
        """
        #print self.fcf_owners.values()

        fcf_owners_values = filter(lambda x :isinstance(x, Number), self.fcf_owners.values())
        fcf_project = filter(lambda x :isinstance(x, Number), self.fcf_project.values())

        fcf_owners_values_y = filter(lambda x :isinstance(x, Number), self.fcf_owners_y.values())
        fcf_project_y = filter(lambda x :isinstance(x, Number), self.fcf_project_y.values())

        self.irr_owners = numpy.irr(fcf_owners_values)
        self.irr_project = numpy.irr(fcf_project)

        self.irr_owners_y = numpy.irr(fcf_owners_values_y)
        self.irr_project_y = numpy.irr(fcf_project_y)

        self.fcf_owners[PROJECT_START] = "IRR = %s" % self.irr_owners
        self.fcf_project[PROJECT_START] = "IRR = %s" % self.irr_owners

        self.fcf_owners_y[PROJECT_START] = "IRR = %s" % self.irr_owners_y
        self.fcf_project_y[PROJECT_START] = "IRR = %s" % self.irr_project_y


    def _calc_unallocated_earnings(self, date):
        """Calculating accumulated earnings = previous (net_earning+unallocated_earning) """
        prev_month_date = last_day_previous_month(date)
        if prev_month_date < self.start_date_project:
            prev_month_date = PROJECT_START
        prev_unallocated_earning = self.unallocated_earning[prev_month_date]
        prev_net_earning = self.net_earning[prev_month_date]
        return prev_unallocated_earning + prev_net_earning

    def accumulated_earnings_to(self, to_date):
        """return accumulated eanings from start project to @to_date -1 day"""
        eanings = 0
        for date in self.report_dates.values():
            if date < to_date:  #!!! NOT EQUAL
                eanings += self._calc_net_earning(date)
        return eanings

    @cached_property
    def price(self):
        """return kwh price for electricity MONTHLY"""
        return self.calc_report_monthly_values1(self.economic_module.getPriceKwh)

    @cached_property
    def electricity(self):
        """return volume of for electricity MONTHLY"""
        return self.calc_report_monthly_values2(self.economic_module.technology_module.getElectricityProduction)

    def _calc_lt_loans(self, end_day):
        """Monthly calculation of  Long-Term Loans"""
        return  self.economic_module.debt_rest_payments_wo_percents.get(end_day, 0)
        #return self.asset[end_day] - self.paid_in_capital[end_day]

    def _calc_lt_operliab(self, end_day):
        """Monthly calculation of Long-Term Operating Liabilities - NOT IMPLEMENTED"""
        return 0

    def _calc_equity(self,  end_day):
        """Monthly calculation of equity"""
        return  self.paid_in_capital[end_day] + self.retained_earning[end_day] + self.unallocated_earning[end_day]

    def _calc_liabilities(self, end_day):
        """Monthly calculation of Liabilities"""
        return self.equity[end_day] + self.financial_operating_obligation[end_day]

    def _calc_st_loans(self, end_day):
        """Monthly calculation of Short-Term Loans """
        cur_earn = self.retained_earning[end_day]
        if cur_earn < 0:
            return abs(cur_earn)
        else:
            return 0

    def _calc_foo(self, date):
        """calculation Financial And Operating Obligations Monthly"""
        return sum([
        self.long_term_loan[date],
        self.long_term_operating_liability[date],
        self.short_term_loan[date],
        self.short_term_debt_suppliers[date],
        ])


    def _cacl_total_costs(self, end_day):
        """calculation of total costs Monthly = operational_cost + development_cost"""
        return  self.operational_cost[end_day] + self.development_cost[end_day]


    def _calc_ebitda(self, date):
        """calculation of ebitda = revenues - costs"""
        return self.revenue[date] - self.cost[date]

    def _calc_ebit(self, date):
        """calculation of ebit = ebitda - deprication"""
        return self.ebitda[date] - self.deprication[date]

    def _calc_ebt(self, date):
        """calculation of ebt = ebit - interests paid"""
        return self.ebit[date] - self.iterest_paid[date]

    def _calc_net_earning(self, date):
        """calculation of net_earning = ebt - taxes"""
        return self.ebt[date] - self.tax[date]

    def _calc_tax(self, date):
        """
        tax = EBT in the year * taxrate
        tax = taxrate * max(EBT*50%; EBT - accumulated loss)
        entered only in december
        """
        if is_last_day_year(date):
            accumulated_earnings = self.accumulated_earnings_to(date)
            year_ebt = self.ebt_y[date]


            if year_ebt <= 0:
                return 0
            elif year_ebt + accumulated_earnings <= 0:
                return 0
            else:
                tax_rate = self.economic_module.getTaxRate()
                return tax_rate * max(year_ebt/2.0, year_ebt + accumulated_earnings)
        else:
            return 0

    def _calc_current_assets(self, date):
        """calculating current assests as sum"""
        return (
        self.inventory[date] +
        self.operating_receivable[date] +
        self.short_term_investment[date] +
        self.asset_bank_account[date] )

    def _calc_assets(self, date):
        """calculating assests as sum fixed + current"""
        return ( self.current_asset[date] + self.fixed_asset[date] )

    def _calc_fixed_assets(self, date):
        """calculating fixed assests as diff between investment and deprication
        return  cur_investments + prev_fixed_asset - cur_deprication
        """
        prev_month_date = last_day_previous_month(date)
        if prev_month_date < self.start_date_project:
            prev_month_date = PROJECT_START
        prev_fixed_asset = self.fixed_asset[prev_month_date] #.get(prev_month_last_day, 0)
        cur_investments = self.investment[date]
        cur_deprication = self.deprication[date]

        return (cur_investments + prev_fixed_asset - cur_deprication)

    def _calc_operating_receivable(self,  date):
        """Calculation Monthly operating_receivable using following rule
        Revenue is paid in 60 days - so at the end of the month you have for two months of recievables
        """
        prev1_date = last_day_previous_month(date)
        prev2_date = last_day_previous_month(prev1_date)

        if prev1_date < self.start_date_project:
            prev1_value = 0
            prev2_value = 0
        elif prev2_date < self.start_date_project:
            prev1_value = self.revenue[prev1_date]
            prev2_value = 0
        else :
            prev1_value = self.revenue[prev1_date]
            prev2_value = self.revenue[prev2_date]

        return  prev1_value + prev2_value

    def _calc_short_term_debt_suppliers(self,  date):
        """Calculation Monthly Short-Term Debt to Suppliers using same rule as for operating_receivable
        """
        prev1_date = last_day_previous_month(date)
        prev2_date = last_day_previous_month(prev1_date)

        if prev1_date < self.start_date_project:
            prev1_value = 0
            prev2_value = 0
        elif prev2_date < self.start_date_project:
            prev1_value = self.cost[prev1_date]
            prev2_value = 0
        else :
            prev1_value = self.cost[prev1_date]
            prev2_value = self.cost[prev2_date]

        return  prev1_value + prev2_value

    def calc_report_monthly_values2(self, func):
        """Calculates monthly values using 2 dates -first_day and last_day in month
        return  dict[end_day] = value
        """
        results = OrderedDict()
        for start_day, end_day in self.report_dates.items():
            results[end_day] = func(start_day, end_day)

        return results

    def calc_report_monthly_values1(self, func):
        """Calculates monthly values using 1 date - last_day in month
        return  dict[end_day] = value"""
        results = OrderedDict()
        for end_day in self.report_dates.values():
            results[end_day] = func(end_day)
        return results

    def report_get_dates(self):
        """saves all dates for report (last day of each month)
        dic[first_day_month]=last_day_month
        """
        report_dates = OrderedDict()
        report_dates_y = OrderedDict()

        date = first_day_month(self.start_date_project)
        date_to = self.end_date_project

        while True:
            report_date = last_day_month(date)
            key = first_day_month(date)
            report_dates[key] = report_date
            if is_last_day_year(report_date):
                report_dates_y[report_date] = get_months_range(report_date.year)
            date = next_month(date)
            if  date > date_to:
                break

        self.report_dates = report_dates
        self.report_dates_y = report_dates_y

    def get_report_fields(self, rows_str, yearly):
        postfix = "" if not yearly else "_y"
        rows = [getattr(self, attr+postfix) for attr in rows_str if attr]
        return rows

    def prepare_rows(self, rows_str, yearly):
        """Prepares rows for outputing to report
        + Rounding
        + Can output monthly (without change) and yearly (+_y) values ---> postfix
        """
        rows = self.get_report_fields(rows_str, yearly)

        new_rows = []
        for row in rows:
            result = OrderedDict()
            for k, v in row.items():
                if isinstance(v, (float, int)):
                    result[k] = round(v, REPORT_ROUNDING)
                else:
                    result[k] = v
            new_rows.append(result)

        return new_rows


    def write_report(self, output_filename, report_dic, yearly):
        """write report to file
        @report_dic - dict with all values incl header
        """
        header = report_dic.keys()
        rows = self.prepare_rows(report_dic.values(), yearly)
        with open(output_filename,'ab') as f:
            w = csv.DictWriter(f, rows[0].keys(), delimiter=';')
            w.writeheader()
            w.writerows(rows)

        transponse_csv(output_filename)
        add_header_csv(output_filename, header)
        transponse_csv(output_filename)


    def check_balance_sheet(self, date):
        """Checks balance sheet Assets - Liabilities should be 0
        return  Nothing if all it OK,
        return  ValueError if check failed
        """
        if self.asset[date] - self.liability[date] == 0:
            self.control[date] = 0
        else:
            self.control[date] = self.asset[date] - self.liability[date]


    def prepare_report_BS(self, excel=False, yearly=False):
        """Prepares and saves monthly BS report in csv file"""
        report_name = 'IS'
        output_filename = self.get_report_filename(report_name)
        self.write_report(output_filename, BS, yearly=yearly)
        print "%s Report outputed to file %s" % (report_name, output_filename)

    def prepare_report_IS(self, excel=False, yearly=False):
        """Prepares and saves monthly IS report in csv file"""
        report_name = 'IS'
        output_filename = self.get_report_filename(report_name)
        self.write_report(output_filename, IS, yearly=yearly)

    def prepare_report_CF(self, excel=False, yearly=False):
        """Prepares and saves monthly CF report in csv file"""
        report_name = 'CF'
        output_filename = self.get_report_filename(report_name)
        self.write_report(output_filename, CF, yearly=yearly)

        print "%s Report outputed to file %s" % (report_name, output_filename)

    def prepare_report_IS_BS_CF_IRR(self, excel=False, yearly=False):
        report_name = 'IS-BS-CF'
        output_filename = self.get_report_filename(report_name, yearly=yearly)

        bs_filename = output_filename + "_BS"
        is_filename = output_filename + "_IS"
        cf_filename = output_filename + "_CF"

        self.write_report(bs_filename, BS, yearly=yearly)
        self.write_report(is_filename, IS, yearly=yearly)
        self.write_report(cf_filename, CF, yearly=yearly)

        combine = [bs_filename, is_filename, cf_filename]
        combine_files(combine, output_filename)

        if excel:
            xls_output_filename = self.get_report_filename(report_name, 'xlsx', yearly=yearly)
            output_filename = convert2excel(report_name, source=output_filename, output=xls_output_filename)

        print "%s Report outputed to file %s" % (report_name, output_filename)

    def get_report_filename(self, name, extension='csv', yearly=False):
        cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if yearly:
            report_name = "%s_%s_yearly.%s" % (cur_date, name, extension)
        else :
            report_name = "%s_%s_monthly.%s" % (cur_date, name, extension)
        report_name = os.path.join(report_directory, report_name)

        output_filename = uniquify_filename(report_name)
        return output_filename

    def plot_charts_monthly(self):
        x = self.revenue.keys()
        revenue = numpy.array(self.revenue.values())
        cost = numpy.array(self.cost.values())
        ebitda = numpy.array(self.ebitda.values())
        deprication = self.deprication.values()
        #net_earning = self.net_earning.values()

        pylab.plot(revenue, label='REVENUE')
        pylab.plot(cost, label='COST')
        pylab.plot(ebitda, label='EBITDA')
        pylab.plot(deprication, label='deprication')
        #pylab.plot(net_earning, label='net_earning')

        pylab.xlabel("months")
        pylab.ylabel("EUROs")
        pylab.legend()
        pylab.grid(True, which="both",ls="-")
        pylab.axhline()
        pylab.axvline()
        pylab.title("Monthly data")
        pylab.show()

        #print deprication
        #print sum(deprication)

    def plot_charts_yearly(self):
        x = self.revenue_yearly.keys()

        revenue = self.revenue_yearly.values()
        cost = self.cost_yearly.values()
        ebitda = self.ebitda_yearly.values()
        deprication = self.deprication_yearly.values()
        #net_earning = self.net_earning_yearly.values()

        pylab.plot(revenue, label='REVENUE')
        pylab.plot(cost, label='COST')
        pylab.plot(ebitda, label='EBITDA')
        pylab.plot(deprication, label='deprication')
        #pylab.plot(net_earning, label='net_earning')

        pylab.xlabel("years")
        pylab.ylabel("EUROs")
        pylab.legend()
        pylab.grid(True, which="both",ls="-")
        pylab.axhline()
        pylab.axvline()
        pylab.title("Yearly data")
        pylab.show()

    def plot_price(self):
        pylab.plot(self.price.values())
        pylab.show()

    def plot_electricity(self):
        pylab.plot(self.electricity.values())
        pylab.show()

if __name__ == '__main__':
    mainconfig = MainConfig()
    energy_module = EnergyModule(mainconfig)
    technology_module = TechnologyModule(mainconfig, energy_module)
    subside_module = SubsidyModule(mainconfig)
    economic_module = EconomicModule(mainconfig, technology_module, subside_module)

    r = Report(mainconfig, economic_module)
    r.calc_report_values()

    #r.plot_charts_yearly()
    #r.plot_charts_monthly()
    #r.prepare_monthly_report_IS()
    r.prepare_report_IS_BS_CF_IRR(yearly=True)

    #print r.fixed_assets.values()
    #print r.assets.values()

    #print r.fixed_asset
    #r.plot_price()
    #print r.fixed_asset.values()
    #print r.revenue.values()
    #print r.revenue_yearly
    #print r.revenue[datetime.date(2000, 1, 31)]

    #print r.ebt.values()[:12]
    #print sum(r.ebt.values()[:12])
    #print r.tax.values()[:12]