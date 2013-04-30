import datetime
import pylab
import numpy
import csv
import os.path
from constants import report_directory

from collections import defaultdict, OrderedDict
from annex import Annuitet, last_day_month, next_month, first_day_month, cached_property, uniquify_filename, transponse_csv, add_header_csv, last_day_previous_month
from annex import accumulate, memoize, OrderedDefaultdict, is_last_day_year, get_months_range
from constants import BS_NAMES, BS_ROWS, IS_NAMES, IS_ROWS

from tm import TechnologyModule
from em import EnergyModule
from sm import SubsidyModule
from ecm import EconomicModule

class Report():
    def __init__(self, economic_module):
        self.economic_module = economic_module
        self.report_get_dates()

    def calc_values(self):
        """Main function to cacl all values for reports"""

        self.init_attrs()
        for start_day, end_day in self.report_dates.items():
            self.calc_monthly_values(start_day, end_day)
            if is_last_day_year(end_day):
                self.calc_yearly_values(end_day)

    def init_attrs(self):
        """Creating attrs for monthly and yearly values"""
        attrs = ['revenue', 'cost', 'deprication', 'iterest_paid', 'ebitda', 'ebit', 'ebt',
                 'tax', 'net_earning', 'investment', 'fixed_asset', 'asset' ,
                 'inventory', 'operating_receivable', 'short_term_investment',
                 'asset_bank_account', 'paid_in_capital', 'current_asset',
                 'retained_earning', 'unallocated_earning', 'retained_earning']
        for attr in attrs:
            setattr(self, attr, OrderedDict())
            setattr(self, attr+"_y", OrderedDefaultdict(int))

    def calc_monthly_values(self, start_day, end_day):
        """Main function to calc montly value for reports"""
        M = end_day

        self.revenue[M] = self.economic_module.getRevenue(start_day, end_day)
        self.deprication[M] = self.economic_module.calcDepricationMonthly(end_day)
        self.iterest_paid[M] = self.economic_module.calculateInterests(end_day)
        self.cost[M] = self.economic_module.getCosts(start_day, end_day)
        self.ebitda[M] = self._calc_ebitda(end_day)
        self.ebit[M] = self._calc_ebit(end_day)
        self.ebt[M] = self._calc_ebt(end_day)
        self.tax[M] = self._calc_tax(end_day)
        self.net_earning[M] = self._calc_net_earning(end_day)

        self.investment[M] = self.economic_module.getMonthlyInvestments(end_day)
        self.fixed_asset[M] = self._calc_fixed_assets(end_day)

        self.inventory[M] = 0 #NOT IMPLEMENTED
        self.operating_receivable[M] = 0 #NOT IMPLEMENTED
        self.short_term_investment[M] = 0 #NOT IMPLEMENTED
        self.asset_bank_account[M] = 0 #NOT IMPLEMENTED
        self.paid_in_capital[M] = 0 #NOT IMPLEMENTED

        self.current_asset[M] = self._calc_current_assets(end_day)
        self.retained_earning[M] = self.net_earning[M]
        self.unallocated_earning[M] = self._calc_unallocated_earnings(M)

        self.asset[M] = self._calc_assets(end_day)

    def calc_yearly_values(self, end_day_y):
        """Main function to calc yearly value for reports"""

        for start_day_m, end_day_m in self.report_dates_y[end_day_y]:
            Y = end_day_y
            M = end_day_m
            self.revenue_y[Y] += self.revenue[M]
            self.deprication_y[Y] += self.deprication[M]
            self.iterest_paid_y[Y] += self.iterest_paid[M]
            self.cost_y[Y] += self.cost[M]
            self.ebitda_y[Y] += self.ebitda[M]
            self.ebit_y[Y] += self.ebit[M]
            self.ebt_y[Y] += self.ebt[M]
            self.tax_y[Y] += self.tax[M]
            self.net_earning_y[Y] += self.net_earning[M]

            self.investment_y[Y] += self.investment[M]
            self.fixed_asset_y[Y] += self.fixed_asset[M]
            self.asset_y[Y] += self.asset[M]

            self.inventory_y[Y] += self.inventory[M]

    def _calc_unallocated_earnings(self, date):
        """Calculating accumulated earnings """
        prev_month_date = last_day_previous_month(date)
        prev_unallocated_earning = self.unallocated_earning.get(prev_month_date, 0)
        return prev_unallocated_earning + self.net_earning[date]

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
                return taxrate * max(year_ebt/2.0, year_ebt + accumulated_earnings)
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
        prev_month_last_day = last_day_previous_month(date)

        prev_fixed_asset = self.fixed_asset.get(prev_month_last_day, 0)
        cur_investments = self.investment[date]
        cur_deprication = self.deprication[date]

        return (cur_investments + prev_fixed_asset - cur_deprication)

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

        date = first_day_month(self.economic_module.start_date)
        date_to = self.economic_module.end_date

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

    def prepare_rows():pass

    def write_report(self, output_filename, header, rows):
        """write report to file staying @free_lines in the head"""

        rows = [getattr(self, attr) for attr in rows]
        with open(output_filename,'ab') as f:
            w = csv.DictWriter(f, rows[0].keys(), delimiter=';')
            w.writeheader()
            w.writerows(rows)

        transponse_csv(output_filename)
        add_header_csv(output_filename, header)
        transponse_csv(output_filename)

    def prepare_monthly_report_BS(self):
        """Prepares and saves monthly BS report in csv file"""
        output_filename = self.get_report_filename('BS')
        self.write_report(output_filename, BS_NAMES, BS_ROWS)
        print "BS Report outputed to file %s" % output_filename


    def prepare_monthly_report_IS(self):
        """Prepares and saves monthly IS report in csv file"""
        output_filename = self.get_report_filename('IS')
        self.write_report(output_filename, IS_NAMES, IS_ROWS)
        print "IS Report outputed to file %s" % output_filename

    def prepare_monthly_report_IS_BS(self):
        output_filename = self.get_report_filename('IS-BS')
        bs_filename = output_filename + "_BS"
        is_filename = output_filename + "_IS"
        self.write_report(bs_filename, BS_NAMES, BS_ROWS)
        self.write_report(is_filename, IS_NAMES, IS_ROWS)

        content = "\n"
        for f in [is_filename, bs_filename]:
            content += open(f).read() + '\n\n\n'
            os.remove(f)

        with open(output_filename,'wb') as output:
            output.write(content)

        print "IS-BS Report outputed to file %s" % output_filename

    def get_report_filename(self, name):
        cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
        report_name = "%s_%s_monthly.csv" % (cur_date, name)
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

    energy_module = EnergyModule()
    technology_module = TechnologyModule(energy_module)
    subside_module = SubsidyModule()
    economic_module = EconomicModule(technology_module, subside_module)
    r = Report(economic_module)
    r.calc_values()

    #r.plot_charts_yearly()
    #r.plot_charts_monthly()
    #r.prepare_monthly_report_IS()
    r.prepare_monthly_report_IS_BS()

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