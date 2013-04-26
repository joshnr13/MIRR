import datetime
import pylab
import numpy

from collections import defaultdict, OrderedDict

from annex import Annuitet, last_day_month, next_month, first_day_month, cached_property
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
    def fixed_asset(self):
        """MONTHLY"""
        return self.calc_report_monthly_values1(self.economic_module.getMonthlyInvestments)

    @cached_property
    def fixed_asset_yearly(self):
        """YEARLY"""
        return self.aggregate_yearly(self.fixed_asset)

    @cached_property
    def price(self):
        """return kwh price for electricity at given day"""
        return self.calc_report_monthly_values1(self.economic_module.getPriceKwh)

    @cached_property
    def electricity(self):
        """return kwh price for electricity at given day"""
        return self.calc_report_monthly_values2(self.economic_module.technology_module.getElectricityProduction)

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
        year_ebt = self.ebt_yearly
        for start_day, end_day in self.report_dates.items():
            if results.has_key(end_day):
                results[end_day] += self.calculateMonthlyTaxes(end_day, year_ebt[end_day.year])
            else:
                results[end_day] = self.calculateMonthlyTaxes(end_day, year_ebt[end_day.year])

        return  results

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
        print("self.ebt[date] = %s" %(self.ebt[date],))  #debug-info-
        print("self.tax[date] = %s" %(self.tax[date],))  #debug-info-
        return self.ebt[date] - self.tax[date]

    def calculateMonthlyTaxes(self, date, year_ebt):
        """EBT in the year * 20% enetered only in december"""
        if date.month == 12:
            return year_ebt * self.economic_module.getTaxRate()
        else:
            return 0

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


    def plot_charts_monthly(self):
        x = self.revenue.keys()
        revenue = numpy.array(self.revenue.values())
        cost = numpy.array(self.cost.values())
        ebitda = numpy.array(self.ebitda.values())
        deprication = self.deprication.values()
        net_earning = self.net_earning.values()

        pylab.plot(revenue, label='REVENUE')
        pylab.plot(cost, label='COST')
        pylab.plot(ebitda, label='EBITDA')
        pylab.plot(deprication, label='deprication')
        pylab.plot(net_earning, label='net_earning')

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
        net_earning = self.net_earning_yearly.values()

        pylab.plot(revenue, label='REVENUE')
        pylab.plot(cost, label='COST')
        pylab.plot(ebitda, label='EBITDA')
        pylab.plot(deprication, label='deprication')
        pylab.plot(net_earning, label='net_earning')

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

    #r.plot_price()
    #print r.fixed_asset.values()
    #print r.revenue.values()
    #print r.revenue_yearly
    #print r.revenue[datetime.date(2000, 1, 31)]

    #print r.ebt.values()[:12]
    #print sum(r.ebt.values()[:12])
    #print r.tax.values()[:12]