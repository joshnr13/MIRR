#!/usr/bin/env python
# -*- coding utf-8 -*-

import datetime as dt
from math import floor
from calendar import monthrange
from dateutil.relativedelta import relativedelta

class cached_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls=None):
        instance.__dict__[self.func.__name__] = self.func(instance)
        result = self.func(instance)
        return result

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


def last_day_month(date):
    """return date - last day date in month with input date"""
    day = monthrange(date.year, date.month)[1]
    return dt.date( date.year, date.month, day)


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
    return  date + relativedelta(years=years) - relativedelta(days=1)

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


if __name__ == '__main__':
    a = Annuitet(1000, 0.16, 12)
    a.calculate()
    print a.percents
