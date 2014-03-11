import os
import csv
import datetime
from database import Database
from numpy import std, mean, median
from scipy.stats import skew, kurtosis
from collections import OrderedDict
from config_readers import RiskModuleConfigReader
import scipy.stats as stat
from constants import report_directory, CORRELLATION_FIELDS
from annex import convert2excel, uniquifyFilename, getOnlyDigitsList
from charts import plotIRRChart, plotHistogramsChart, plotElectricityChart, plotWeatherChart

def calcStatistics(values):
    """input @list of values
    output @dict with keys - stat name, value=stat_value
    """
    result = OrderedDict()
    if len(values) > 1:
        values_upd = values[:]
        values_upd[0] += 0.00001  #adding very small value for first element in list for proper calculation of stats in case all values are the same

        result['std'] = std(values_upd)  #standart deviation
        result['skew'] = skew(values_upd)  #Skew
        result['kurtosis'] = kurtosis(values_upd)
        result['mean'] = mean(values_upd)
        result['min'] = min(values_upd)
        result['max'] = max(values_upd)
        result['median'] = median(values_upd)
        result['variance'] = result['std'] ** 0.5
    else:  #in case we have only one value, so we cant normally calculate stats, espessialy skew and kutorsis
        result['std'] = std(values)
        result['skew'] = float('nan')
        result['kurtosis'] = float('nan')
        result['mean'] = mean(values)
        result['min'] = min(values)
        result['max'] = max(values)
        result['median'] = median(values)
        result['variance'] = result['std'] ** 0.5
    return  result

def calculateRequiredRateOfReturn(irr_values, riskFreeRate, benchmarkSharpeRatio ):
    """return  riskFreeRate(const) + benchmarkSharpeRatio(const) x standard deviation of IRR @irr_values"""
    irr_stdev = std(irr_values)  #calculating st.deviation of IRR values
    return riskFreeRate + benchmarkSharpeRatio * irr_stdev  #formula


def jbCritValue(p):
    """Calculate critical value fo x2 distribution for checking JB
    df=2%
    """
    df = 2  #two percent, CONSTANT
    return stat.chi2.ppf(p, df)

def calcJbStats(values):
    """
    we will use it to test the distribution of IRR from a smulation
    return  JB stat value
    """
    n = len(values)
    stats = calcStatistics(values)  #calculation of Statistics for values
    K = stats['kurtosis']  #but we need only 2 of stats: skew and kutorsis
    S = stats['skew']
    JB = n/6.0 * (S*S + (K-3)*(K-3)/4.0)  #formula from book
    return JB

def calcJbProbability(jb_stat_value, levels=(95, 99, 99.9)):
    """
    inputs:
       jb_stat_value, - calculated JB value
       levels= list of levels for probability calculation [0-100.0]

    return:
       dict  with
       key=percent level, for ex  0.95, 0.99, 0.999
       value=  True or False with of probability that the distribution is normal
    """
     #calculation probability distribution is normal for all levels levels=(95, 99, 99.9)

    percent_levels = [l / 100.0 for l in levels]  #floats [0.0-0.99] representation of percents
    result = OrderedDict()  #init result container
    for level in percent_levels:
        str_level = str(round(level, 3)).replace('.', ',')  #string representation of percent level, we replace dot to comma because of excel
        if jb_stat_value >= jbCritValue(level):  #if stat value > cricitacal, means distribution is normal
            result[str_level] = True
        else:
            result[str_level] = False
    return  result

def JarqueBeraTest(values):
    """calculates JarqueBeraTest """
    jb_stat_value = calcJbStats(values)
    return jb_stat_value

def printIRRStats(irr_values_lst):
    """Prints statistics of irr values"""
    for dic in irr_values_lst:
        print "Statistics for %s" % dic.get('field', None)
        print "\tSt.deviation value %s" % dic.get('std', None)
        print "\tVariance value %s" % dic.get('variance', None)
        print "\tMin value %s" % dic.get('min', None)
        print "\tMax value %s" % dic.get('max', None)
        print "\tMedium value %s" % dic.get('median', None)
        print "\tMean value %s" % dic.get('mean', None)
        print "\tSkew value %s" % dic.get('skew', None)
        print "\tKurtosis value %s" % dic.get('kurtosis', None)
        print "\tRequired rate of return value %s" % dic.get('required_rate_of_return', None)
        print "\tJB test values %s" % dic.get('JBTest', None)
        print "\tJB value %s" % dic.get('JBTest_value', None)

def saveIRRValuesXls(irr_values_lst, simulation_no, yearly):
    """Saves IRR values to excel file
    @irr_values_lst - list  with 2 complicated dicts inside """
    cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
    report_name = "{cur_date}_irr_values_s{simulation_no}.csv".format(**locals())
    report_full_name = os.path.join(report_directory, report_name)
    output_filename = uniquifyFilename(report_full_name)  #real filename of report

    blank_row = [""]
    field1 = irr_values_lst[0]['field']  #field1 and field2 is IRR project or owners
    field2 = irr_values_lst[1]['field']

    irr_values1 = [field1] + irr_values_lst[0][field1]  #prepare row with first value field name, others - values
    irr_values2 = [field2] + irr_values_lst[1][field2]  #prepare row with first value field name, others - values

    iterations = ["Iteration number"] + list(range(1, len(irr_values1)))  #prepare row with first value Iterations number, others - iterations 1,2,3...
    simulation_info = ["Simulation number"] + [simulation_no]  #prepare row with field name and value

    stat_params = ['min', 'max', 'median', 'mean', 'variance', 'std','skew', 'kurtosis', 'required_rate_of_return']
    stat_fields = ['field'] + stat_params
    stat_info1 = [field1]
    stat_info2 = [field2]

    jb_fileds = ['JB_TEST' ] + irr_values_lst[0]['JBTest'].keys() + ["JB_VALUE"]  #prepare row with first column JB_TEST and second - values
    jb_values1 = [field1] + irr_values_lst[0]['JBTest'].values() +  [irr_values_lst[0]['JBTest_value']]
    jb_values2 = [field2] + irr_values_lst[1]['JBTest'].values() +  [irr_values_lst[1]['JBTest_value']]

    for key in stat_params:
        stat_info1.append(irr_values_lst[0].get(key, ''))
        stat_info2.append(irr_values_lst[1].get(key, ''))

    with open(output_filename,'ab') as f:  #starting write to FILE

        w = csv.writer(f, delimiter=';')
        w.writerow(simulation_info)  #writing simulation info to csv
        w.writerow(blank_row)  #write blank row

        w.writerow(iterations)
        w.writerow(irr_values1)
        w.writerow(irr_values2)

        w.writerow(blank_row)
        w.writerow(stat_fields)
        w.writerow(stat_info1)
        w.writerow(stat_info2)

        w.writerow(blank_row)
        w.writerow(jb_fileds)
        w.writerow(jb_values1)
        w.writerow(jb_values2)


    xls_output_filename = os.path.splitext(output_filename)[0] + ".xlsx"
    xls_output_filename = uniquifyFilename(xls_output_filename)  #preparing XLS filename before converting from CSV
    convert2excel(source=output_filename, output=xls_output_filename)  #coverting from CSV to XLS , using prepared report name
    print "CSV Report outputed to file %s" % (xls_output_filename)  #printing to screen path to generated report

def plotSaveStochasticValuesSimulation(simulation_no, yearly=True):
    """plots simulation stochastic values and saves them in xls"""
    fields = CORRELLATION_FIELDS.values()  #taking correlation fields needed for analys
    results = Database().getIterationValuesFromDb(simulation_no, fields=[], yearly=yearly , not_changing_fields=fields)  #loading data from db for correlation fields
    plotHistogramsChart(results, simulation_no, yearly)  #plotting histogram based on DB data
    saveStochasticValuesSimulation(results, simulation_no)  #saving results to XLS file

def plotGeneratedWeather(what, simulation_no, country):
    """plots graph of generated Weather Insolation and temperature from user defined simulation_no """
    results = Database().getWeatherData(simulation_no, country)  #loading data from db
    plotWeatherChart(results, what, simulation_no, country)  #plotting chart based on DB data

def plotGeneratedElectricity(what, simulation_no, country):
    """plots graph of generated Electricity Prices from user defined simulation_no """
    results = Database().getElectricityPrices(simulation_no, country)  #loading data from db
    plotElectricityChart(results, what=what, simulation_no=simulation_no, country=country)  #plotting chart based on DB data

def saveStochasticValuesSimulation(dic_values, simulation_no):
    """Saves IRR values to excel file
    @dic_values - dict[name]=list of values """
    cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
    report_name = "{cur_date}_stochastic_s{simulation_no}.csv".format(**locals())
    report_full_name = os.path.join(report_directory, report_name)
    output_filename = uniquifyFilename(report_full_name)

    rows_values = [];  rows_stats = []
    for name, values in dic_values.items():  #preparing rows with stats for saving to CSV
        row = [name] + values  #first value = name, other values
        rows_values.append(row)
        stats_dic = calcStatistics(values)  #preparing stats row
        stats = [name] + stats_dic.values() #first value = name, other stats values
        rows_stats.append(stats)

    blank_row = [""]
    iterations = ["Iteration number"] + list(range(1, len(values)+1))
    simulation_info = ["Simulation number"] + [simulation_no]
    stat_info = ["Statistics"] + stats_dic.keys()

    with open(output_filename,'ab') as f:  #writing all rows to CSV

        w = csv.writer(f, delimiter=';')
        w.writerow(simulation_info)
        w.writerow(blank_row)

        w.writerow(iterations)
        w.writerows(rows_values)

        w.writerow(blank_row)
        w.writerow(stat_info)
        w.writerows(rows_stats)

    xls_output_filename = os.path.splitext(output_filename)[0] + ".xlsx"
    xls_output_filename = uniquifyFilename(xls_output_filename)  #generating filename for XLS
    convert2excel(source=output_filename, output=xls_output_filename)  #converting CSV to XLS

    print "Stochastic Report outputed to file %s" % (xls_output_filename)  #printing path to generated report

def caclIrrsStatisctics(field_names, irr_values, riskFreeRate, benchmarkSharpeRatio):
    """
    inputs: @field_names - list of irr field names for @irr_values
    output: list of dicts with irr statistics for each irr_type
    """
    results = []
    for field_name, irr in zip(field_names, irr_values):
        digit_irr = getOnlyDigitsList(irr)  #filtering only digits values of IRR for proper calculation of statistics

        result = {}  #init dict for saving stats
        result['field'] = field_name  #what irr values was used (name of filed)
        result[field_name] = irr  #not filtered irr values
        result['digit_values'] = digit_irr  #filtered irr values (only digit values)
        result['JBTest_value'] = JarqueBeraTest(digit_irr)  #JB test result
        result['JBTest'] = calcJbProbability(result['JBTest_value'])  #JB test result
        result['required_rate_of_return'] = calculateRequiredRateOfReturn(digit_irr, riskFreeRate, benchmarkSharpeRatio)  #rrr
        result.update(calcStatistics(digit_irr))  #adding all statistics (stdevm min, max etc)

        results.append(result)

    return  results  #return list of dicts

def analyseSimulationResults(simulation_no, yearly=False):
    """
    1 Gets from DB yearly values of irr
    2 Saves in xls report & Charts

    """
    db = Database()
    field = 'irr_stats'  #which field will be loaded from DB
    irr_values_lst = db.getSimulationValuesFromDB(simulation_no, [field])[field][0]  #loading defined field values from DB

    saveIRRValuesXls(irr_values_lst, simulation_no, yearly)  #saving IRR values to XLS
    plotIRRChart(irr_values_lst, simulation_no, yearly)  #plotting IRR charts
    printIRRStats(irr_values_lst)  #outputing to screen IRR stats

if __name__ == '__main__':
    X = [0.1, 0.2, 0.3]
    import numpy
    X_norm = numpy.random.normal(5, size=100)
    print JarqueBeraTest(X_norm)
