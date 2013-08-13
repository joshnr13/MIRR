from numpy import corrcoef, around, isnan, std, mean, median
from scipy.stats import skew, kurtosis
from collections import OrderedDict
from config_readers import RiskModuleConfigReader
from math import sqrt
import scipy.stats as stat

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

def  calculateRequiredRateOfReturn(irr_values):
    """return  riskFreeRate(const) + benchmarkSharpeRatio(const) x standard deviation of IRR @irr_values"""

    config_values = RiskModuleConfigReader().getConfigsValues()
    riskFreeRate = config_values['riskFreeRate']
    benchmarkSharpeRatio = config_values['benchmarkSharpeRatio']
    irr_stdev = calcStatistics(irr_values)['std']

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
    result = {}
    for level in percent_levels:
        str_level = str(round(level, 3))
        if jb_stat_value >= jbCritValue(level):
            result[str_level] = True
        else:
            result[str_level] = False
    return  result

def JarqueBeraTest(values):
    """calculates JarqueBeraTest and return probability list"""
    jb_stat_value = calcJbStats(values)
    return  calcJbProbability(jb_stat_value)


if __name__ == '__main__':
    X = [0.1, 0.2, 0.3]
    import numpy
    X_norm = numpy.random.normal(5, size=100)
    print JarqueBeraTest(X_norm)