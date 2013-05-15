#!/usr/bin/env python
# -*- coding utf-8 -*-

import os
import csv
import pylab
import datetime

from constants import report_directory, BS, IS, CF, REPORT_ROUNDING
from annex import uniquify_filename, transponse_csv, add_header_csv
from annex import convert2excel, combine_files, get_only_digits
from collections import OrderedDict

class ReportOutput():
    def __init__(self, report_data):
        self.r = report_data

    def prepare_report_BS_db(self, excel=False, yearly=False):
        report_name = 'IS_db'
        report_dic = BS

        output_filename = self.get_report_filename(report_name)
        rows = self.prepare_rows(report_dic.values(), yearly)
        header = report_dic.keys()

        self.write_report(rows, header, output_filename, BS)
        print "%s Report outputed to file %s" % (report_name, output_filename)

    def prepare_report_IS_BS_CF_IRR(self, excel=False, yearly=False):
        report_name = 'IS-BS-CF'
        output_filename = self.get_report_filename(report_name, yearly=yearly)

        bs_filename = output_filename + "_BS"
        is_filename = output_filename + "_IS"
        cf_filename = output_filename + "_CF"

        bs_rows = self.prepare_rows(BS.values(), yearly)
        bs_header = BS.keys()

        is_rows = self.prepare_rows(IS.values(), yearly)
        is_header = IS.keys()

        cf_rows = self.prepare_rows(CF.values(), yearly)
        cf_header = CF.keys()

        self.write_report(bs_rows, bs_header, bs_filename)
        self.write_report(is_rows, is_header, is_filename)
        self.write_report(cf_rows, cf_header, cf_filename)

        combine_list = [bs_filename, is_filename, cf_filename]
        combine_files(combine_list, output_filename)

        if excel:
            xls_output_filename = self.get_report_filename(report_name, 'xlsx', yearly=yearly)
            output_filename = convert2excel(source=output_filename, output=xls_output_filename)

        print "%s Report outputed to file %s" % (report_name, output_filename)

    def get_report_fields(self, rows_str, yearly):
        postfix = "" if not yearly else "_y"
        rows = [getattr(self.r, attr+postfix) for attr in rows_str if attr]
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

    def write_report(self, rows, header, output_filename ):
        """write report to file
        """
        with open(output_filename,'ab') as f:
            w = csv.DictWriter(f, rows[0].keys(), delimiter=';')
            w.writeheader()
            w.writerows(rows)

        transponse_csv(output_filename)
        add_header_csv(output_filename, header)
        transponse_csv(output_filename)


    def get_report_filename(self, name, extension='csv', yearly=False):
        cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if yearly:
            report_name = "%s_%s_y.%s" % (cur_date, name, extension)
        else :
            report_name = "%s_%s_monthly.%s" % (cur_date, name, extension)
        report_name = os.path.join(report_directory, report_name)

        output_filename = uniquify_filename(report_name)
        return output_filename

    def plot_charts_monthly(self):
        x = self.r.revenue.keys()
        revenue = get_only_digits(self.r.revenue)
        cost = get_only_digits(self.r.cost)
        ebitda = get_only_digits(self.r.ebitda)
        deprication = get_only_digits(self.r.deprication)
        #net_earning = get_only_digits(self.net_earning)

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

        revenue = get_only_digits(self.r.revenue_y)
        cost = get_only_digits(self.r.cost_y)
        ebitda = get_only_digits(self.r.ebitda_y)
        deprication = get_only_digits(self.r.deprication_y)
        #net_earning = get_only_digits(self.net_earning_y)

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
        pylab.plot(get_only_digits(self.r.price))
        pylab.show()

    def plot_electricity(self):
        pylab.plot(get_only_digits(self.r.electricity))
        pylab.show()


if __name__ == '__main__':
    import os.path

    from collections import OrderedDict
    from annex import Annuitet, last_day_month, next_month, first_day_month, cached_property, uniquify_filename, transponse_csv, add_header_csv, last_day_previous_month
    from annex import accumulate, memoize, OrderedDefaultdict, is_last_day_year, OrderedDefaultdict
    from annex import add_start_project_values, get_months_range, csv2xlsx, month_number_days

    from constants import PROJECT_START, report_directory, REPORT_ROUNDING
    from tm import TechnologyModule
    from em import EnergyModule
    from sm import SubsidyModule
    from ecm import EconomicModule
    from config_readers import MainConfig
    from report import Report

    mainconfig = MainConfig()
    energy_module = EnergyModule(mainconfig)
    technology_module = TechnologyModule(mainconfig, energy_module)
    subside_module = SubsidyModule(mainconfig)
    economic_module = EconomicModule(mainconfig, technology_module, subside_module)

    r = Report(mainconfig, economic_module)
    r.calc_report_values()
    o = ReportOutput(r)
    o.prepare_report_IS_BS_CF_IRR()