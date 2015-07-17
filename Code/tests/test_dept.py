import unittest
from datetime import date
from annex import PMT


class TestCase(unittest.TestCase):

    def test_pmt(self):
        pmt = PMT(1000, yrate=0.12, yperiods=1, date=date(2014, 1, 1))
        pmt.calculate()
        print "dates;", ";".join(map(str, pmt.percent_payments.keys()))
        print "percent_payments;", ";".join(map(str, pmt.percent_payments.values()))
        print "debt_payments;", ";".join(map(str, pmt.debt_payments.values()))
        print "rest_payments;", ";".join(map(str, pmt.rest_payments.values()))
        print "rest_payments_wo_percents;", ";".join(
            map(str, pmt.rest_payments_wo_percents.values()))

        def rround(val):
            return round(val, 2)

        self.assertEqual(
            [0.0, -10.0, -9.21, -8.42, -7.61, -6.8, -5.98, -5.15, -4.31, -3.47, -2.61, -1.75, -0.88],
            map(rround, pmt.percent_payments.values())
        )
        self.assertEqual(
            [0.0, -78.85, -79.64, -80.43, -81.24, -82.05, -82.87, -83.7, -84.54, -85.38, -86.24, -87.1, -87.97],
            map(rround, pmt.debt_payments.values())
        )

        self.assertEqual(
            [1066.19, 977.34, 888.49, 799.64, 710.79, 621.94, 533.09, 444.24, 355.4, 266.55, 177.7, 88.85, 0.0],
            map(rround, pmt.rest_payments.values())
        )

        self.assertEqual(
            [1000.0, 921.15, 841.51, 761.08, 679.84, 597.79, 514.92, 431.22, 346.68, 261.3, 175.07, 87.97, 0.0],
            map(rround, pmt.rest_payments_wo_percents.values())
        )

