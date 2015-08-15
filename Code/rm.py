import os
import csv
import datetime
from database import Database
from numpy import std, mean, median, absolute, diff, var
from scipy.stats import skew, kurtosis, normaltest
from collections import OrderedDict
from config_readers import RiskModuleConfigReader
import scipy.stats as stat
from constants import report_directory, CORRELLATION_FIELDS
from annex import convert2excel, uniquifyFilename, getOnlyDigitsList, transponseCsv, addHeaderCsv, dot2comma
from charts import plotIRRChart, plotHistogramsChart, plotElectricityChart, plotWeatherChart, \
    plotElectricityHistogram, plotTotalEnergyProducedChart


def calcStatistics(values):
    """input @list of values
    output @dict with keys - stat name, value=stat_value
    """
    result = OrderedDict()
    if len(values) > 1:
        values_upd = list(values)
        values_upd[0] += 1e-5  #adding very small value for first element in list for proper calculation of stats in case all values are the same

        result['std'] = std(values_upd)  # standart deviation -- biased estimator
        result['skew'] = skew(values_upd)  # skewness -- biased estimator
        result['kurtosis'] = kurtosis(values_upd) # Fisher (-3) definition -- biased estimator
        result['mean'] = mean(values_upd) # mean -- ubiased estimator
        result['min'] = min(values_upd)
        result['max'] = max(values_upd)
        result['median'] = median(values_upd)
        result['variance'] = var(values_upd) # variance -- biased estimator
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


def jbCritValue(significance):
    """Return assimptotically aproximative critical value ofr JB statistics.
       JB ~ chi^2(2) (approximately, as n -> inf)"""
    return stat.chi2.ppf(1 - significance, 2)

def calcJBStat(values):
    """Return value of JB statistics to test the distribution of IRR from a
       simulation for normality.
       Null hypothesis: @values are distibuted normally.
       Alternative hypothesis: @values are not distributed normally.
       JB = n / 6 + (S^2 + K^2 / 4)
       P(JB < crit_val) < significance, if null hypothesis is true."""
    n = len(values)
    stats = calcStatistics(values)  # calculation of Statistics for values
    K = stats['kurtosis']  # but we need only 2 of stats: skew and kutorsis
    S = stats['skew']
    JB = n / 6.0 * (S*S + K*K / 4.0)  #formula from book
    return JB

def JarqueBeraTest(values=(), significance_levels=(0.05, 0.01, 0.001), JB_stat_value=None):
    """Performs Jarque-Bera test of @values at @significance_levels
    returns dict {significance level : value of the test (true or false)}"""
    if JB_stat_value is None:
        JB_stat_value = calcJBStat(values)

    result = OrderedDict()  # init result container
    for significance in significance_levels:
        str_level = "{0:.3f}".format(1 - significance).replace(".", ",") # format with comma for excel
        if JB_stat_value >= jbCritValue(significance):  # if stat value >= cricitcal we reject the hypothesis: there is very low probability of this happening if null hypothesis were true
            result[str_level] = False
        else:
            result[str_level] = True
    return result

def normalityTest(values_orig, significance_levels=(0.05, 0.01, 0.001)):
    values = list(values_orig)
    values[0] += 1e-5

    if len(values) < 3:
        stat_val, p_val = -1, 100
    else:
        stat_val, p_val = normaltest(values)

    result = OrderedDict()  # init result container
    for significance in significance_levels:
        str_level = "{0:.3f}".format(1 - significance).replace(".", ",") # format with comma for excel
        if p_val < significance:
            result[str_level] = False
        else:
            result[str_level] = True
    return result

def printSimulationStats(irr_values_lst):
    """Prints statistics of irr values"""
    for dic in irr_values_lst:
        print "Statistics for %s:"                   % dot2comma(dic.get('field'))
        print "\tSt.deviation value: %s"             % dot2comma(dic.get('std'))
        print "\tVariance value: %s"                 % dot2comma(dic.get('variance'))
        print "\tMin value: %s"                      % dot2comma(dic.get('min'))
        print "\tMax value: %s"                      % dot2comma(dic.get('max'))
        print "\tMedian value: %s"                   % dot2comma(dic.get('median'))
        print "\tMean value: %s"                     % dot2comma(dic.get('mean'))
        print "\tSkewness value: %s"                 % dot2comma(dic.get('skew'))
        print "\tKurtosis value: %s"                 % dot2comma(dic.get('kurtosis'))
        print "\tRequired rate of return value: %s"  % dot2comma(dic.get('required_rate_of_return'))
        print "\tJB test: %s"                        % sorted(dic.get('JBTest').items())
        print "\tJB value: %s"                       % dot2comma(dic.get('JBTest_value'))
        print "\tNormal test: %s"                    % sorted(dic.get('normaltest').items())

def saveSimulationValuesXls(irr_values_lst, tep_values_lst, simulation_no, yearly, country):
    """Saves IRR and TEP values to excel file
    @irr_values_lst - list  with 3 complicated dicts inside"""
    report_name = "{country}_irr_tep_values_s{simulation_no}.csv".format(**locals())
    report_full_name = os.path.join(report_directory, report_name)
    output_filename = uniquifyFilename(report_full_name)  # real filename of report

    num_irr_fields, num_tep_fields = len(irr_values_lst), len(tep_values_lst)

    irr_fields = [irr_values_lst[i]['field'] for i in range(num_irr_fields)]
    tep_fields = [tep_values_lst[i]['field'] for i in range(num_tep_fields)]

    irr_values = []  # rows with IRR values, the first column of each row is field name
    tep_values = []  # rows with TEP values, the first column of each row is field name
    for i in range(num_irr_fields):
        irr_values.append([irr_fields[i]] + irr_values_lst[i][irr_fields[i]])
    for i in range(num_tep_fields):
        tep_values.append([tep_fields[i]] + tep_values_lst[i][tep_fields[i]])

    stat_params = ['min', 'max', 'median', 'mean', 'variance', 'std', 'skew', 'kurtosis', 'required_rate_of_return']
    stat_fields = ['field'] + stat_params
    stat_info_irr = []  # rows with IRR statistics
    stat_info_tep = []  # rows with TEP statistics
    for i in range(num_irr_fields):
        stat_info_irr.append([irr_fields[i]] + [irr_values_lst[i].get(key, '') for key in stat_params])
    for i in range(num_tep_fields):
        stat_info_tep.append([tep_fields[i]] + [tep_values_lst[i].get(key, '') for key in stat_params])

    sorted_jb_keys = sorted(irr_values_lst[0]['JBTest'].keys())
    sorted_normal_keys = sorted(irr_values_lst[0]['normaltest'].keys())
    jb_fields = ['JB_TEST'] + sorted_jb_keys + ["JB_VALUE"]  # prepare row with first column JB_TEST and second - values
    normal_fields = ['Normal test'] + sorted_normal_keys
    jb_values = []  # rows with JB values for IRR
    normal_values = []  # rows with normal test values for IRR
    for i in range(num_irr_fields):
        jb_values.append([irr_fields[i]] + [irr_values_lst[i]['JBTest'][k] for k in sorted_jb_keys] + [irr_values_lst[i]['JBTest_value']])
        normal_values.append([irr_fields[i]] + [irr_values_lst[i]['normaltest'][k] for k in sorted_jb_keys])

    iterations = ["Iteration number"] + list(range(1, len(irr_values[0])))  # prepare row with first value Iterations number, others - iterations 1,2,3...
    simulation_info = ["Simulation number"] + [simulation_no]  # prepare row with field name and value

    blank_row = [""]
    with open(output_filename, 'ab') as f:  # starting write to FILE
        w = csv.writer(f, delimiter=';')

        w.writerow(simulation_info)  # writing simulation info to csv
        w.writerow(blank_row)  # write blank row

        w.writerow(iterations)
        for row in irr_values:
            w.writerow(row)
        for row in tep_values:
            w.writerow(row)

        w.writerow(blank_row)
        w.writerow(stat_fields)
        for row in stat_info_irr:
            w.writerow(row)
        for row in stat_info_tep:
            w.writerow(row)

        w.writerow(blank_row)
        w.writerow(jb_fields)
        for row in jb_values:
            w.writerow(row)

        w.writerow(blank_row)
        w.writerow(normal_fields)
        for row in normal_values:
            w.writerow(row)

    xls_output_filename = os.path.splitext(output_filename)[0] + ".xlsx"
    xls_output_filename = uniquifyFilename(xls_output_filename)  # preparing XLS filename before converting from CSV
    convert2excel(source=output_filename, output=xls_output_filename)  # coverting from CSV to XLS, using prepared report name
    print "CSV Report outputed to file %s" % xls_output_filename  # printing to screen path to generated report

def plotSaveStochasticValuesSimulation(simulation_no, yearly=True):
    """plots simulation stochastic values and saves them in xls"""
    fields = CORRELLATION_FIELDS.values()  #taking correlation fields needed for analys
    db = Database()
    results = db.getIterationValuesFromDb(simulation_no, fields=[], yearly=yearly, not_changing_fields=fields)  #loading data from db for correlation fields
    country = db.getSimulationCountry(simulation_no=simulation_no, print_result=True)
    plotHistogramsChart(results, simulation_no, yearly, country=country)  #plotting histogram based on DB data
    saveStochasticValuesSimulation(results, simulation_no, country=country)  #saving results to XLS file

def plotGeneratedWeather(weather_data, what, simulation_no, country, chosen_simulation):
    """plots graph of generated Weather Insolation and temperature from user defined simulation_no"""
    plotWeatherChart(weather_data, what, simulation_no, country, chosen_simulation)  #plotting chart based on DB data


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
    header = ['Date', 'Insolation', 'Temperature', 'Average production ker kW']

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
    if isinstance(simulation_no, int):
        all_stats = [i['stats'] for i in Database().getElecticityStats(country)]
        st = all_stats[simulation_no]
        print 'Statistics:'
        print "\tSt.deviation value: %s" % dot2comma(st.get('std'))
        print "\tVariance value: %s"     % dot2comma(st.get('variance'))
        print "\tMin value: %s"          % dot2comma(st.get('min'))
        print "\tMax value: %s"          % dot2comma(st.get('max'))
        print "\tMedian value: %s"       % dot2comma(st.get('median'))
        print "\tMean value: %s"         % dot2comma(st.get('mean'))
        print "\tSkewness value: %s"     % dot2comma(st.get('skew'))
        print "\tKurtosis value: %s"     % dot2comma(st.get('kurtosis'))

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

def calcSimulationStatistics(field_names, irr_values, riskFreeRate, benchmarkSharpeRatio):
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
        result['JBTest_value'] = calcJBStat(digit_irr)  # JB statistics value
        result['JBTest'] = JarqueBeraTest(JB_stat_value=result['JBTest_value'])  # JB test result for different significance levels
        result['normaltest'] = normalityTest(digit_irr)
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
    field1 = 'irr_stats'  #which field will be loaded from DB
    field2 = 'total_energy_produced_stats'
    country = db.getSimulationCountry(simulation_no)

    # IRR values
    irr_values_lst = db.getSimulationValuesFromDB(simulation_no, [field1])[field1][0]  #loading defined field value
    # from DB
    plotIRRChart(irr_values_lst, simulation_no, yearly, country)  #plotting IRR charts
    printSimulationStats(irr_values_lst)  #outputing to screen IRR stats

    # total energy produced values
    total_energy_values_lst = db.getSimulationValuesFromDB(simulation_no, [field2])[field2][0]
    plotTotalEnergyProducedChart(total_energy_values_lst, simulation_no, yearly, country)
    printSimulationStats(total_energy_values_lst)

    saveSimulationValuesXls(irr_values_lst, total_energy_values_lst, simulation_no, yearly, country)  # saving IRR
    # and TEP values to XLS

if __name__ == '__main__':
    import numpy
    print JarqueBeraTest(numpy.random.normal(5, size=1000)) # must be normal
    print JarqueBeraTest(numpy.random.normal(5, size=100)) # should be normal
    print JarqueBeraTest(numpy.random.normal(5, size=20)) # probably normal
    print JarqueBeraTest(range(20)) # could be normal
    print JarqueBeraTest(range(100)) # maybe not normal
    print JarqueBeraTest(range(1000)) # certanly not normal

    print normalityTest(numpy.random.normal(5, size=1000)) # must be normal
    print normalityTest(numpy.random.normal(5, size=100)) # should be normal
    print normalityTest(numpy.random.normal(5, size=20)) # probably normal
    print normalityTest(range(30)) # could be normal
    print normalityTest(range(100)) # maybe not normal
    print normalityTest(range(1000)) # certanly not normal
