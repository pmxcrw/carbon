from core.forward_curves.shape_ratio import IntradayShapeRatioCurve, DailyShapeRatioCurve
from core.forward_curves.tests.testing_data import intraday_shape_ratios
from core.time_period.load_shape import HOURS, DAYTIME, NIGHTTIME, EFAS
from core.time_period.date_range import LoadShapedDateRange
from core.forward_curves.quotes import AbstractQuotes

import datetime as dt
import unittest

class IntraDayShapedForwardCurveTestCase(unittest.TestCase):

    def setUp(self):
        quotes = {LoadShapedDateRange(dt.date(2015, 5, 1) + dt.timedelta(d), DAYTIME): 100 + d / 100
                  for d in range(0, 10)}
        quotes.update({LoadShapedDateRange(dt.date(2015, 5, 1) + dt.timedelta(d), NIGHTTIME): 100 + d / 37
                       for d in range(0, 10)})
        quotes = AbstractQuotes(quotes)
        self.curve = DailyShapeRatioCurve(quotes)
        self.intraday_shaped_curve = IntradayShapeRatioCurve(self.curve, intraday_shape_ratios)

    def test_one_hour_price(self):
        time_period = LoadShapedDateRange(dt.date(2015, 5, 5), HOURS[0])
        denominator, ratio = intraday_shape_ratios.extract_shape_ratio(time_period)
        self.assertAlmostEqual(self.intraday_shaped_curve.price(time_period), ratio * self.curve.price(time_period))

    def test_efa_price(self):
        time_periods = [LoadShapedDateRange(dt.date(2015, 5, 5), HOURS[h]) for h in range(4)]
        ratio_denominator_period = [intraday_shape_ratios.extract_shape_ratio(time_period)
                                    for time_period in time_periods]
        ratio = sum(x[1] for x in ratio_denominator_period) / 4
        time_period = LoadShapedDateRange(dt.date(2015, 5, 5), EFAS[0])
        denominator_period = ratio_denominator_period[0][0]
        self.assertAlmostEqual(self.intraday_shaped_curve.price(time_period),
                               ratio * self.curve.price(denominator_period))