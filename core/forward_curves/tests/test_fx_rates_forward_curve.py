from core.forward_curves.fx_rates_forward_curves import FxForwardCurve
from core.forward_curves.quotes import MissingPriceError, FxQuotes
from core.time_period.date_range import DateRange, LoadShapedDateRange
from core.quantity.quantity import USD, GBP

import unittest
import datetime as dt
import numpy as np


class FxForwardCurveTestCase(unittest.TestCase):

    def setUp(self):
        self.quotes = FxQuotes({dt.date(2014, 1, 1): 1.25,
                                dt.date(2014, 4, 1): 1.26,
                                dt.date(2014, 7, 1): 1.27,
                                dt.date(2014, 10, 1): 1.28}, unit = USD / GBP)
        self.curve = FxForwardCurve(self.quotes)

    def test_retrieve_quotes(self):
        """
        Test that we can retreive an input quote
        """
        self.assertEqual(self.curve.price(DateRange("2014-7-1")), 1.27 * USD / GBP)

    def test_price_non_quoted_period(self):
        """
        Test the lienar interpolation in the log space
        """
        expected = np.exp((np.log(1.27) * 61 + np.log(1.28) * 31) / 92)
        self.assertEqual(self.curve.price(DateRange("2014-8-1")), expected * USD / GBP)

    def test_out_of_bounds(self):
        with self.assertRaises(MissingPriceError):
            self.curve.price(DateRange("2013, 8, 1"))
        with self.assertRaises(MissingPriceError):
            self.curve.price(DateRange("2015, 8, 1"))

    def test_compute_fx_forward_on_lsdr(self):
        """
        Test that we can compute an everage FX rate over a non-trivial LoadShapedDateRange
        """
        lsdr = LoadShapedDateRange("2014-Q3", "offpeak")
        expected = sum(LoadShapedDateRange(DateRange(dt.date(2014, 7, 1) + dt.timedelta(i), range_type='d'),
                                           "offpeak").duration
                       * np.exp((np.log(1.27) * (92 - i) + np.log(1.28) * i) / 92)
                       for i in range(92))
        self.assertEqual(self.curve.price(lsdr), expected / lsdr.duration * USD / GBP)
        # sanity check: we expect the price to be close to 1.275
        self.assertTrue(1.2748 < self.curve.price(lsdr).value < 1.2752)