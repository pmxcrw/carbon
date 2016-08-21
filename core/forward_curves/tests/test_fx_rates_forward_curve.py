from core.forward_curves.fx_rates_forward_curves import FxForwardCurve, DiscountCurve, ForeignDiscountCurve, \
                                                        InverseFxForwardCurve
from core.forward_curves.quotes import MissingPriceError, FxQuotes, RatesQuotes
from core.time_period.date_range import DateRange, LoadShapedDateRange
from core.quantity.quantity import USD, GBP, EUR

import unittest
import datetime as dt
import numpy as np


class FxForwardCurveTestCase(unittest.TestCase):

    def setUp(self):
        self.quotes = FxQuotes({dt.date(2014, 1, 1): 1.25,
                                dt.date(2014, 4, 1): 1.26,
                                dt.date(2014, 7, 1): 1.27,
                                dt.date(2014, 10, 1): 1.28},
                               value_date = dt.date(2013, 12, 31),
                               unit = USD / GBP)
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

class RateCurveTestCase(unittest.TestCase):

    def setUp(self):
        quotes = RatesQuotes(USD,
                             {dt.date(2014, 1, 1): 0.01,
                              dt.date(2014, 4, 1): 0.03,
                              dt.date(2014, 7, 1): 0.04,
                              dt.date(2014, 10, 1): 0.06},
                             value_date=dt.date(2013, 12, 31))
        self.curve = DiscountCurve(quotes)

    def test_is_null(self):
        quotes = RatesQuotes(USD,
                             {dt.date(2014, 1, 1): 0,
                              dt.date(2014, 4, 1): 0,
                              dt.date(2014, 7, 1): 0,
                              dt.date(2014, 10, 1): 0},
                             value_date = dt.date(2013, 12, 31))
        null_curve = DiscountCurve(quotes)
        self.assertTrue(null_curve.is_null)
        self.assertFalse(self.curve.is_null)

    def test_today(self):
        self.assertEqual(self.curve.price(DateRange("2013-12-31")), 1)

    def test_typecheck(self):
        with self.assertRaises(TypeError):
            DiscountCurve(FxQuotes({dt.date(2014, 1, 1): 0.01 * USD / GBP}, value_date=dt.date(2013, 12, 31)))

    def test_discount_factor(self):
        days_offset = (dt.date(2014, 9, 1) - dt.date(2014, 7, 1)).days
        expected_rate = 0.04 + (0.06 - 0.04) / 92 * days_offset
        expected = (1 + expected_rate) ** ((self.curve.value_date - dt.date(2014, 9, 1).toordinal()) / 365)
        self.assertEqual(self.curve.price(DateRange("2014-9-1")), expected)

    def test_forward_discount_factor(self):
        days_offset = (dt.date(2014, 9, 1) - dt.date(2014, 7, 1)).days
        expected_rate = 0.04 + (0.06 - 0.04) / 92 * days_offset
        expected = (1 + expected_rate) ** ((self.curve.value_date - dt.date(2014, 9, 1).toordinal()) / 365)
        expected /= (1 + 0.04) ** ((self.curve.value_date - dt.date(2014, 7, 1).toordinal()) / 365)
        period = DateRange(dt.date(2014, 7, 1), dt.date(2014, 9, 1))
        self.assertEqual(self.curve.forward_price(period), expected)

class ForeignDiscountCurveTestCase(unittest.TestCase):

    def setUp(self):
        domestic_quotes = RatesQuotes(GBP,
                                      {dt.date(2013, 12, 19): 0.01,
                                       dt.date(2014, 1, 1): 0.03,
                                       dt.date(2014, 4, 1): 0.032},
                                      value_date=dt.date(2013, 12, 18))
        self.domestic_curve = DiscountCurve(domestic_quotes)
        fx_quotes = FxQuotes({dt.date(2013, 12, 18): 1.2,
                              dt.date(2013, 12, 19): 1.3,
                              dt.date(2014, 1, 1): 1.4,
                              dt.date(2014, 4, 1): 1.5},
                             value_date=dt.date(2013, 12, 18),
                             unit=USD/GBP)
        self.fx_curve = FxForwardCurve(fx_quotes)
        self.foreign_discount_curve = ForeignDiscountCurve(self.domestic_curve, self.fx_curve)
        fx_inverse_quotes = FxQuotes({dt.date(2013, 12, 18): 1 / 1.2,
                              dt.date(2013, 12, 19): 1 / 1.3,
                              dt.date(2014, 1, 1): 1 / 1.4,
                              dt.date(2014, 4, 1): 1 / 1.5},
                             value_date=dt.date(2013, 12, 18),
                             unit=GBP/USD)
        self.inverse_fx_curve = FxForwardCurve(fx_inverse_quotes)
        self.inverse_foreign_discount_curve = ForeignDiscountCurve(self.domestic_curve, self.fx_curve)
        usdeur_fx_quotes = FxQuotes({dt.date(2013, 12, 18): 1.2,
                              dt.date(2013, 12, 19): 1.3,
                              dt.date(2014, 1, 1): 1.4,
                              dt.date(2014, 4, 1): 1.5},
                             value_date=dt.date(2013, 12, 18),
                             unit=USD/EUR)
        self.usdeur_curve = FxForwardCurve(usdeur_fx_quotes)

    def test_price(self):
        date = dt.date(2014, 2, 15)
        self.assertEqual(self.foreign_discount_curve.price(date),
                         self.domestic_curve.price(date) * self.fx_curve.price(dt.date(2013, 12, 18)) /
                         self.fx_curve.price(date))

    def test_arbitrage(self):
        today = dt.date(2013, 12, 18)
        expiry = dt.date(2014, 2, 15)
        domestic_cash_at_expiry = 1 * GBP
        foreign_cash_at_expiry = self.fx_curve.price(expiry) * domestic_cash_at_expiry
        self.assertEqual(foreign_cash_at_expiry.unit, USD)
        domestic_cash_today = domestic_cash_at_expiry * self.domestic_curve.price(expiry)
        self.assertEqual(domestic_cash_today.unit, GBP)
        foreign_cash_today = foreign_cash_at_expiry * self.foreign_discount_curve.price(expiry)
        self.assertEqual(foreign_cash_today.unit, USD)
        gbp_value_of_foreign_cash_today = foreign_cash_today / self.fx_curve.price(today)
        self.assertAlmostEqual(domestic_cash_today.value, gbp_value_of_foreign_cash_today.value)
        self.assertEqual(domestic_cash_today.unit, gbp_value_of_foreign_cash_today.unit)

    def test_price_inverse(self):
        date = dt.date(2014, 2, 15)
        self.assertEqual(self.foreign_discount_curve.price(date), self.inverse_foreign_discount_curve.price(date))

    def test_currency_check(self):
        with self.assertRaises(TypeError):
            ForeignDiscountCurve(self.domestic_curve, self.usdeur_curve)

class InverseFxCurveTestCase(unittest.TestCase):

    def setUp(self):
        fx_quotes = FxQuotes({dt.date(2013, 12, 18): 1.2,
                              dt.date(2013, 12, 19): 1.3,
                              dt.date(2014, 1, 1): 1.4,
                              dt.date(2014, 4, 1): 1.5},
                             value_date=dt.date(2013, 12, 18),
                             unit=USD / GBP)
        self.fx_curve = FxForwardCurve(fx_quotes)
        fx_inverse_quotes = FxQuotes({dt.date(2013, 12, 18): 1 / 1.2,
                                      dt.date(2013, 12, 19): 1 / 1.3,
                                      dt.date(2014, 1, 1): 1 / 1.4,
                                      dt.date(2014, 4, 1): 1 / 1.5},
                                     value_date=dt.date(2013, 12, 18),
                                     unit=GBP / USD)
        self.inverse_fx_curve = FxForwardCurve(fx_inverse_quotes)

    def test_inverse(self):
        self.assertAlmostEqual(self.fx_curve.inverse.price(dt.date(2014, 2, 20)).value,
                               self.inverse_fx_curve.price(dt.date(2014, 2, 20)).value)