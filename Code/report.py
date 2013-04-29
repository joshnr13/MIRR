import datetime
import pylab
import numpy
import csv
import os.path
from constants import report_directory

from collections import defaultdict, OrderedDict
from annex import Annuitet, last_day_month, next_month, first_day_month, cached_property, uniquify_filename, transponse_csv, add_header_csv, last_day_previous_month
from annex import accumulate, memoize

from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from ecm import EconomicModule

class Report():
    def __init__(self, economic_module):
        self.economic_module = economic_module
        self.report_get_dates()

    @cached_property
    def revenue(self):
        """dict with all months revenues since start project MONTHLY"""
        return  self.calc_report_monthly_values2(self.economic_module.getRevenue)

    @cached_property
    def revenue_yearly(self):
        """dict with all months revenues since start project MONTHLY"""
        return  self.aggregate_yearly(self.revenue)

    @cached_property
    def deprication(self):
        """dict with all deprication since start project MONTHLY"""
        return  self.calc_report_monthly_values1(self.economic_module.calcDepricationMonthly)

    @cached_property
    def deprication_yearly(self):
        """dict with all deprication since start project MONTHLY"""
        return  self.aggregate_yearly(self.deprication)

    @cached_property
    def iterest_paid(self):
        """dict with all interest payments since start project MONTHLY"""
        return  self.calc_report_monthly_values1(self.economic_module.calculateInterests)

    @cached_property
    def iterest_paid_yearly(self):
        """dict with all interest payments since start project YEARLY"""
        return  self.aggregate_yearly(self.iterest_paid)

    @cached_property
    def cost(self):
        """dict with all costs since start project MONTHLY"""
        return  self.calc_report_monthly_values2(self.economic_module.getCosts)

    @cached_property
    def cost_yearly(self):
        """dict with all costs since start project YEARLY"""
        return  self.aggregate_yearly(self.cost)

    @cached_property
    def ebitda(self):
        """MONTHLY"""
        return self.calc_report_monthly_values1(self._calc_ebitda)

    @cached_property
    def ebitda_yearly(self):
        """YEARLY"""
        return self.aggregate_yearly(self.ebitda)

    @cached_property
    def ebit(self):
        """MONTHLY"""
        return self.calc_report_monthly_values1(self._calc_ebit)

    @cached_property
    def ebit_yearly(self):
        """YEARLY"""
        return self.aggregate_yearly(self.ebit)

    @cached_property
    def ebt(self):
        """MONTHLY"""
        return self.calc_report_monthly_values1(self._calc_ebt)

    @cached_property
    def ebt_yearly(self):
        """YEARLY"""
        return self.aggregate_yearly(self.ebt)

    @cached_property
    def tax(self):
        """dict with all taxes since start project MONTHLY"""
        return self._calc_tax()

    @cached_property
    def tax_yearly(self):
        """dict with all taxes since start project YEARLY"""
        return self.aggregate_yearly(self.tax)

    @cached_property
    def net_earning(self):
        """MONTHLY"""
        return self.calc_report_monthly_values1(self._calc_net_earning)

    @cached_property
    def net_earning_yearly(self):
        """YEARLY"""
        return self.aggregate_yearly(self.net_earning)

    @cached_property
    def investments(self):
        """return investments MONTHLY"""
        return self.calc_report_monthly_values1(self.economic_module.getMonthlyInvestments)

    @cached_property
    def fixed_assets(self):
        """return current_asset MONTHLY"""
        return self.calc_report_monthly_values1(self._calc_fixed_assets)

    @cached_property
    def assets(self):
        """return current_asset MONTHLY"""
        return self.calc_report_monthly_values1(self._calc_assets)

    @cached_property
    def fixed_asset_yearly(self):
        """YEARLY"""
        return self.aggregate_yearly(self.fixed_assets)

    @cached_property
    def price(self):
        """return kwh price for electricity MONTHLY"""
        return self.calc_report_monthly_values1(self.economic_module.getPriceKwh)


    @cached_property
    def electricity(self):
        """return volume of for electricity MONTHLY"""
        return self.calc_report_monthly_values2(self.economic_module.technology_module.getElectricityProduction)

    @cached_property
    def inventory(self):
        """return inventories MONTHLY - NOT IMPLEMENTED"""
        return self.calc_report_monthly_values1(self.return_zero)

    @cached_property
    def operating_receivable(self):
        """return operating_receivable MONTHLY - NOT IMPLEMENTED"""
        return self.calc_report_monthly_values1(self.return_zero)

    @cached_property
    def short_term_investment(self):
        """return short_term_investment MONTHLY - NOT IMPLEMENTED"""
        return self.calc_report_monthly_values1(self.return_zero)

    @cached_property
    def assets_bank_account(self):
        """return assets_bank_account MONTHLY - NOT IMPLEMENTED"""
        return self.calc_report_monthly_values1(self.return_zero)

    @cached_property
    def current_assets(self):
        """return current_asset MONTHLY """
        return self.calc_report_monthly_values1(self._calc_current_assets)

    #######################################################################

    @cached_property
    def paid_in_capital(self):
        """return paid_in_capital MONTHLY - NOT IMPLEMENTED"""
        return self.calc_report_monthly_values1(self.return_zero)

    @cached_property
    def retained_earnings(self):
        """return retained_earnings MONTHLY"""
        return self.net_earning

    @cached_property
    def unallocated_earnings(self):
        """return unallocated_earnings - sum of all previous retained_earnings MONTHLY"""
        return accumulate(self.net_earning)

    #@memoize
    def accumulated_earnings_to(self, to_date):
        """return accumulated eanings from start project to @to_date -1 day"""
        eanings = 0
        for date in self.report_dates.values():
            if date < to_date:  #!!! NOT EQUAL
                eanings += self._calc_net_earning(date)
        return eanings

    def return_zero(self, date):
        """methon for non implemented calculations"""
        return 0

    def aggregate_yearly(self, data):
        """Aggregate monthly values to yearly"""
        result = OrderedDict()
        for date, value in data.items():
            if result.has_key(date.year):
                result[date.year] += value
            else:
                result[date.year] = value
        return result

    def _calc_tax(self):
        """dict with all taxes since start project"""
        results = OrderedDict()

        for start_day, end_day in self.report_dates.items():
            result = self._calc_month_taxes(end_day)
            if results.has_key(end_day):
                results[end_day] += result
            else:
                results[end_day] = result

        return  results

    #@memoize
    def _calc_ebitda(self, date):
        """calculation of ebitda = revenues - costs"""
        return self.revenue[date] - self.cost[date]

    #@memoize
    def _calc_ebit(self, date):
        """calculation of ebit = ebitda - deprication"""
        return self.ebitda[date] - self.deprication[date]

    #@memoize
    def _calc_ebt(self, date):
        """calculation of ebt = ebit - interests paid"""
        return self.ebit[date] - self.iterest_paid[date]

    #@memoize
    def _calc_net_earning(self, date):
        """calculation of net_earning = ebt - taxes"""
        return self.ebt[date] - self.tax[date]

    def _calc_something(self, date_from, date_to): pass



    ##@memoize
    def _calc_month_taxes(self, date):
        """
        tax = EBT in the year * taxrate
        tax = taxrate * max(EBT*50%; EBT - accumulated loss)
        entered only in december
        """
        print date
        accumulated_earnings = self.accumulated_earnings_to(date)
        if date.month == 12:
            year_ebt = [f]
            if year_ebt <= 0:
                return 0
            elif year_ebt + accumulated_earnings <= 0:
                return 0
            else:
                tax_rate = self.economic_module.getTaxRate()
                return taxrate * max(year_ebt/2.0, year_ebt + accumulated_earnings)
        else:
            return 0

    #@memoize
    def _calc_current_assets(self, date):
        """calculating current assests as sum"""
        return (
        self.inventory[date] +
        self.operating_receivable[date] +
        self.short_term_investment[date] +
        self.assets_bank_account[date] )

    #@memoize
    def _calc_assets(self, date):
        """calculating assests as sum fixed + current"""
        return ( self.current_assets[date] + self.fixed_assets[date] )

    def _calc_fixed_assets(self, date):
        """calculating fixed assests as diff between investment and deprication"""
        prev_month_last_day = last_day_previous_month(date)
        if self.investments.has_key(prev_month_last_day):
            return (self._calc_fixed_assets(prev_month_last_day) - self.deprication[date])
        else:
            return (self.investments[date])

    def calc_yearly_values2(self, func):
        """Calculates monthly values using 2 dates -first_day and last_day in month
        return dict [year]=value"""
        results = OrderedDict()
        for start_day, end_day in self.report_dates.items():
            if results.has_key(start_day.year):
                result[end_day.year] += func(start_day, end_day)
            else:
                result[end_day.year] = func(start_day, end_day)

        return results

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
        date = first_day_month(self.economic_module.start_date)
        date_to = self.economic_module.end_date

        while True:
            report_date = last_day_month(date)
            key = first_day_month(date)
            report_dates[key] = report_date

            date = next_month(date)
            if  date > date_to:
                break

        self.report_dates = report_dates

    def report_get_lastdays(self):
        return self.report_dates.values()

    def report_get_firstdays(self):
        return self.report_dates.keys()

    def prepare_monthly_report_IS(self):
        """Prepares and saves monthly IS report in csv file"""
        cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
        report_name = "%s_IS_monthly.csv" % (cur_date, )
        report_name = os.path.join(report_directory, report_name)
        output_filename = uniquify_filename(report_name)

        IS_ROWS = [self.revenue, self.cost, self.ebitda, self.deprication, self.ebit,
                self.iterest_paid, self.ebt, self.tax, self.net_earning ]

        NAMES = ['Dates', 'Revenue', 'Costs', 'EBITDA', 'Deprication', 'EBIT',
                 'Interest paid', 'EBT', 'Taxes', 'Net earnings']

        with open(output_filename,'wb') as f:
            w = csv.DictWriter(f, IS_ROWS[0].keys(), delimiter=';')
            w.writeheader()
            w.writerows(IS_ROWS)

        transponse_csv(output_filename)
        add_header_csv(output_filename, NAMES)
        transponse_csv(output_filename)

        print "IS Report outputed to file %s" % output_filename

    def prepare_monthly_report_BS(self):
        """Prepares and saves monthly BS report in csv file"""
        cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
        report_name = "%s_BS_monthly.csv" % (cur_date, )
        report_name = os.path.join(report_directory, report_name)
        output_filename = uniquify_filename(report_name)

        BS_ROWS = [self.fixed_assets, self.current_assets, self.inventory,
                   self.operating_receivable, self.short_term_investment,
                   self.assets_bank_account, self.assets,
                   self.paid_in_capital, self.retained_earnings, self.unallocated_earnings]

        NAMES = ['Dates', 'Fixed Assests', 'Current Assets', 'Inventories',
                 'Operating Receivables', 'Short-Term Investments',
                 'Assets On Bank Accounts', 'Assets',
                 'Paid-In Capital', 'Retained Earnings', 'Unallocated Earnings']

        with open(output_filename,'wb') as f:
            w = csv.DictWriter(f, BS_ROWS[0].keys(), delimiter=';')
            w.writeheader()
            w.writerows(BS_ROWS)

        transponse_csv(output_filename)
        add_header_csv(output_filename, NAMES)
        transponse_csv(output_filename)

        print "BS Report outputed to file %s" % output_filename

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

    energy_module = EnergyModule()
    technology_module = TechnologyModule(energy_module)
    subside_module = SubsidyModule()
    economic_module = EconomicModule(technology_module, subside_module)
    r = Report(economic_module)

    r.plot_charts_yearly()
    r.plot_charts_monthly()
    r.prepare_monthly_report_IS()
    r.prepare_monthly_report_BS()

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