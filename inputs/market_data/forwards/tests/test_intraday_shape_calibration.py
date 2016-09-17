import unittest

from core.forward_curves.shape_ratio import UnshapedDailyRatioCurve
from core.time_period.date_range import LoadShapedDateRange
from core.time_period.load_shape import WEEKDAY_HOURS, WEEKEND_HOURS, PEAK, WEEKEND_OFFPEAK, BASE, WEEKDAY_EFAS
from inputs.market_data.forwards.intraday_shape_calibration import PowerIntradayShapeCalibration
from inputs.market_data.forwards.tests.testing_data import intraday_shape_ratios, wd_pk, we_op, wd_op


class IntraDayShapeCalibrationTestCase(unittest.TestCase):

    def test_time_of_week_index(self):
        time_period = LoadShapedDateRange("2016-7-31", WEEKDAY_HOURS[8])
        self.assertEqual(PowerIntradayShapeCalibration._load_shape_index(time_period), 1)  # wd_pk
        time_period = LoadShapedDateRange("2016-7-31", WEEKEND_HOURS[7])
        self.assertEqual(PowerIntradayShapeCalibration._load_shape_index(time_period), 2)  # we_op

    def test_month_index(self):
        time_period = LoadShapedDateRange("2015-7-31", WEEKDAY_HOURS[8])
        self.assertEqual(PowerIntradayShapeCalibration._month_index(time_period), 6)

    def test_hour_index(self):
        hours_and_expected_indices = [
            # daytime
            (8, 0), (19, 11),
            # nighttime
            (0, 0), (7, 7), (20, 8), (23, 11)]
        for hour, i in hours_and_expected_indices:
            time_period = LoadShapedDateRange("2016-7-31", WEEKDAY_HOURS[hour])
            self.assertEqual(PowerIntradayShapeCalibration._hour_index(time_period), i)

    def test_get_peak_ratio(self):
        time_period = LoadShapedDateRange("2016-7-29", WEEKDAY_HOURS[8])
        denominator_time_period = LoadShapedDateRange("2016-7-29", PEAK)
        expected = (denominator_time_period, wd_pk[6][0])
        self.assertEqual(intraday_shape_ratios.extract_shape_ratio(time_period), expected)

        time_period = LoadShapedDateRange("2016-7-29", WEEKDAY_HOURS[19])
        denominator_time_period = LoadShapedDateRange("2016-7-29", PEAK)
        expected = (denominator_time_period, wd_pk[6][11])
        self.assertEqual(intraday_shape_ratios.extract_shape_ratio(time_period), expected)

        time_period = LoadShapedDateRange("2016-7-31", WEEKEND_HOURS[0])
        denominator_time_period = LoadShapedDateRange("2016-7-31", WEEKEND_OFFPEAK)
        expected = (denominator_time_period, we_op[6][0])
        self.assertEqual(intraday_shape_ratios.extract_shape_ratio(time_period), expected)


    def test_decorate(self):
        unshaped = UnshapedDailyRatioCurve()
        intraday = intraday_shape_ratios.decorate(unshaped)
        time_period = LoadShapedDateRange("2016-08-02", BASE)
        self.assertAlmostEqual(intraday.price(time_period), 1)
        with self.assertRaises(AssertionError):
            time_period = LoadShapedDateRange("2016-08-02", WEEKEND_HOURS[0])
            self.assertEqual(intraday.price(time_period), wd_op[7][0])
        time_period = LoadShapedDateRange("2016-M8", WEEKDAY_HOURS[0])
        self.assertAlmostEqual(intraday.price(time_period), wd_op[7][0])
        time_period = LoadShapedDateRange("2016-M4", WEEKDAY_EFAS[3])
        expected = (1.121479411 + 1.081247748 + 0.981449994 + 0.897401978) / 4
        self.assertAlmostEqual(intraday.price(time_period), expected)