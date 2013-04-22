import random
import pylab
import datetime
import numpy
import ConfigParser
import csv
import os

def getConfig(filename='em_config.ini'):
    """Reads module config file and makes variables global"""
    config = ConfigParser.ConfigParser()
    filepath = os.path.join(os.getcwd(), 'configs', filename)
    config.read(filepath)
    global mean, stdev
    mean = config.getfloat('NormalDistribution', 'mean')
    stdev = config.getfloat('NormalDistribution', 'stdev')

def getRandomFactor():
    """return random factor with normal distribution"""
    result = random.gauss(mean, stdev)
    return result

def getAvMonthInsolation(month):
    """Returns average daily insolation in given month"""
    filepath = os.path.join(os.getcwd(), 'inputs', 'em_input.txt')
    result = numpy.genfromtxt(filepath, dtype=None, delimiter=';',  names=True)
    return result[month-1]['Hopt']

def generatePrimaryEnergyAvaialbility(date):
    """Parameters: start date
    based on monthly averages creates daily data
    """
    """for each day of month:   .insulation = average monthly insolation for respective month * (random factor according to normal distribution)"""
    date_month = date.month
    av_insolation = getAvMonthInsolation(date_month)
    return av_insolation * getRandomFactor()

def generatePrimaryEnergyAvaialbility_range(start_date, end_date):
    """Parameters: start date
    based on monthly averages creates daily data
    """
    result = 0
    while True:
        if start_date > end_date:
            return result
        else:
            result += generatePrimaryEnergyAvaialbility(start_date)
            start_date += datetime.timedelta(days=1)

def getResolutionStartEnd(start_date, end_date, resolution):
    """Returns list [start and end dates] using resolution"""
    result = []
    while True:
        next_step_date = start_date + datetime.timedelta(days=resolution)
        if start_date >= end_date:
            break
        if next_step_date <= end_date:
            result.append((start_date, next_step_date))
            start_date = next_step_date
        elif next_step_date > end_date:
            result.append((start_date, end_date))
        start_date = next_step_date
    return result


def get_xy_values_for_plot(start_date, end_date, resolution):
    """return x,y values for plotting step chart"""

    result = getResolutionStartEnd(start_date, end_date, resolution)
    result.insert(0, (start_date, start_date))
    y = []

    for start_period, end_period in result:
        y.append(generatePrimaryEnergyAvaialbility_range(start_period, end_period))

    x = []
    sm = 0
    for r in result:
        delta = (r[1] - r[0]).days
        x.append(sm+delta)
        sm += delta

    return x,y


def outputPrimaryEnergy(start_date, end_date, resolution):
    """Parameters: start_date; end_date; resolution
       Makes a graph (x-axis displays time; y-axis= displays primary energy).
       The minimum interval on the x-axis is set by resolution (integer number of days).
       Values on the y-axis are sum of the energy in the time interval.
    """

    datetime_delta = end_date - start_date
    assert end_date > start_date
    assert datetime_delta.days > resolution, "Difference between start and end date should be grater then resolution"
    x, y = get_xy_values_for_plot(start_date, end_date, resolution)
    pylab.step(x, y)
    pylab.show()

getConfig()

if __name__ == '__main__':
    start_date = datetime.date(2005, 1, 1)
    end_date = datetime.date(2006, 12, 30)

    #result = getResolutionStartEnd(start_date, end_date, 5)
    #print getAvMonthInsolation(3)
    #generatePrimaryEnergyAvaialbility(end_date)

    outputPrimaryEnergy(start_date, end_date, 10)

