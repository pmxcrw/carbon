from core.forward_curves.commodity_forward_curve import CommodityForwardCurve
from core.forward_curves.shape_ratio import ShapeAlgorithm
from core.forward_curves.daily_shape_calibration import SeasonBasedDailyShapeCalibration
from core.quantity.quantity import PENCE, THERM
from core.time_period.date_range import DateRange
from core.time_period.load_shape import WEEKDAY, WEEKEND, BASE
from core.forward_curves.quotes import ContinuousQuotes
from core.time_period.settlement_rules import GasSettlementRule
from core.forward_curves.tests.mock_curves import MockNullDiscountCurve

import datetime as dt
import unittest

class ShifftedForwardCurveTestCase(unittest.TestCase):

    def setUp(self):
        dict = {DateRange("2015-M1"): 70 * PENCE / THERM,
                DateRange("2015-M2"): 60 * PENCE / THERM,
                DateRange("2015-M3"): 55 * PENCE / THERM}
        self.monthly_quotes = ContinuousQuotes(dict, GasSettlementRule)
        self.quarterly_quotes = ContinuousQuotes({DateRange("2015-Q1"): 62 * PENCE / THERM}, GasSettlementRule)
        self.shift = 1.1

    def test_shifting_a_month_on_a_monthly_curve(self):
        jan = DateRange("2015-M1")
        feb = DateRange("2015-M2")
        base_curve = CommodityForwardCurve(self.monthly_quotes, MockNullDiscountCurve)
        shifted_curve = base_curve.shift(jan, self.shift)
        self.assertEqual(shifted_curve.price(jan), 77 * PENCE / THERM)
        self.assertEqual(shifted_curve.price(feb), 60 * PENCE / THERM)

    def test_shifting_a_non_month_on_a_monthly_curve(self):
        jan = DateRange("2015-M1")
        feb = DateRange("2015-M2")
        q1 = DateRange("2015-Q1")
        base_curve = CommodityForwardCurve(self.monthly_quotes, MockNullDiscountCurve)
        shifted_curve = base_curve.shift(q1, self.shift)
        self.assertEqual(shifted_curve.price(jan), 77 * PENCE / THERM)
        self.assertEqual(shifted_curve.price(feb), 66 * PENCE / THERM)
        self.assertEqual(base_curve.price(jan), 70 * PENCE / THERM)

    def test_shifting_intersecting_but_not_contained_period(self):
        jan = DateRange("2015-M1")
        feb = DateRange("2015-M2")
        q1 = DateRange("2015-Q1")
        base_curve = CommodityForwardCurve(self.monthly_quotes, MockNullDiscountCurve)
        shifted_curve = base_curve.shift(jan, self.shift)
        self.assertEqual(shifted_curve.price(jan), 77 * PENCE / THERM)
        self.assertEqual(shifted_curve.price(feb), 60 * PENCE / THERM)
        self.assertTrue(abs(shifted_curve.price(q1) - 64.1333333333334 * PENCE / THERM) < 1e-7 * PENCE / THERM)

    def test_shifting_with_shaping(self):
        s_to_q = {BASE: [1.1, 0.9, 1, 1]}
        q_to_m = {BASE: [1.2, 1.2, 0.6, 1.1, 1, 0.9, 1, 1, 1, 1, 1, 1]}
        wdwe = {WEEKDAY: 1.0, WEEKEND: 1.0}
        base_ratios = SeasonBasedDailyShapeCalibration(s_to_q, q_to_m, wdwe)
        base_curve = CommodityForwardCurve(self.quarterly_quotes, MockNullDiscountCurve, base_ratios)
        shift_period = DateRange(dt.date(2015, 1, 1), dt.date(2015, 1, 7))
        shifted_curve = base_curve.shift(shift_period, self.shift)

        check_period = DateRange(dt.date(2015, 1, 1), dt.date(2015, 1, 14))
        for day in check_period:
            ratio = shifted_curve.price(day) / base_curve.price(day)
            self.assertEqual(ratio, self.shift if day in shift_period else 1.0)