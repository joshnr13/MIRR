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

class ReportOutput():
    """class for preparing data for XLS report from DB and writing it to file """
    def __init__(self, report_data):
        self.r = report_data
        self.db = Database()

    def prepareReportFilenames(self, yearly, from_db):
        """Generate standart filenames for all parts of report
        this files will be deleted after combining to final report
        """
        self.report_name = 'IS-BS-CF'
        if from_db:
            self.report_name += "_s%s_i%s" %  from_db
        self.output_filename = self.getReportFilename(self.report_name, yearly=yearly)

        self.bs_filename = self.output_filename + "_BS"
        self.is_filename = self.output_filename + "_IS"
        self.cf_filename = self.output_filename + "_CF"
        self.npv_filename = self.output_filename +  "_NPV"
        self.ss_filename = self.output_filename +  "_SS"
        self.source_filename = self.output_filename + "_SOURCE"

    def prepareReportHeaders(self):
        """prepare header (titles) for xls report"""
        self.bs_header = BS.keys()
        self.is_header = IS.keys()
        self.cf_header = CF.keys()
        self.npv_header = NPV.keys()
        self.ss_header = ELPROD.keys()

    def prepareReportValues(self, yearly, from_db):
        """main method to prepare values for report"""
        self.prepareSourceSecondSheetExcel(*from_db)
        if from_db:
            self.getReportValuesDb(yearly, from_db)
        else:
            self.getReportValuesLocal(yearly)

    def getReportValuesDb(self, yearly, from_db):
        """prepares rows values from database based on dict @from_db
        with simulation and iteration keys limitations"""

        simulation_no, iteration_no = from_db
        report_header = self.db.getReportHeader(simulation_no, iteration_no, yearly)

        self.bs_rows = self.getProcessReportValuesDb(simulation_no, BS.values(),  yearly, iteration_no, report_header)
        self.is_rows = self.getProcessReportValuesDb(simulation_no, IS.values(),  yearly, iteration_no, report_header)
        self.cf_rows = self.getProcessReportValuesDb(simulation_no, CF.values(),  yearly, iteration_no, report_header)
        self.npv_rows = self.getProcessReportValuesDb(simulation_no, NPV.values(),  yearly, iteration_no, report_header)
        self.ss_rows = self.getProcessReportValuesDb(simulation_no, ELPROD.values(),  yearly, iteration_no, report_header)

    def getReportValuesLocal(self, yearly):
        """Takes report values from current report, now not used! - because we take values from db"""
        self.bs_rows = self.prepareRows(BS.values(), yearly)
        self.is_rows = self.prepareRows(IS.values(), yearly)
        self.cf_rows = self.prepareRows(CF.values(), yearly)
        self.npv_rows = self.prepareRows(NPV.values(), yearly)
        self.ss_rows = self.prepareRows(ELPROD.values(), yearly)

    def getProcessReportValuesDb(self, simulation_no, fields, yearly, iteration_no, report_header):
        """takes values based on simulation no and process them: rouning, adding yearly prefix"""

        double_round = REPORT_ROUNDING*2
        single_round = REPORT_ROUNDING
        def round_value(v):
            """Smart rounging - if number is small - use double round, otherwise - single """
            if isinstance(v, float):
                if  v > 5 or v < -5:
                    return   round(v, single_round)
                else:
                    return   round(v, double_round)
            else:
                return v

        db_values = self.db.getIterationValuesFromDb(simulation_no, fields, yearly, iteration_no=iteration_no)  #load data from db
        result = []
        for field in fields:  #loop for all fields
            if not field:  continue
            field = addYearlyPrefix(field, yearly)  #add yearly prefix if needed
            d = OrderedDict( (date,round_value(value)) for date,value in zip(report_header,db_values[field]) )  #make result dict
            result.append(d)
        return result

    def writeReportValues(self, yearly):
        """
        1 writing values for each file
        2 combining files into one
        3 converting it to excel
        4 adding second sheet to excel
        """
        self.writeReport(self.bs_rows, self.bs_header, self.bs_filename)
        self.writeReport(self.is_rows, self.is_header, self.is_filename)
        self.writeReport(self.cf_rows, self.cf_header, self.cf_filename)
        self.writeReport(self.npv_rows, self.npv_header, self.npv_filename)
        self.writeReport(self.ss_rows, self.ss_header, self.ss_filename)

        combine_list = [self.bs_filename, self.is_filename, self.ss_filename, self.cf_filename, self.npv_filename]
        combineFiles(combine_list, self.output_filename)

        xls_output_filename = self.getReportFilename(self.report_name, 'xlsx', yearly=yearly)
        self.output_filename = convert2excel(source=self.output_filename, output=xls_output_filename)
        addSecondSheetXls(self.output_filename, self.source_filename )

    def getReportFields(self, rows_str, yearly):
        """loads values from local report. now not used"""
        postfix = "" if not yearly else "_y"
        rows = [getattr(self.r, attr+postfix) for attr in rows_str if attr]
        return rows

    def roundDictValues(self, rows):
        """Rounding dict values if they are floats
        input and output: list of dicts
        """
        double_round = REPORT_ROUNDING*2
        single_round = REPORT_ROUNDING
        for row in rows:
            for k, v in row.items():
                if isinstance(v, float):
                    if  v > 5 or v < -5:
                        row[k] = round(v, single_round)
                    else:
                        row[k] = round(v, double_round)

    def prepareRows(self, rows_str, yearly):
        """Prepares rows for outputing to report
        + Rounding
        + Can output monthly (without change) and yearly (+_y) values ---> postfix
        """
        rows = self.getReportFields(rows_str, yearly)
        self.roundDictValues(rows)
        return rows

    def writeReport(self, rows, header, output_filename ):
        """write single report to file
        """
        with open(output_filename,'ab') as f:
            w = csv.DictWriter(f, rows[0].keys(), delimiter=';')
            w.writeheader()
            w.writerows(rows)

        transponseCsv(output_filename)
        addHeaderCsv(output_filename, header)
        transponseCsv(output_filename)

    def getReportFilename(self, name, extension='csv', yearly=False):
        """Generates report filename, it should be uniq"""

        cur_date = datetime.datetime.now().strftime("%Y%m%d")
        if yearly:
            report_name = "%s_%s_yearly.%s" % (cur_date, name, extension)
        else :
            report_name = "%s_%s_monthly.%s" % (cur_date, name, extension)
        report_name = os.path.join(report_directory, report_name)

        output_filename = uniquifyFilename(report_name)
        return output_filename

    def prepareSourceSecondSheetExcel(self, simulation_no, iteration_no):
        """Prepares second sheet date for excel
        saves data to csv file
        """
        source = self.db.getIterationValuesFromDb(simulation_no, SOURCE.values(), False, iteration_no=iteration_no)

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
    from tm import TechnologyModule
    from em import EnergyModule
    from sm import SubsidyModule
    from ecm import EconomicModule
    from report import Report
    from config_readers import MainConfig
    mainconfig = MainConfig()
    energy_module = EnergyModule(mainconfig)
    technology_module = TechnologyModule(mainconfig, energy_module)
    subside_module = SubsidyModule(mainconfig)
    economic_module = EconomicModule(mainconfig, technology_module, subside_module)

    o = ReportOutput(None)
    o.source_filename = r"C:\temp2.csv"
    o.prepareSourceSecondSheetExcel(20, 1)