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
import sys

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

class NullDevice():
    def write(self, s):
        pass

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

#def irr(pmts, guess=0.01):
    #"""
    #IRR function that accepts irregularly spaced cash flows
    #@values: array_like
          #Contains the cash flows including the initial investment
    #@Returns: Float
          #Internal Rate of Return
    #"""
    ##pmts = np.around(pmts, decimals=4)
    ##pmts = np.float64(pmts)
    #f = lambda x: _discf(x, pmts)
    #try:
        #sys.stderr = NullDevice()
        #value = newton(f, guess, maxiter=100, tol=10**(-10))
        #sys.stderr = sys.__stderr__
        #if value > 1:
            #print "Too large IRR %s . Setting to zero" % value
            #value = 0
        #if value < 0.0001:
            #print "Too low IRR %s . Setting to zero" % value
            #value = 0
        #return value
    #except RuntimeError:
        #return float('Nan')

def invert_dict(d):
    newdict = {}
    for k, v in d.iteritems():
        newdict[v] = k
    return newdict

if __name__=="__main__":
    pmts=[-1000,	500,	100,	1000, -200, 100, 10, -222]
    fcf_project_values = [-52500.0, 9.094947017729282e-13, -3000.000000000002, -1999.9999999999986, 10312.917080295065, -4554.1354255383039, -5105.5779770375266, 7002.2624291253878, 5634.9137524801899, 6215.0637694091101, 5451.4289039946689, 2496.5823558127327, 3978.1215116621293, 3540.2299623837584, 3206.7971105880242, 3016.1425272861957, 4780.0596139307872, 5336.239675863193, 7117.5060421685785, 6900.6579751536447, 5691.1671272720478, 8703.9073283371126, 5285.9878539342035, -416.6339909854961, 6653.8555931863211, 5669.0730892146212, 4914.0290583622036, 5548.3829570661155, 7969.833817518077, 7691.1232862130501, 10274.188320124791, 11946.028667951214, 8519.0887947056854, 9529.3109333959637, 9071.4027094270241, -735.08515308104836, 6710.0208204081546, 5750.6354532294908, 4871.0665364767683, 5917.3624066550865, 7312.345421327992, 8451.4701351231633, 11015.196071144206, 11334.545811574646, 9174.6162399457207, 9748.8235396951204, 9375.9967489622068, -307.50607637522796, 6705.7745237545805, 5663.062778287971, 5547.1303219264328, 4714.3538518292653, 7393.1541563399796, 9233.9995980640015, 10638.039945775592, 10096.774458680329, 9765.6144568849359, 9939.2905421443793, 8959.2510035102878, -503.41361386985159, 6730.4035665583369, 5347.360198277388, 5362.9887293777319, 5490.1159633674579, 7207.1527733107469, 8697.1514895566888, 11460.744856578127, 10128.123442041939, 8562.6784699011259, 10983.378495895653, 9859.1028149740177, -781.86115991419399, 6622.042841081312, 5232.4035403778298, 5248.4570476110603, 6052.3091183943043, 6934.1220330320084, 9012.4142354032301, 11841.675380078836, 9486.0370643950828, 10252.473621029467, 10310.64517414683, 9434.3955935036247, 46.123073375468152, 6806.8082467515542, 5769.0595844708041, 5174.7667732016271, 6716.5759906468575, 7434.9062466735195, 8643.1268179751005, 13632.927694774904, 10778.867890635292, 8409.8470366867605, 12021.822806167367, 10601.465386621025, -962.14694396295442, 6962.3082957340612, 5295.4571627679979, 5976.2390296886324, 6244.8155147842144, 7666.8695054020282, 8295.3207165046988, 11742.055766048079, 13313.334722960093, 9015.6984657350386, 10314.2475292411, 10165.310980490749, -664.40049197974827, 7773.294586336503, 6008.6692472765089, 5600.2217423336233, 5492.5680989610355, 8697.8936226116857, 8569.2770641057232, 12017.957509182392, 12148.197320661924, 9112.0083209206859, 11181.596206223838, 10317.954937037633, -364.92484626579113, 7504.9517987759973, 5704.9963507485318, 5790.4446962159427, 6499.1038574446511, 8229.267682323878, 8036.0316875122326, 12283.209741605489, 13049.353101204457, 9048.5477859057701, 10775.260838053206, 10410.861587470185, -703.12404105089581, 7430.2997042469788, 5801.9408283786197, 5668.301590239259, 6683.3416712388316, 7989.6964873877387, 10281.587628510635, 11248.798025614402, 12095.30774515239, 10389.636384907648, 11658.157316488572, 11114.352821420869, -1118.7518386910247, 7263.4760424815522, 5678.8369965810371, 7087.8664264264462, 5411.0809770516889, 8609.0646933039552, 10459.442466664432, 13042.209104422544, 11240.852467487228, 10908.025276886472, 12699.735188558565, 10315.737752453093, -1174.1444948088933, 7506.4961734529152, 6185.6166090621655, 5192.6365718888774, 7071.8520606767252, 9023.5819129335487, 8280.4872561192024, 13729.626119623648, 11073.496823111362, 10697.57968316798, 10460.807867587966, 11465.634442825783, -714.48340436391584, 4686.921162846289, 4131.1039002659536, 4786.7749632913137, 4382.6823891166432, 5706.93630069746, 7431.2204186033914, 8509.8075906323302, 9110.5269952439721, 8139.361443169204, 8356.5720976058292, 7632.446026610216, -555.14693166405777, 5611.6749463672541, 4402.2292765757002, 4311.6860213645168, 4651.7191294300655, 6073.3878282425349, 6222.6813321364461, 10256.585821178143, 9180.3196616838868, 6712.7862142481672, 8951.0122879210539, 7945.1097895652128, -863.37691291227566, 5559.043961319604, 4640.2558328986033, 3925.1673153095708, 4400.8805809087216, 6427.1633906306943, 6279.1318435972735, 10219.876135870192, 8450.7614839756552, 7300.5816429141823, 9094.0630577289849, 8167.1729693360285, -706.47668455910116, 5530.9096311506264, 4429.8794235583255, 4461.6003525139031, 5180.3331092140088, 5731.1588299356899, 7355.1554856490475, 8932.2570346145967, 10547.076753181906, 7707.3944135819002, 8445.2136283408599, 8905.466038860257, -1123.6937954504911, 5708.4922088313488, 4858.9782361956322, 4628.2308463017944, 4967.958025068654, 6468.9141773962328, 7617.2468741553275, 10090.369807591378, 9719.4358014486425, 8246.9393376979842, 9489.720838223293, 8261.5879209848863, -1065.9991467367872, 6275.1010199424354, 4410.6724305425287, 5121.2548832872135, 4964.9849173432667, 5974.2281760169153, 7898.8334953196791, 10668.799142429123, 8956.3175131871394, 8794.0810666176167, 9280.5169997192261, 7943.242486161138, -793.70537807980236, 5704.8219367140337, 4910.2258162493745, 5140.5154933015619, 5109.001813561923, 6634.9976013057221, 7422.8494847777511, 10844.986359943065, 9784.9421698982696, 8500.2204746230418, 10257.702603048754, 7526.0237508893661, -1046.8078115980661, 6617.9684016175443, 5001.1188275615395, 5117.0229527069478, 5305.6455985498542, 6965.7356269573738, 7823.7712315417357, 10346.949318598427, 11128.869958660265, 9400.2822001810018, 8737.6186644093323, 9087.8949768541061, -508.85982122375208, 6078.9761817095368, 5127.3951217802523, 4741.5478660529698, 5458.1467111769543, 7969.4766495295771, 6374.5075125167023, 11239.692393848965, 11299.001627192769, 8461.1299277465478, 9652.866022894199, 8795.2223602662616, -1006.3893133863476, 6877.7655485983714, 5254.7633672579705, 4912.6929833628456, 4890.6393602096159, 7640.5366598476012, 8883.7146295852035, 10800.232901625091, 9930.7375283106085, 10133.989817086498, 10166.763140080729, 8883.0221999942405, -722.62381516753885, 6694.0034341773007, 5337.9301467509467, 5128.3419748295873, 5530.7490062188936, 7750.761308764324, 8434.9019245882373, 11747.22917231989, 10749.223044332512, 9477.1238541874245, 10872.153426920808, 9489.7554319245719, -919.67147347397167, 6995.6239901504996, 5766.0148261194881, 5254.8960215442485, 5321.9538629097588, 8011.0884056396899, 8186.4395813027641, 11262.613464218692, 11782.9308645906, 10150.715372268964, 10236.620797254944, 8929.1086940157147, -447.6888474397856, 7700.4797428236407, 5733.42060891445, 4487.978485906855, 6641.6643363952262, 8011.2957939433927, 7907.4645001282915, 12162.110345826683, 11203.783303928196, 10122.85228786607, 10059.847222695551, 10400.669900191055, -408.03959613845291, 6594.9943009343278, 5123.4874257404072, 5648.5223072312128, 5378.8995762653431, 8468.7265398993641, 7859.8950803189018, 12676.466433045503, 11108.682010216446, 8927.8342236975004, 11860.12163110762, 10047.776191492478, -1397.981258339747, 7331.3980754192944, 5290.6318374881248, 6146.0057459494901, 5913.2340178056511, 8399.7238174893719, 8345.0268933752341, 11510.66897625773, 13282.209440672035, 10042.929883737481, 11355.622122722163, 9771.1708978037368, -1464.556666966484, 7830.6010939082726, 5012.5153578713634, 5764.9824408538516, 7588.017818553928, 6273.3250461460866, 8907.4593727349275, 12630.011774394825, 12396.754794301227, 11115.033883777502, 10471.32094304479, 10100.458264748399, -514.3024749248234]

    print irr(fcf_project_values)

#if __name__ == '__main__':
    #date = dt.date(2000, 1, 1)
    #date2 = dt.date(2001, 12, 31)
    #print get_report_dates(date, date2)[1]
    #import types
    #o = OrderedDict()
    #print isinstance(o, types.DictionaryType)

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
