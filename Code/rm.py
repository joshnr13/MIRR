from numpy import corrcoef, around, isnan, std, mean, median
from  scipy.stats import skew, kurtosis
from collections import OrderedDict
from config_readers import RiskModuleConfigReader

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

if __name__ == '__main__':
    print calculateRequiredRateOfReturn([0.1, 0.2, 0.3])