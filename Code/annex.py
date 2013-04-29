#!/usr/bin/env python
# -*- coding utf-8 -*-

import os
import itertools
import tempfile
import csv
import operator
import datetime as dt
import errno

from math import floor
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from collections import OrderedDict

class cached_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls=None):
        instance.__dict__[self.func.__name__] = self.func(instance)
        result = self.func(instance)
        return result

def accumulate(data, f=operator.add):
    xs = data.values()
    keys = data.keys()
    new_values = reduce(lambda a, x: a + [f(a[-1], x)], xs[1:], [xs[0]])
    items = zip(keys, new_values)
    new_dict = dict(items)
    result = OrderedDict(sorted(new_dict.items(), key=lambda t: t[0]))
    return result

def getDaysNoInMonth(date):
    """return number of days in given month"""
    days = monthrange(date.year, date.month)[1]
    return days

def months_between(date1,date2):
    """return full month number since date2 till date1"""
    if date1>date2:
        date1,date2=date2,date1
    m1=date1.year*12+date1.month
    m2=date2.year*12+date2.month
    months=m2-m1
    if date1.day>date2.day:
        months-=1
    #elif date1.day==date2.day:

        #seconds1=date1.hour*3600+date1.minute+date1.second
        #seconds2=date2.hour*3600+date2.minute+date2.second
        #if seconds1>seconds2:
            #months-=1
    return months

def years_between(date1,date2):
    """return full year number since date2 till date1"""
    return floor(months_between(date1, date2) / 12)

def years_between_1Jan(date1,date2):
    """return year difference between 2 datas """
    return date2.year - date1.year

def last_day_month(date):
    """return date - last day date in month with input date"""
    day = getDaysNoInMonth(date)
    return dt.date( date.year, date.month, day)

def last_day_previous_month(date):
    """return date - last day of previous month"""
    prev_month_date =  date - relativedelta(months=1)
    last_day_prev_month = last_day_month(prev_month_date)
    return last_day_prev_month

def first_day_month(date):
    """return date - first day date in month with input date"""
    return dt.date( date.year, date.month, 1)

def next_month(date):
    cur_month = date.month
    cur_year = date.year
    if cur_month == 12:
        cur_month = 1
        cur_year += 1
    else:
        cur_month += 1

    return dt.date(cur_year,cur_month , date.day)

def add_x_years(date, years):
    """return date X years later - 1 day"""
    return  date + relativedelta(years=int(years)) - relativedelta(days=1)

class Annuitet():
    def __init__(self,summa,yrate,yperiods):
        """
        summa - how much we borrow
        yrate - fix rate in percents per year
        yperiods - number of years to return debt
        """
        self.summa = summa
        self.yrate = yrate
        self.mperiods = yperiods * 12
        self.mpayment = self.__calcMonthlyPayment()


    def __calcMonthlyPayment(self):
        P = self.yrate / 12
        N = self.mperiods
        S = self.summa

        return  S * P * (1+P) ** N / ((1+P) ** N-1)


    def calculate(self):
        percent = (self.summa * self.yrate / 12)
        debt = self.mpayment - percent
        ost = self.summa - debt

        percents = [percent]
        debts = [debt]
        ostatki = [ost]
        for i in range(1, self.mperiods):
            percent = ost * self.yrate / 12
            debt = self.mpayment - percent
            ost -= debt

            percents.append(percent)
            debts.append(debt)
            ostatki.append(ost)

        self.percents = percents
        self.depts = debts
        self.ostatki = ostatki


def uniquify_filename(path, sep = ''):
    """Return free filename, if file name is Busy adds suffix _number
    Input: filename we want
    Output: filename we can
    """
    def name_sequence():
        count = itertools.count()
        yield ''
        while True:
            yield '{s}_v{n:d}'.format(s = sep, n = next(count))

    orig = tempfile._name_sequence
    with tempfile._once_lock:
        tempfile._name_sequence = name_sequence()
        path = os.path.normpath(path)
        dirname, basename = os.path.split(path)
        filename, ext = os.path.splitext(basename)
        fd, filename = tempfile.mkstemp(dir = dirname, prefix = filename, suffix = ext)
        tempfile._name_sequence = orig
    return filename


def transponse_csv(csv_filename):
    """Transposing csv file"""
    new_filenmame = csv_filename
    with  open(csv_filename) as csv_file:
        a = itertools.izip(*csv.reader(csv_file, delimiter=';'))
        with open(new_filenmame, "wb") as f:
            csv.writer(f, delimiter=';').writerows(a)


def add_header_csv(csv_filename, header):
    """Adds first row header to csv file"""
    line = ";".join(header)
    with open(csv_filename,'r+') as f:
        content = f.read()
        f.seek(0,0)
        f.write(line.rstrip('\r\n') + '\n' + content)


def mkdir_p(path):
    """ Mkdir if not exists """
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else: raise



if __name__ == '__main__':
    a = Annuitet(1000, 0.16, 12)
    a.calculate()
    print a.percents
