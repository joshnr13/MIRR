#!/usr/bin/env python
# -*- coding utf-8 -*-

import datetime as dt
from math import floor

def months_between(date1,date2):
    """return full month number since date2 till date1"""
    if date1>date2:
        date1,date2=date2,date1
    m1=date1.year*12+date1.month
    m2=date2.year*12+date2.month
    months=m2-m1
    if date1.day>date2.day:
        months-=1
    elif date1.day==date2.day:
        seconds1=date1.hour*3600+date1.minute+date1.second
        seconds2=date2.hour*3600+date2.minute+date2.second
        if seconds1>seconds2:
            months-=1
    return months

def years_between(date1,date2):
    """return full year number since date2 till date1"""
    return floor(months_between(date1, date2) / 12)


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
        self.mpayment = self.calcMonthlyPayment()

    def calcMonthlyPayment(self):
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
