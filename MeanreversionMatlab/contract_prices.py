from __future__ import division
import csv
import math
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict

def start_q_date(date):
    """Returns date of first day of quarter in which the @date is."""
    y = date.year
    start_dates = [datetime(y, 1, 1), datetime(y, 4, 1), datetime(y, 7, 1), datetime(y, 10, 1)]
    i = 3
    while date < start_dates[i]:
        i -= 1
    return start_dates[i]

def end_q_date(date):
    """Returns date past the last day of quarter in which the @date is."""
    y = date.year
    end_dates = [datetime(y, 4, 1), datetime(y, 7, 1), datetime(y, 10, 1), datetime(y+1, 1, 1)]
    i = 0
    while date >= end_dates[i]:
        i += 1
    return end_dates[i]

def get_q(date):
    """Returns csv representation of this dates quarter, eq. 2007Q3."""
    return '{0}Q{1}'.format(date.year, (date.month - 1) // 3 + 1)

def get_q_range(start_date, end_date):
    """Return sorted list of quarters in interval [start, end)."""
    assert start_date <= end_date
    q = get_q(start_date)
    yield q
    end_q = get_q(end_date - timedelta(days=1))
    while q != end_q:
        start_date += timedelta(days=90)
        new_q = get_q(start_date)
        if new_q != q:
            yield new_q
        q = new_q

def contract_price(start_date, prices_dict):
    """Returns price of contract starting with @start_date."""
    start_date += timedelta(days=90)
    end_date = start_date + timedelta(days=365)
    q_range = list(get_q_range(start_date, end_date))
    weights = [0.25] * len(q_range)
    if len(q_range) == 5: # some quarters are not fully covered

        start_part = (end_q_date(start_date) - start_date).days
        end_part = (end_date - start_q_date(end_date)).days
        sum_of_parts = start_part + end_part
        assert 85 < sum_of_parts < 95

        weights[0]  *= start_part / sum_of_parts
        weights[-1] *= end_part   / sum_of_parts

        if weights[0] == 0: weights.pop(0)
        if weights[-1] == 0: weights.pop()

    try:
        prices = [prices_dict[q] for q in q_range]
    except KeyError as e:
        ### podatki manjkajo za dneve 28, 29, 30, ker je +90 dni premalo, rabimo +92
        if start_date.day >= 25:
            m = start_date.month
            while start_date.month == m:
                start_date += timedelta(days=1)
            return contract_price(start_date, prices_dict)
        return float('nan')

    assert len(prices) == len(weights), "prices len: {0}, weights len: {1}".format(len(prices), len(weights))
    return np.average(prices, weights=weights)

with open('Kvartali_EEX_settlement.csv') as f:
    data = defaultdict(dict)
    r = csv.DictReader(f)
    for line in r:
        d = datetime.strptime(line['tradingdate'], "%d.%m.%Y")
        obd = '20' + line['Leto'][-2:] + line['Kvartal']
        data[d][obd] = float(line['value'])

succ, fail = 0, 0
with open('contract_prices.csv', 'w') as g:
    w = csv.writer(g)
    w.writerow(["date", "price"])
    for start_date in sorted(data):
        price = contract_price(start_date, data[start_date])
        if not math.isnan(price):
            w.writerow([start_date.strftime("%d.%m.%Y"), "{0:.4f}".format(price)])
            succ += 1
        else:
            fail += 1
            print "Warning: not enough data on", start_date
print "succ:", succ, "fail:", fail
