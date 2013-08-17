import os
import csv
import datetime
from database import Database
from numpy import corrcoef, around, isnan, std, mean, median
from scipy.stats import skew, kurtosis
from collections import OrderedDict
from config_readers import RiskModuleConfigReader
from math import sqrt
import scipy.stats as stat
from constants import report_directory, CORRELLATION_FIELDS
from annex import get_only_digits,  convert_value, convert2excel, uniquify_filename, get_only_digits_list
from charts import show_irr_charts, plot_histograms


def calcStatistics(values):

    """input @list of values
    output @dict with keys - stat name, value=stat_value
    """
    result = OrderedDict()
    if len(values) > 1:
        values_upd = values[:]
        values_upd[0] += 0.00001

        result['std'] = std(values_upd)
        result['skew'] = skew(values_upd)
        result['kurtosis'] = kurtosis(values_upd)
        result['mean'] = mean(values_upd)
        result['min'] = min(values_upd)
        result['max'] = max(values_upd)
        result['median'] = median(values_upd)
        result['variance'] = result['std'] ** 0.5
    else:
        result['std'] = std(values)
        result['skew'] = float('nan')
        result['kurtosis'] = float('nan')
        result['mean'] = mean(values)
        result['min'] = min(values)
        result['max'] = max(values)
        result['median'] = median(values)
        result['variance'] = result['std'] ** 0.5
    return  result

def calculateRequiredRateOfReturn(irr_values):
    """return  riskFreeRate(const) + benchmarkSharpeRatio(const) x standard deviation of IRR @irr_values"""
    config_values = RiskModuleConfigReader().getConfigsValues()
    riskFreeRate = config_values['riskFreeRate']
    benchmarkSharpeRatio = config_values['benchmarkSharpeRatio']
    irr_stdev = std(irr_values)

    return  riskFreeRate + benchmarkSharpeRatio * irr_stdev


def jbCritValue(p):
    """Calculate critical value fo x2 distribution for checking JB
    df=2%
    """
    df = 2
    return stat.chi2.ppf(p, df)

def calcJbStats(values):
    """

    we will use it to test the distribution of IRR from a smulation
    return  JB stat value
    """

    n = len(values)
    stats = calcStatistics(values)
    K = stats['kurtosis']
    S = stats['skew']
    JB = n/6.0 * (S*S + (K-3)*(K-3)/4.0)

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

    percent_levels = [l / 100.0 for l in levels]
    result = OrderedDict()
    for level in percent_levels:
        str_level = str(round(level, 3)).replace('.', ',')
        if jb_stat_value >= jbCritValue(level):
            result[str_level] = True
        else:
            result[str_level] = False
    return  result

def JarqueBeraTest(values):
    """calculates JarqueBeraTest and return probability list"""
    jb_stat_value = calcJbStats(values)
    return  calcJbProbability(jb_stat_value)



def print_irr_stats(irr_values_lst):
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

def save_irr_values_xls(irr_values_lst, simulation_no, yearly):
    """Saves IRR values to excel file
    @irr_values_lst - list  with 2 complicated dicts inside """

    cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
    report_name = "{cur_date}_irr_values_s{simulation_no}.csv".format(**locals())
    report_full_name = os.path.join(report_directory, report_name)
    output_filename = uniquify_filename(report_full_name)

    blank_row = [""]
    field1 = irr_values_lst[0]['field']
    field2 = irr_values_lst[1]['field']

    irr_values1 = [field1] + irr_values_lst[0][field1]
    irr_values2 = [field2] + irr_values_lst[1][field2]

    iterations = ["Iteration number"] + list(range(1, len(irr_values1)))
    simulation_info = ["Simulation number"] + [simulation_no]

    stat_params = ['min', 'max', 'median', 'mean', 'variance', 'std','skew', 'kurtosis', 'required_rate_of_return']
    stat_fields = ['field'] + stat_params
    stat_info1 = [field1]
    stat_info2 = [field2]

    jb_fileds = ['JB_TEST'] + irr_values_lst[0]['JBTest'].keys()
    jb_values1 = [field1] + irr_values_lst[0]['JBTest'].values()
    jb_values2 = [field2] + irr_values_lst[1]['JBTest'].values()

    for key in stat_params:
        stat_info1.append(irr_values_lst[0].get(key, ''))
        stat_info2.append(irr_values_lst[1].get(key, ''))

    with open(output_filename,'ab') as f:

        w = csv.writer(f, delimiter=';')
        w.writerow(simulation_info)
        w.writerow(blank_row)

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
    xls_output_filename = uniquify_filename(xls_output_filename)

    convert2excel(source=output_filename, output=xls_output_filename)
    print "CSV Report outputed to file %s" % (xls_output_filename)


def plotsave_stochastic_values_by_simulation(simulation_no, yearly=True):
    """"""
    fields = CORRELLATION_FIELDS.values()
    results = Database().get_iteration_values_from_db(simulation_no, fields=[], yearly=yearly , not_changing_fields=fields)
    plot_histograms(results, simulation_no, yearly)
    save_stochastic_values_by_simulation(results, simulation_no)

def save_stochastic_values_by_simulation(dic_values, simulation_no):
    """Saves IRR values to excel file
    @irr_values_lst - list  with 2 complicated dicts inside """

    cur_date = datetime.datetime.now().strftime("%Y-%m-%d")
    report_name = "{cur_date}_stochastic_s{simulation_no}.csv".format(**locals())
    report_full_name = os.path.join(report_directory, report_name)
    output_filename = uniquify_filename(report_full_name)
    rows_values = []
    rows_stats = []

    for name, values in dic_values.items():
        row = [name] + values
        rows_values.append(row)
        stats_dic = calcStatistics(values)
        stats = [name] + stats_dic.values()
        rows_stats.append(stats)


    blank_row = [""]

    iterations = ["Iteration number"] + list(range(1, len(values)+1))
    simulation_info = ["Simulation number"] + [simulation_no]
    stat_info = ["Statistics"] + stats_dic.keys()

    with open(output_filename,'ab') as f:

        w = csv.writer(f, delimiter=';')
        w.writerow(simulation_info)
        w.writerow(blank_row)

        w.writerow(iterations)
        w.writerows(rows_values)

        w.writerow(blank_row)
        w.writerow(stat_info)
        w.writerows(rows_stats)

    xls_output_filename = os.path.splitext(output_filename)[0] + ".xlsx"
    xls_output_filename = uniquify_filename(xls_output_filename)

    convert2excel(source=output_filename, output=xls_output_filename)
    print "Stochastic Report outputed to file %s" % (xls_output_filename)

def caclIrrsStatisctics(field_names, irr_values):
    """
    inputs: @field_names - list of irr field names for @irr_values
    output: list of dicts with irr statistics for each irr_type
    """
    results = []
    for field_name, irr in zip(field_names, irr_values):
        digit_irr = get_only_digits_list(irr)

        result = {}
        result[field_name] = irr
        result['field'] = field_name
        result['digit_values'] = digit_irr
        result['JBTest'] = JarqueBeraTest(digit_irr)
        result['required_rate_of_return'] = calculateRequiredRateOfReturn(digit_irr)
        result.update(calcStatistics(digit_irr))

        results.append(result)

    return  results


def analyseSimulationResults(simulation_no, yearly=False):
    """
    1 Gets from DB yearly values of irr
    2 Saves in xls report & Charts

    """
    field = 'irr_stats'
    db = Database()
    irr_values_lst = db.get_simulation_values_from_db(simulation_no, [field])[field][0]

    save_irr_values_xls(irr_values_lst, simulation_no, yearly)
    show_irr_charts(irr_values_lst, simulation_no, yearly)
    print_irr_stats(irr_values_lst)

if __name__ == '__main__':
    X = [0.1, 0.2, 0.3]
    import numpy
    X_norm = numpy.random.normal(5, size=100)
    print JarqueBeraTest(X_norm)