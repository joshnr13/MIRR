#!/usr/bin/env python
# -*- coding utf-8 -*-

import os
import itertools
import tempfile
import csv
import operator
import datetime as dt
import errno
import types
import numpy as np

from functools import partial
from math import floor
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from numbers import Number
from decimal import Decimal
from scipy.optimize import newton

try:
    from openpyxl import Workbook
    from openpyxl.cell import get_column_letter
except ImportError:
    print "No Excel support for reports"


class cached_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls=None):
        instance.__dict__[self.func.__name__] = self.func(instance)
        result = self.func(instance)
        return result

class OrderedDefaultdict(OrderedDict):
    def __init__(self, *args, **kwargs):
        newdefault = None
        newargs = ()
        if args:
            newdefault = args[0]
            if not (newdefault is None or callable(newdefault)):
                raise TypeError('first argument must be callable or None')
            newargs = args[1:]
        self.default_factory = newdefault
        super(self.__class__, self).__init__(*newargs, **kwargs)

    def __missing__ (self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):  # optional, for pickle support
        args = self.default_factory if self.default_factory else tuple()
        return type(self), args, None, None, self.items()

class memoize(object):
    """cache the return value of a method

    This class is meant to be used as a decorator of methods. The return value
    from a given method invocation will be cached on the instance whose method
    was invoked. All arguments passed to a method decorated with memoize must
    be hashable.

    If a memoized method is invoked directly on its class the result will not
    be cached. Instead the method will be invoked like a static method:
    class Obj(object):
        #@memoize
        def add_to(self, arg):
            return self + arg
    Obj.add_to(1) # not enough arguments
    Obj.add_to(1, 2) # returns 3, result is not cached
    """
    def __init__(self, func):
        self.func = func
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self.func
        return partial(self, obj)
    def __call__(self, *args, **kw):
        obj = args[0]
        try:
            cache = obj.__cache
        except AttributeError:
            cache = obj.__cache = {}
        key = (self.func, args[1:], frozenset(kw.items()))
        try:
            res = cache[key]
        except KeyError:
            res = cache[key] = self.func(*args, **kw)
        return res


def get_multiplier(_from, _to, step):
    digits = []
    for number in [_from, _to, step]:
        pre = Decimal(str(number)) % 1
        digit = len(str(pre)) - 2
        digits.append(digit)
    max_digits = max(digits)
    return float(10 ** (max_digits))


def float_range(_from, _to, step, include=False):
    """Generates a list of floating point values over the Range [start, stop]
       with step size step
    Works fine with floating point representation!
    """
    mult = get_multiplier(_from, _to, step)
    # print mult
    int_from = int(round(_from * mult))
    int_to = int(round(_to * mult))
    int_step = int(round(step * mult))
    # print int_from,int_to,int_step
    if include:
        result = range(int_from, int_to + int_step, int_step)
        result = [r for r in result if r <= int_to]
    else:
        result = range(int_from, int_to, int_step)
    # print result
    float_result = [r / mult for r in result]
    return float_result

def get_configs(dic):
    """Gets dict ,return   dict with keys not starts with _"""
    result = {}
    for k, v in dic.items():
        if k.startswith('_') or k == 'self':
            continue
        result[k] = v
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
        return (-months_between(date2, date1))
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

def is_last_day_year(date):
    """return True is date is last day of year"""
    new_date = date + dt.timedelta(days=1)
    if new_date.year != date.year:
        return True
    else:
        return False

def get_months_range(year):
    result = []
    for i in range(1, 13):
        start_date_m = dt.date(year, i, 1)
        end_date_m = last_day_month(start_date_m)
        result.append((start_date_m, end_date_m))
    return result

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

def last_day_year(date):
    """return date - last day date in month with input date"""
    return dt.date( date.year, 12, 31)

def month_number_days(date):
    last_day = last_day_month(date)
    return last_day.day

def last_year(date):
    """Return the same date but previous year"""
    last_year = date.year - 1
    last_month = date.month
    temp_date = dt.date(last_year, last_month, 1)
    return  last_day_month(temp_date)


def last_day_previous_month(date):
    """return date - last day of previous month"""
    prev_month_date =  date - relativedelta(months=1)
    last_day_prev_month = last_day_month(prev_month_date)
    return last_day_prev_month

def last_day_next_month(date):
    """return date - last day of next month"""
    next_month_date =  date + relativedelta(months=1)
    last_day_next_month = last_day_month(next_month_date)
    return last_day_next_month

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

def add_x_months(date, months):
    """return date X months later - 1 day"""
    return  date + relativedelta(months=int(months)) - relativedelta(days=1)


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
        os.close(fd)
    return filename

def get_report_dates(start_date_project, end_date_project):
    """return  dates for reports
    dic_monthly[first_day_month]=last_day_month
    dic_yearly[last_day_month]=list_of_ (start_date,end_date)
    """
    report_dates = OrderedDict()
    report_dates_y = OrderedDefaultdict(list)

    date = first_day_month(start_date_project)
    date_to = end_date_project

    while True:
        end_date = last_day_month(date)
        end_date_y = last_day_year(date)
        start_date = first_day_month(date)

        report_dates[start_date] = end_date
        report_dates_y[end_date_y].append((start_date, end_date))

        date = next_month(date)
        if  date > date_to:
            break

    return (report_dates, report_dates_y)

def add_start_project_values(csv_filename, header, values=None):
    if values is not None:
        pass
    else :
        blank_header = ["" for h in header]
        add_header_csv(csv_filename, blank_header)


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


#def setColumnWidths(sheet, widths):
    #idx = 1
    #for w in widths:
        #colLetter = openpyxl.cell.get_column_letter(idx)
        #sheet.column_dimensions[colLetter].width = w
        #idx += 1

def csv2xlsx(inputfilename, outputfilename, listname='report'):
    """Converts csv 2 excel"""

    with open(inputfilename) as fin:
        reader = csv.reader(fin, delimiter=';')
        wb = Workbook()

        open(outputfilename, 'wb').close()

        ws = wb.worksheets[0]
        ws.title = listname
        columns = []
        for row_index, row in enumerate(reader):
            for column_index, cell in enumerate(row):
                column_letter = get_column_letter((column_index + 1))
                if column_letter not in columns:
                    columns.append(column_letter)
                _ceil = ws.cell('%s%s'%(column_letter, (row_index + 1)))
                _ceil.value = cell

                #_ceil.style.font.bold = True

        first_column = columns[0]
        ws.column_dimensions[first_column].width = 40

        for column in columns[1:]:
            ws.column_dimensions[column].width = 12

        wb.save(filename = outputfilename)

def combine_files(from_filenames, to_filename):
    """Combining several files to one
    from_filenames=[of filenames], to_filename="filename"
    """
    content = "\n"
    for f in from_filenames:
        content += open(f).read() + '\n\n\n'
        os.remove(f)

    with open(to_filename,'wb') as output:
        output.write(content)


def convert2excel(source, output):
    """Converts souce file to excel file with name = @output"""
    csv2xlsx(source, output)
    os.remove(source)
    return  output

def get_input_date(default=None, text=''):
    date = raw_input("Input date %s or press ENTER to use default value %s::  " %(text, default))
    try:
        result= dt.datetime.strptime(date,"%Y-%m-%d").date()
    except ValueError:
        print "No value or value error. Return default value %s" % default
        result = default

    return result

def get_input_int(default=None, text=''):
    value = raw_input(text)
    try:
        result= int(value)
    except ValueError:
        print "No value or value error. Return default value %s" % default
        result = default

    return result

def get_only_digits(obj):
    return  filter(lambda x :isinstance(x, Number), obj.values())

class Annuitet():
    def __init__(self,summa,yrate,yperiods, start_date):
        """
        summa - how much we borrow
        yrate - fix rate in percents per year
        yperiods - number of years to return debt
        """
        self.summa = summa
        self.yrate = yrate
        self.mperiods = yperiods * 12
        self.mpayment = self.__calcMonthlyPayment()
        self.start_date = start_date
        self.total_debt = self.mpayment * self.mperiods


    def __calcMonthlyPayment(self):
        P = self.yrate / 12
        N = self.mperiods
        S = self.summa

        return  S * P * (1+P) ** N / ((1+P) ** N-1)


    def calculate(self):
        """Calculated annuitet values

        @percent_payments = dict with sum we need to pay at current period - for percent of loan
        @debt_payments = dict with sum we need to pay at current period - for body of loan
        @rest_payments = dict with sum, we still need to pay in next periods

        """
        date = self.start_date

        percent_payment = 0# (self.summa * self.yrate / 12)
        debt_payment = 0
        rest_payment = self.total_debt
        rest_payment_wo_percent = self.summa

        percent_payments = OrderedDict({date: percent_payment,})
        debt_payments = OrderedDict({date: debt_payment,})
        rest_payments = OrderedDict({date: rest_payment,})
        rest_payments_wo_percents = OrderedDict({date: rest_payment_wo_percent,})

        for i in range(0, self.mperiods):
            date = last_day_next_month(date)

            percent_payment = rest_payment_wo_percent * self.yrate / 12
            debt_payment = self.mpayment - percent_payment
            rest_payment -= self.mpayment
            rest_payment_wo_percent -= debt_payment

            if rest_payment < 0.01:
                rest_payment = 0

            if rest_payment_wo_percent < 0.01:
                rest_payment_wo_percent = 0

            percent_payments[date] = percent_payment
            debt_payments[date] = debt_payment
            rest_payments[date] = rest_payment
            rest_payments_wo_percents[date] = rest_payment_wo_percent

        self.percent_payments = percent_payments
        self.debt_payments = debt_payments
        self.rest_payments = rest_payments
        self.rest_payments_wo_percents = rest_payments_wo_percents


def convert_dict(input_dict):
    """part of deep_serilization od DICTS"""
    result = OrderedDict()
    for (key, value) in input_dict.items():
        if key == 'report_dates_y':
            print

        key = convert_base_values(key)
        value = convert_base_values(value)
        value = convert_value(value)
        result[key] = value
    return result

def convert_base_values(base_value):
    """part of deep_serilization of BASE VALUES"""
    if isinstance(base_value, (dt.datetime, dt.date)):
        key = str(base_value)
    else:
        key = base_value
    return key

def convert_value(value):
    """part of deep_serilization MAIN"""
    if isinstance(value, types.DictionaryType):
        return  convert_dict(value)
    elif isinstance(value, (types.ListType, types.TupleType)):
        return convert_list(value)
    elif isinstance(value, (dt.datetime, dt.date)):
        return str(value)
    else:
        return value

def convert_list(input_lst):
    """part of deep_serilization of LISTS and TUPLES"""
    result = []
    for v in input_lst:
        converted = convert_value(v)
        result.append(converted)
    return result


def _discf(rate, pmts, ):
    dcf=[]
    cur_period=0
    for i,cf in enumerate(pmts):
        dcf.append(cf*(1+rate)**(-i))
    return np.add.reduce(dcf)

def irr(pmts, guess=0.1):
    """
    IRR function that accepts irregularly spaced cash flows
    @values: array_like
          Contains the cash flows including the initial investment
    @Returns: Float
          Internal Rate of Return
    """

    f = lambda x: _discf(x, pmts)
    try:
        return newton(f, guess, maxiter=100, tol=0.001)
    except RuntimeError:
        return float('Nan')


if __name__=="__main__":
    pmts=[-1000,	-500,	-100,	1000]
    print xirr(pmts)

if __name__ == '__main__':
    date = dt.date(2000, 1, 1)
    date2 = dt.date(2001, 12, 31)
    print get_report_dates(date, date2)[1]
    import types
    o = OrderedDict()
    print isinstance(o, types.DictionaryType)

    #a = Annuitet(summa=1000, yrate=0.16, yperiods=1, start_date=date)
    #a = Annuitet(summa=250000, yrate=0.06, yperiods=12, start_date=date)
    #a.calculate()
    #for i in range(13):
        #print "%s: %-13s %-13s %-13s  %-13s  = %-13s" % (date,
                                          #a.rest_payments[date],
                                          #a.rest_payments_wo_percents[date],
                                   #a.debt_payments[date],
                                   #a.percent_payments[date],
                                   #a.debt_payments[date] + a.percent_payments[date]
                                   #)
        #date = last_day_next_month(date)
