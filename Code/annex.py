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