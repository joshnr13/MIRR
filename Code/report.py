from ecm import EconomicModule
from annex import Annuitet, last_day_month, next_month, first_day_month
import datetime
from collections import defaultdict

class Report():
    def __init__(self, economic_module):
        self.economic_module = economic_module
        self.report_get_dates()

    def report_get_all_revenue(self):
        """saves all months revenues since start project"""
        self.revenues = self.calc_report_monthly_values2(self.economic_module.getRevenue)

    def report_get_all_amortization(self):
        """saves all amortization since start project"""
        self.amortization = self.calc_report_monthly_values2(self.economic_module.calcAmortizationMonthly)

    def report_get_all_iterest_paymnets(self):
        """saves all interest payments since start project"""
        self.interest_payments = self.calc_report_monthly_values1(self.economic_module.calculateInterests)

    def report_get_all_taxes(self):
        """saves all taxe since start project"""
        results = {}
        year_revenues = calc_yearly_values2(self.economic_module.getRevenue)
        for start_day, end_day in self.report_dates.items():
            result[end_day] += self.economic_module.calculateMonthlyTaxes(end_day, year_revenues[end_day.year])
        self.taxes = results


    def report_get_all_investments(self):
        """saves all investments since start project"""
        pass





    def calc_yearly_values2(self, func):
        """Calculates monthly values using 2 dates -first_day and last_day in month
        return dict [year]=value"""
        results = {}
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
        results = {}
        for start_day, end_day in self.report_dates.items():
            results[end_day] = func(start_day, end_day)

        return results

    def calc_report_monthly_values1(self, func):
        """Calculates monthly values using 1 date - last_day in month
        return  dict[end_day] = value"""
        results = {}
        for end_day in self.report_dates.values():
            results[end_day] = func(end_day)
        return results

    def report_get_dates(self):
        """saves all dates for report (last day of each month)
        dic[first_day_month]=last_day_month
        """
        report_dates = {}
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
