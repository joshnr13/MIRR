import os
import csv
import datetime
from database import Database
from numpy import std, mean, median, absolute, diff, var
from scipy.stats import skew, kurtosis
from collections import OrderedDict
from config_readers import RiskModuleConfigReader
import scipy.stats as stat
from constants import report_directory, CORRELLATION_FIELDS
from annex import convert2excel, uniquifyFilename, getOnlyDigitsList, transponseCsv, addHeaderCsv
from charts import plotIRRChart, plotHistogramsChart, plotElectricityChart, plotWeatherChart, \
    plotElectricityHistogram


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
        result['variance'] = var(values_upd)
    else:  #in case we have only one value, so we cant normally calculate stats, espessialy skew and kutorsis
        result['std'] = std(values)
        result['skew'] = float('nan')
        result['kurtosis'] = float('nan')
        result['mean'] = mean(values)
        result['min'] = min(values)
        result['max'] = max(values)
        result['median'] = median(values)
        result['variance'] = var(values)
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
        if jb_stat_value >= jbCritValue(level):  #if stat value < cricitcal, means distribution is normal
            result[str_level] = False
        else:
            result[str_level] = True
    return  result

def JarqueBeraTest(values):
    """calculates JarqueBeraTest"""
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
        print "\tMedian value %s" % dic.get('median', None)
        print "\tMean value %s" % dic.get('mean', None)
        print "\tSkewness value %s" % dic.get('skew', None)
        print "\tKurtosis value %s" % dic.get('kurtosis', None)
        print "\tRequired rate of return value %s" % dic.get('required_rate_of_return', None)
        print "\tJB test values %s" % dic.get('JBTest', None)
        print "\tJB value %s" % dic.get('JBTest_value', None)

def saveIRRValuesXls(irr_values_lst, simulation_no, yearly, country):
    """Saves IRR values to excel file
    @irr_values_lst - list  with 2 complicated dicts inside"""

    report_name = "{country}_irr_values_s{simulation_no}.csv".format(**locals())
    report_full_name = os.path.join(report_directory, report_name)
    output_filename = uniquifyFilename(report_full_name)  #real filename of report

    blank_row = [""]
    field1 = irr_values_lst[0]['field']  #field1 and field2 is IRR project or owners
    field2 = irr_values_lst[1]['field']
    field3 = irr_values_lst[2]['field']

    irr_values1 = [field1] + irr_values_lst[0][field1]  #prepare row with first value field name, others - values
    irr_values2 = [field2] + irr_values_lst[1][field2]  #prepare row with first value field name, others - values
    irr_values3 = [field3] + irr_values_lst[2][field3]

    iterations = ["Iteration number"] + list(range(1, len(irr_values1)))  #prepare row with first value Iterations number, others - iterations 1,2,3...
    simulation_info = ["Simulation number"] + [simulation_no]  #prepare row with field name and value

    stat_params = ['min', 'max', 'median', 'mean', 'variance', 'std','skew', 'kurtosis', 'required_rate_of_return']
    stat_fields = ['field'] + stat_params
    stat_info1 = [field1]
    stat_info2 = [field2]
    stat_info3 = [field3]

    jb_fileds = ['JB_TEST' ] + irr_values_lst[0]['JBTest'].keys() + ["JB_VALUE"]  #prepare row with first column JB_TEST and second - values
    jb_values1 = [field1] + irr_values_lst[0]['JBTest'].values() +  [irr_values_lst[0]['JBTest_value']]
    jb_values2 = [field2] + irr_values_lst[1]['JBTest'].values() +  [irr_values_lst[1]['JBTest_value']]
    jb_values3 = [field3] + irr_values_lst[2]['JBTest'].values() +  [irr_values_lst[2]['JBTest_value']]

    for key in stat_params:
        stat_info1.append(irr_values_lst[0].get(key, ''))
        stat_info2.append(irr_values_lst[1].get(key, ''))
        stat_info3.append(irr_values_lst[2].get(key, ''))

    with open(output_filename, 'ab') as f:  #starting write to FILE

        w = csv.writer(f, delimiter=';')
        w.writerow(simulation_info)  #writing simulation info to csv
        w.writerow(blank_row)  #write blank row

        w.writerow(iterations)
        w.writerow(irr_values1)
        w.writerow(irr_values2)
        w.writerow(irr_values3)

        w.writerow(blank_row)
        w.writerow(stat_fields)
        w.writerow(stat_info1)
        w.writerow(stat_info2)
        w.writerow(stat_info3)

        w.writerow(blank_row)
        w.writerow(jb_fileds)
        w.writerow(jb_values1)
        w.writerow(jb_values2)
        w.writerow(jb_values3)


    xls_output_filename = os.path.splitext(output_filename)[0] + ".xlsx"
    xls_output_filename = uniquifyFilename(xls_output_filename)  #preparing XLS filename before converting from CSV
    convert2excel(source=output_filename, output=xls_output_filename)  #coverting from CSV to XLS, using prepared report name
    print "CSV Report outputed to file %s" % (xls_output_filename)  #printing to screen path to generated report

def plotSaveStochasticValuesSimulation(simulation_no, yearly=True):
    """plots simulation stochastic values and saves them in xls"""
    fields = CORRELLATION_FIELDS.values()  #taking correlation fields needed for analys
    db = Database()
    results = db.getIterationValuesFromDb(simulation_no, fields=[], yearly=yearly, not_changing_fields=fields)  #loading data from db for correlation fields
    country = db.getSimulationCountry(simulation_no=simulation_no, print_result=True)
    plotHistogramsChart(results, simulation_no, yearly, country=country)  #plotting histogram based on DB data
    saveStochasticValuesSimulation(results, simulation_no, country=country)  #saving results to XLS file

def plotGeneratedWeather(weather_data, what, simulation_no, country):
    """plots graph of generated Weather Insolation and temperature from user defined simulation_no"""
    plotWeatherChart(weather_data, what, simulation_no, country)  #plotting chart based on DB data


def getWeatherDataFromDb(simulation_no, country):
    return Database().getWeatherData(simulation_no, country)  # loading data from db


def getElectricityDataFromDb(simulation_no, country):
    return Database().getElectricityPrices(simulation_no, country)  # loading data from db


def saveWeatherData(weather_data, what, simulation_no, country):
    cur_date = get_cur_date()
    report_name = "{cur_date}_{country}_weather_s{simulation_no}.csv".format(**locals())
    report_full_name = os.path.join(report_directory, report_name)
    output_filename = uniquifyFilename(report_full_name)

    rows_values = []
    rows_stats = []

    for date, values in weather_data.items():  # preparing rows with stats for saving to CSV
        row = [date] + values  #first value = date, other values
        rows_values.append(row)

    blank_row = [""]
    simulation_info = ["Simulation number"] + [simulation_no]
    header = ['Date', 'Insolation', 'Temperature']

    with open(output_filename, 'ab') as f:  # writing all rows to CSV
        w = csv.writer(f, delimiter=';')
        w.writerow(simulation_info)
        w.writerow(blank_row)
        w.writerow(header)
        w.writerows(rows_values)

    xls_output_filename = os.path.splitext(output_filename)[0] + ".xlsx"
    xls_output_filename = uniquifyFilename(xls_output_filename)  # generating filename for XLS
    convert2excel(source=output_filename, output=xls_output_filename)  # converting CSV to XLS

    print "Weather data Report outputed to file %s" % xls_output_filename  #printing path to generated report


def exportElectricityPrices(country, simulation_no=None):
    prices = getElectricityDataFromDb(simulation_no, country)  # loading data from db
    print 1
    stats = Database().getElecticityStats(country)
    print 2
    report_name = "{country}_electricity_prices.csv".format(**locals())
    report_full_name = os.path.join(report_directory, report_name)
    output_filename = uniquifyFilename(report_full_name)

    price_rows = [s.items() for s in prices]
    rows_stats = [simulation['stats'] for simulation in stats]

    info1 = "Electricity prices stats for %s \n" % country
    info2 = "Electricity prices for %s \n" % country

    simulations_names = ['Sim-%s' % (i+1) for i in range(len(rows_stats))]

    print 3
    with open(output_filename, 'wb') as f:
        w = csv.DictWriter(f, rows_stats[0].keys(), delimiter=';')  # writing report
        w.writeheader()
        w.writerows(rows_stats)

    transponseCsv(output_filename)
    addHeaderCsv(output_filename, ["Stat"] + simulations_names)  # adding header
    content = open(output_filename).readlines()

    with open(output_filename, 'wb') as f:
        w = csv.DictWriter(f, prices[0].keys(), delimiter=';')  # writing report
        w.writeheader()
        w.writerows(prices)
    transponseCsv(output_filename)
    addHeaderCsv(output_filename, ["Date/Price"] + simulations_names)  # adding header
    content2 = open(output_filename).readlines()

    with open(output_filename, 'wb') as output:
        output.write(info1)
        output.writelines(content)
        output.write('\n')
        output.write(info2)
        output.writelines(content2)

    # xls_output_filename = os.path.splitext(output_filename)[0] + ".xlsx"
    # xls_output_filename = uniquifyFilename(xls_output_filename)  # generating filename for XLS
    # convert2excel(source=output_filename, output=xls_output_filename)  # converting CSV to XLS

    print "Weather data Report outputed to file %s" % output_filename


def plotGeneratedElectricity(what, simulation_no, country):
    """plots graph of generated Electricity Prices from user defined simulation_no"""
    results = getElectricityDataFromDb(simulation_no, country)  #loading data from db
    plotElectricityChart(results, what=what, simulation_no=simulation_no, country=country)  #plotting chart based on DB data
    if isinstance(simulation_no, int):  # plotting diagrams only for single simulation
        prices = results.values()
        price_diff = diff(prices)
        abs_price_diff = absolute(price_diff)
        data = {'prices': prices, 'price_diff': price_diff, 'abs_price_diff': abs_price_diff}
        plotElectricityHistogram(data, what=what, simulation_no=simulation_no, country=country)


def get_cur_date():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def saveStochasticValuesSimulation(dic_values, simulation_no, country):
    """Saves IRR values to excel file
    @dic_values - dict[name]=list of values"""
    cur_date = get_cur_date()
    report_name = "{cur_date}_{country}_stochastic_s{simulation_no}.csv".format(**locals())
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
    country = db.getSimulationCountry(simulation_no)
    saveIRRValuesXls(irr_values_lst, simulation_no, yearly, country)  #saving IRR values to XLS
    plotIRRChart(irr_values_lst, simulation_no, yearly, country)  #plotting IRR charts
    printIRRStats(irr_values_lst)  #outputing to screen IRR stats

if __name__ == '__main__':
    X = [0.1, 0.2, 0.3]
    import numpy
    X_norm = numpy.random.normal(5, size=100)
    print JarqueBeraTest(X_norm)
