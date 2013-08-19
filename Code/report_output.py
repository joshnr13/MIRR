#!/usr/bin/env python
# -*- coding utf-8 -*-

import os
import csv
import pylab
import datetime

from constants import report_directory, BS, IS, CF, NPV, REPORT_ROUNDING, ELPROD, SOURCE
from annex import uniquifyFilename, transponseCsv, addHeaderCsv, addYearlyPrefix
from annex import convert2excel, combineFiles, getOnlyDigits, addSecondSheetXls
from collections import OrderedDict
from database import Database

db = Database()

class ReportOutput():
    def __init__(self, report_data):
        self.r = report_data


    def prepare_report_filenames(self, yearly, from_db):
        self.report_name = 'IS-BS-CF'
        if from_db:
            self.report_name += "_s%s_i%s" %  from_db
        self.output_filename = self.get_report_filename(self.report_name, yearly=yearly)

        self.bs_filename = self.output_filename + "_BS"
        self.is_filename = self.output_filename + "_IS"
        self.cf_filename = self.output_filename + "_CF"
        self.npv_filename = self.output_filename +  "_NPV"
        self.ss_filename = self.output_filename +  "_SS"
        self.source_filename = self.output_filename + "_SOURCE"

    def prepare_report_headers(self):
        self.bs_header = BS.keys()
        self.is_header = IS.keys()
        self.cf_header = CF.keys()
        self.npv_header = NPV.keys()
        self.ss_header = ELPROD.keys()

    def prepare_report_values(self, yearly, from_db):

        self.prepare_source(*from_db)
        if from_db:
            self.prepare_report_values_db(yearly, from_db)
        else:
            self.prepare_report_values_local(yearly)

    def prepare_report_values_db(self, yearly, from_db):
        """prepares rows values from database based on dict @from_db
        with simulation and iteration keys limitations"""

        simulation_no, iteration_no = from_db
        report_header = db.get_report_header(simulation_no, iteration_no, yearly)

        self.bs_rows = self.get_and_process_report_values_db(simulation_no, BS.values(),  yearly, iteration_no, report_header)
        self.is_rows = self.get_and_process_report_values_db(simulation_no, IS.values(),  yearly, iteration_no, report_header)
        self.cf_rows = self.get_and_process_report_values_db(simulation_no, CF.values(),  yearly, iteration_no, report_header)
        self.npv_rows = self.get_and_process_report_values_db(simulation_no, NPV.values(),  yearly, iteration_no, report_header)
        self.ss_rows = self.get_and_process_report_values_db(simulation_no, ELPROD.values(),  yearly, iteration_no, report_header)

    def get_and_process_report_values_db(self, simulation_no, fields, yearly, iteration_no, report_header):
        double_round = REPORT_ROUNDING*2
        single_round = REPORT_ROUNDING
        def round_value(v):
            if isinstance(v, float):
                if  v > 5 or v < -5:
                    return   round(v, single_round)
                else:
                    return   round(v, double_round)
            else:
                return v

        db_values = db.get_iteration_values_from_db(simulation_no, fields, yearly, iteration_no=iteration_no)
        result = []
        for field in fields:
            if not field:
                continue
            field = addYearlyPrefix(field, yearly)
            d = OrderedDict( (date,round_value(value)) for date,value in zip(report_header,db_values[field]) )
            result.append(d)

        return result

    def prepare_report_values_local(self, yearly):
        self.bs_rows = self.prepare_rows(BS.values(), yearly)
        self.is_rows = self.prepare_rows(IS.values(), yearly)
        self.cf_rows = self.prepare_rows(CF.values(), yearly)
        self.npv_rows = self.prepare_rows(NPV.values(), yearly)
        self.ss_rows = self.prepare_rows(ELPROD.values(), yearly)

    def write_report_values(self, yearly):
        self.write_report(self.bs_rows, self.bs_header, self.bs_filename)
        self.write_report(self.is_rows, self.is_header, self.is_filename)
        self.write_report(self.cf_rows, self.cf_header, self.cf_filename)
        self.write_report(self.npv_rows, self.npv_header, self.npv_filename)
        self.write_report(self.ss_rows, self.ss_header, self.ss_filename)

        combine_list = [self.bs_filename, self.is_filename, self.ss_filename, self.cf_filename, self.npv_filename]
        combineFiles(combine_list, self.output_filename)

        xls_output_filename = self.get_report_filename(self.report_name, 'xlsx', yearly=yearly)
        self.output_filename = convert2excel(source=self.output_filename, output=xls_output_filename)
        addSecondSheetXls(self.output_filename, self.source_filename )

    def prepare_report_IS_BS_CF_IRR(self, from_db=False,  yearly=False, ):
        self.prepare_report_filenames(yearly, from_db)
        self.prepare_report_headers()
        self.prepare_report_values(yearly, from_db)
        self.write_report_values(yearly)
        print "%s Report outputed to file %s" % (self.report_name, self.output_filename)

    def get_report_fields(self, rows_str, yearly):
        postfix = "" if not yearly else "_y"
        obj = self.r

        rows = [getattr(obj, attr+postfix) for attr in rows_str if attr]
        return rows

    def round_rows_dicts(self, rows):
        double_round = REPORT_ROUNDING*2
        single_round = REPORT_ROUNDING
        for row in rows:
            for k, v in row.items():
                if isinstance(v, float):
                    if  v > 5 or v < -5:
                        row[k] = round(v, single_round)
                    else:
                        row[k] = round(v, double_round)

    def prepare_rows(self, rows_str, yearly):
        """Prepares rows for outputing to report
        + Rounding
        + Can output monthly (without change) and yearly (+_y) values ---> postfix
        """
        rows = self.get_report_fields(rows_str, yearly)
        self.round_rows_dicts(rows)
        return rows


    def write_report(self, rows, header, output_filename ):
        """write report to file
        """
        with open(output_filename,'ab') as f:
            w = csv.DictWriter(f, rows[0].keys(), delimiter=';')
            w.writeheader()
            w.writerows(rows)

        transponseCsv(output_filename)
        addHeaderCsv(output_filename, header)
        transponseCsv(output_filename)


    def get_report_filename(self, name, extension='csv', yearly=False):
        cur_date = datetime.datetime.now().strftime("%Y%m%d")
        if yearly:
            report_name = "%s_%s_yearly.%s" % (cur_date, name, extension)
        else :
            report_name = "%s_%s_monthly.%s" % (cur_date, name, extension)
        report_name = os.path.join(report_directory, report_name)

        output_filename = uniquifyFilename(report_name)
        return output_filename


    def prepare_source(self, simulation_no, iteration_no):
        """Prepares second sheet date for excel
        saves data to csv file
        """
        source = db.get_iteration_values_from_db(simulation_no, SOURCE.values(), False, iteration_no=iteration_no)

        with open(self.source_filename,'wb') as f:
            w = csv.writer(f, delimiter=';')
            for title,source_key  in SOURCE.items():
                dic_values = source[source_key]
                header = dic_values.keys()
                values = dic_values.values()
                w.writerow([title])
                for name, value in dic_values.items():
                    if isinstance(value, (dict, list)):
                        continue
                    else:
                        w.writerow([name, value])
                w.writerow('')

if __name__ == '__main__':
    import os.path

    from collections import OrderedDict
    from annex import Annuitet, lastDayMonth, firstDayMonth, cached_property, uniquifyFilename, transponseCsv, addHeaderCsv, lastDayPrevMonth
    from annex import memoize, OrderedDefaultdict, isLastDayYear, OrderedDefaultdict
    from annex import csv2xlsx, nubmerDaysInMonth, timer

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

    @timer
    def test_speed():
        r = Report(mainconfig, economic_module)
        r.calc_report_values()
        o = ReportOutput(r)
        o.prepare_report_IS_BS_CF_IRR(from_db=(9, 1), yearly=True)
        #o.prepare_report_IS_BS_CF_IRR()


    #test_speed()
    o = ReportOutput(None)
    o.source_filename = r"C:\temp2.csv"
    print o.prepare_source(20, 1)