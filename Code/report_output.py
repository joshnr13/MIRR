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
        self.r = report_data  #data of report
        self.db = Database()  #connection to DB

    def prepareReportISBSCFIRR(self, from_db=False, yearly=False, ):
        self.prepareReportFilenames(yearly, from_db)
        self.prepareReportHeaders()
        self.prepareReportValues(yearly, from_db)
        self.writeReportValues(yearly)
        print "%s Report outputed to file %s" % (self.report_name, self.output_filename)

    def prepareReportFilenames(self, yearly, from_db):
        """Generate standart filenames for all parts of report
        this files will be deleted after combining to final report
        """
        self.report_name = 'IS-BS-CF'
        if from_db:
            self.report_name += "_s%s_i%s" %  from_db
        self.output_filename = self.getReportFilename(self.report_name, yearly=yearly)  #generating output filename for XLS report

        self.bs_filename = self.output_filename + "_BS"  #report parts filenames
        self.is_filename = self.output_filename + "_IS"
        self.cf_filename = self.output_filename + "_CF"
        self.npv_filename = self.output_filename +  "_NPV"
        self.ss_filename = self.output_filename +  "_SS"
        self.source_filename = self.output_filename + "_SOURCE"

    def prepareReportHeaders(self):
        """prepare header (titles) for xls report"""
        self.bs_header = BS.keys()  #header for Balance Sheet (ie first row in report)
        self.is_header = IS.keys()
        self.cf_header = CF.keys()
        self.npv_header = NPV.keys()
        self.ss_header = ELPROD.keys()

    def prepareReportValues(self, yearly, from_db):
        """main method to prepare values for report"""
        self.prepareSourceSecondSheetExcel(*from_db)  #prepare second sheet XLS
        if from_db:
            self.getReportValuesDb(yearly, from_db)  #prepare first sheet XLS
        else:
            self.getReportValuesLocal(yearly) #prepare first sheet XLS

    def getReportValuesDb(self, yearly, from_db):
        """prepares rows values from database based on dict @from_db
        with simulation and iteration keys limitations"""

        simulation_no, iteration_no = from_db
        report_header = self.db.getReportHeader(simulation_no, iteration_no, yearly)  #loading header from DB

        self.bs_rows = self.getProcessReportValuesDb(simulation_no, BS.values(),  yearly, iteration_no, report_header)  #loading rows values from DB
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
        """takes values based on simulation from DB and process them: rouning, adding yearly prefix
        return  list of dicts, each dict with data for each iteration
        """

        double_round = REPORT_ROUNDING*2
        single_round = REPORT_ROUNDING
        def round_value(v):
            """Smart rounging - if number is small - use double round, otherwise - single """
            if isinstance(v, float):
                if  v > 5 or v < -5:  #if value is LARGE 5 abs than use single ROUND
                    return   round(v, single_round)
                else: #if value is LESS  5 abs than use double ROUND
                    return   round(v, double_round)
            else:
                return v

        db_values = self.db.getIterationValuesFromDb(simulation_no, fields, yearly, iteration_no=iteration_no)  #load data from db

        result = []
        for field in fields:  #loop for all fields
            if not field:  continue
            field = addYearlyPrefix(field, yearly)  #add yearly prefix if needed
            d = OrderedDict( (date,round_value(value)) for date,value in zip(report_header,db_values[field]) )  #make result dict for each iterations
            result.append(d)
        return result  #list of dicts, each dict with data for each iteration

    def writeReportValues(self, yearly):
        """
        1 writing values for each file
        2 combining files into one
        3 converting it to excel
        4 adding second sheet to excel
        """
        self.writeReport(self.bs_rows, self.bs_header, self.bs_filename)  #writing report parts to csv file
        self.writeReport(self.is_rows, self.is_header, self.is_filename)
        self.writeReport(self.cf_rows, self.cf_header, self.cf_filename)
        self.writeReport(self.npv_rows, self.npv_header, self.npv_filename)
        self.writeReport(self.ss_rows, self.ss_header, self.ss_filename)

        combine_list = [self.bs_filename, self.is_filename, self.ss_filename, self.cf_filename, self.npv_filename]
        combineFiles(combine_list, self.output_filename)  #combine all files into one CSV file

        xls_output_filename = self.getReportFilename(self.report_name, 'xlsx', yearly=yearly)  #generating XLS report filename
        self.output_filename = convert2excel(source=self.output_filename, output=xls_output_filename)  #coverting large CSV into XLS
        addSecondSheetXls(self.output_filename, self.source_filename )  #adding second sheet to XLS

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
            w = csv.DictWriter(f, rows[0].keys(), delimiter=';')  #writing report
            w.writeheader()
            w.writerows(rows)

        transponseCsv(output_filename)  #transposing report before adding header, becuase header is longer than values
        addHeaderCsv(output_filename, header)  #adding header
        transponseCsv(output_filename)  #transposing it back

    def getReportFilename(self, name, extension='csv', yearly=False):
        """Generates report filename, it should be uniq"""

        cur_date = datetime.datetime.now().strftime("%Y%m%d")
        if yearly:
            report_name = "%s_%s_yearly.%s" % (cur_date, name, extension)
        else :
            report_name = "%s_%s_monthly.%s" % (cur_date, name, extension)
        report_name = os.path.join(report_directory, report_name)

        output_filename = uniquifyFilename(report_name)  #return unique name based on given name
        return output_filename

    def prepareSourceSecondSheetExcel(self, simulation_no, iteration_no):
        """Prepares second sheet date for excel
        saves data to csv file
        """
        source = self.db.getIterationValuesFromDb(simulation_no, SOURCE.values(), False, iteration_no=iteration_no)  #loading values from DB

        with open(self.source_filename,'wb') as f:  #open file to write
            w = csv.writer(f, delimiter=';')
            for title,source_key  in SOURCE.items():
                dic_values = source[source_key]
                header = dic_values.keys()
                values = dic_values.values()
                w.writerow([title])
                for name, value in dic_values.items():
                    if isinstance(value, (dict, list)):
                        continue  #because SECOND sheet is for only config values, so we dont want to save to XLS large structures like lists and dicts
                    else:
                        w.writerow([name, value])  #else write to XLS
                w.writerow('')  #write last row blank

if __name__ == '__main__':
    from tm import TechnologyModule
    from em import EnergyModule
    from sm import SubsidyModule
    from ecm import EconomicModule
    from report import Report
    from config_readers import MainConfig
    mainconfig = MainConfig('ITALY')
    energy_module = EnergyModule(mainconfig)
    technology_module = TechnologyModule(mainconfig, energy_module)
    subsidy_module = SubsidyModule(mainconfig)
    economic_module = EconomicModule(mainconfig, technology_module, subsidy_module)

    o = ReportOutput(None)
    o.source_filename = r"C:\temp2.csv"
    o.prepareSourceSecondSheetExcel(20, 1)
