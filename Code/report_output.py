#!/usr/bin/env python
# -*- coding utf-8 -*-

import os
import csv
import pylab
import datetime

from constants import report_directory, BS, IS, CF, NPV, REPORT_ROUNDING, SECOND_SHEET
from annex import uniquify_filename, transponse_csv, add_header_csv
from annex import convert2excel, combine_files, get_only_digits, add_second_sheet_excel
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
        npv_filename = output_filename +  "_NPV"
        ss_filename = output_filename +  "_SS"

        bs_rows = self.prepare_rows(BS.values(), yearly)
        bs_header = BS.keys()

        is_rows = self.prepare_rows(IS.values(), yearly)
        is_header = IS.keys()

        cf_rows = self.prepare_rows(CF.values(), yearly)
        cf_header = CF.keys()

        npv_rows = self.prepare_rows(NPV.values(), yearly)
        npv_header = NPV.keys()

        ss_rows = self.prepare_rows(SECOND_SHEET.values(), yearly)
        ss_header = SECOND_SHEET.keys()

        self.write_report(bs_rows, bs_header, bs_filename)
        self.write_report(is_rows, is_header, is_filename)
        self.write_report(cf_rows, cf_header, cf_filename)
        self.write_report(npv_rows, npv_header, npv_filename)
        self.write_report(ss_rows, ss_header, ss_filename)

        combine_list = [bs_filename, is_filename, ss_filename, cf_filename, npv_filename]
        combine_files(combine_list, output_filename)

        if excel:
            xls_output_filename = self.get_report_filename(report_name, 'xlsx', yearly=yearly)
            output_filename = convert2excel(source=output_filename, output=xls_output_filename)
            #add_second_sheet_excel(output_filename, ss_filename)

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
                    if v <= 5:
                        result[k] = round(v, REPORT_ROUNDING*2)
                    else:
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