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
        """dict with all months revenues since start project"""
        return  self.calc_report_monthly_values2(self.economic_module.getRevenue)

    @cached_property
    def deprication(self):
        """dict with all deprication since start project"""
        return  self.calc_report_monthly_values1(self.economic_module.calcDepricationMonthly)

    @cached_property
    def iterest_paid(self):
        """dict with all interest payments since start project"""
        return  self.calc_report_monthly_values1(self.economic_module.calculateInterests)

    @cached_property
    def tax(self):
        """dict with all taxes since start project"""
        results = OrderedDict()
        year_revenues = calc_yearly_values2(self.economic_module.getRevenue)
        for start_day, end_day in self.report_dates.items():
            result[end_day] += self.economic_module.calculateMonthlyTaxes(end_day, year_revenues[end_day.year])
        return  results

    @cached_property
    def cost(self):
        """dict with all costs since start project"""
        return  self.calc_report_monthly_values2(self.economic_module.getCosts)

    @cached_property
    def ebitda(self):
        """"""
        return self.calc_report_monthly_values1(self._calc_ebitda)

    @cached_property
    def ebit(self):
        """"""
        return self.calc_report_monthly_values1(self._calc_ebit)

    @cached_property
    def ebt(self):
        """"""
        return self.calc_report_monthly_values1(self._calc_ebt)

    @cached_property
    def net_earning(self):
        return self.calc_report_monthly_values1(self._calc_net_earning)

    @cached_property
    def fixed_asset(self):
        return self.calc_report_monthly_values1(self.economic_module.getMonthlyInvestments)


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


    def plot_charts(self):
        x = self.revenue.keys()
        revenue = numpy.array(self.revenue.values())
        cost = numpy.array(self.cost.values())

        ebitda = numpy.array(self.ebitda.values())
        deprication = self.deprication.values()
        pylab.plot(revenue, label='REVENUE')
        pylab.plot(cost, label='COST')
        pylab.plot(ebitda, label='EBITDA')
        pylab.plot(deprication, label='deprication')

        pylab.xlabel("months")
        pylab.ylabel("EUROs")
        pylab.legend()
        pylab.grid(True, which="both",ls="-")
        pylab.axhline()
        pylab.axvline()
        pylab.show()

        print deprication
        print sum(deprication)


if __name__ == '__main__':
    start_date = datetime.date(2000, 1, 1)
    end_date = datetime.date(2001, 12, 31)
    em = EnergyModule()
    technology_module = TechnologyModule(em)
    subside_module = SubsidyModule()
    ecm = EconomicModule(technology_module, subside_module)
    r = Report(ecm)
    #r.plot_charts()
    print r.fixed_asset.values()

    #print r.revenue[datetime.date(2000, 1, 31)]