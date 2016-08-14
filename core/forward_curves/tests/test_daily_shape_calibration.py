from core.forward_curves.daily_shape_calibration import SeasonBasedDailyShapeCalibration, \
    CalendarBasedDailyShapeCalibration, _ShapeRatioTree
from core.time_period.load_shape import OFFPEAK, PEAK, WEEKEND, WEEKDAY, WEEKEND_OFFPEAK, BASE
from core.time_period.time_period_sets import TimePeriodSet
from core.time_period.date_range import LoadShapedDateRange, DateRange

import unittest

class SeasonBasedDailyShapeCalibrationTestCase(unittest.TestCase):

    def test_find_period(self):
        s_to_q = {OFFPEAK: [1.1, 0.9, 1, 1], PEAK: [1, 1, 0.9, 1.1]}
        q_to_m = {OFFPEAK: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], PEAK: [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]}
        wdwe = {WEEKEND: 1, WEEKDAY: 1}
        daily = SeasonBasedDailyShapeCalibration(s_to_q, q_to_m, wdwe)
        lsdr = daily._find_period(TimePeriodSet({LoadShapedDateRange("2016-Q1", WEEKEND_OFFPEAK)}))
        self.assertEqual(lsdr, LoadShapedDateRange("2015-WIN", OFFPEAK))
        with self.assertRaises(ValueError):
            daily._find_period(TimePeriodSet({LoadShapedDateRange("2016-Q1", BASE)}))


class CalendarBasedDailyShapeCalibrationTestCase(unittest.TestCase):

    def test_find_period(self):
        s_to_q = {OFFPEAK: [1.1, 0.9, 1, 1], PEAK: [1, 1, 0.9, 1.1]}
        q_to_m = {OFFPEAK: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], PEAK: [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]}
        wdwe = {WEEKEND: 1, WEEKDAY: 1}
        daily = CalendarBasedDailyShapeCalibration(s_to_q, q_to_m, wdwe)
        lsdr = daily._find_period(TimePeriodSet({LoadShapedDateRange("2016-Q1", WEEKEND_OFFPEAK)}))
        self.assertEqual(lsdr, LoadShapedDateRange("2016", OFFPEAK))
        with self.assertRaises(ValueError):
            daily._find_period(TimePeriodSet({LoadShapedDateRange("2016-Q1", BASE)}))


class ShapeRatiosTestCase(unittest.TestCase):

    summer11_tree = _ShapeRatioTree(LoadShapedDateRange("2011-SUM"), frozenset([
        (1.05, _ShapeRatioTree(LoadShapedDateRange("2011-Q2"), frozenset([
            (1.1, _ShapeRatioTree(LoadShapedDateRange("2011-M4"), frozenset([
                (1.1, _ShapeRatioTree(LoadShapedDateRange("2011-M4", WEEKDAY))),
                (1.0, _ShapeRatioTree(LoadShapedDateRange("2011-M4", WEEKEND)))]))),
            (1.2, _ShapeRatioTree(LoadShapedDateRange("2011-M5"), frozenset([
                (1.1, _ShapeRatioTree(LoadShapedDateRange("2011-M5", WEEKDAY))),
                (1.0, _ShapeRatioTree(LoadShapedDateRange("2011-M5", WEEKEND)))]))),
            (1.1, _ShapeRatioTree(LoadShapedDateRange("2011-M6"), frozenset([
                (1.1, _ShapeRatioTree(LoadShapedDateRange("2011-M6", WEEKDAY))),
                (1.0, _ShapeRatioTree(LoadShapedDateRange("2011-M6", WEEKEND)))])))]))),
        (0.95, _ShapeRatioTree(LoadShapedDateRange("2011-Q3"), frozenset([
            (1.3, _ShapeRatioTree(LoadShapedDateRange("2011-M7"), frozenset([
                (1.1, _ShapeRatioTree(LoadShapedDateRange("2011-M7", WEEKDAY))),
                (1.0, _ShapeRatioTree(LoadShapedDateRange("2011-M7", WEEKEND)))]))),
            (1.4, _ShapeRatioTree(LoadShapedDateRange("2011-M8"), frozenset([
                (1.1, _ShapeRatioTree(LoadShapedDateRange("2011-M8", WEEKDAY))),
                (1.0, _ShapeRatioTree(LoadShapedDateRange("2011-M8", WEEKEND)))]))),
            (1.3, _ShapeRatioTree(LoadShapedDateRange("2011-M9"), frozenset([
                (1.1, _ShapeRatioTree(LoadShapedDateRange("2011-M9", WEEKDAY))),
                (1.0, _ShapeRatioTree(LoadShapedDateRange("2011-M9", WEEKEND)))])))])))]))

    def test_season_sum(self):
        """Check that SeadonBasedShapeRatios can create a ShapeRatioTree for a summer period"""
        s_to_q = {BASE: [0, 1.05, 0.95, 0]}
        q_to_m = {BASE: [0, 0, 0, 1.1, 1.2, 1.1, 1.3, 1.4, 1.3, 0, 0, 0]}
        wd_we = {WEEKDAY: 1.1, WEEKEND: 1.0}
        ratios = SeasonBasedDailyShapeCalibration(s_to_q, q_to_m, wd_we)
        period = ratios._find_period(TimePeriodSet([LoadShapedDateRange("2011-SUM")]))
        constructed_tree = ratios._tree(period)
        self.assertEqual(constructed_tree, self.summer11_tree)

    winter10_tree = _ShapeRatioTree(LoadShapedDateRange("2010-WIN"), frozenset([
        (1.05, _ShapeRatioTree(LoadShapedDateRange("2010-Q4"), frozenset([
            (1.1, _ShapeRatioTree(LoadShapedDateRange("2010-M10"), frozenset([
                (1.1, _ShapeRatioTree(LoadShapedDateRange("2010-M10", WEEKDAY))),
                (1.0, _ShapeRatioTree(LoadShapedDateRange("2010-M10", WEEKEND)))]))),
            (1.2, _ShapeRatioTree(LoadShapedDateRange("2010-M11"), frozenset([
                (1.1, _ShapeRatioTree(LoadShapedDateRange("2010-M11", WEEKDAY))),
                (1.0, _ShapeRatioTree(LoadShapedDateRange("2010-M11", WEEKEND)))]))),
            (1.1, _ShapeRatioTree(LoadShapedDateRange("2010-M12"), frozenset([
                (1.1, _ShapeRatioTree(LoadShapedDateRange("2010-M12", WEEKDAY))),
                (1.0, _ShapeRatioTree(LoadShapedDateRange("2010-M12", WEEKEND)))])))]))),
        (0.95, _ShapeRatioTree(LoadShapedDateRange("2011-Q1"), frozenset([
            (1.3, _ShapeRatioTree(LoadShapedDateRange("2011-M1"), frozenset([
                (1.1, _ShapeRatioTree(LoadShapedDateRange("2011-M1", WEEKDAY))),
                (1.0, _ShapeRatioTree(LoadShapedDateRange("2011-M1", WEEKEND)))]))),
            (1.4, _ShapeRatioTree(LoadShapedDateRange("2011-M2"), frozenset([
                (1.1, _ShapeRatioTree(LoadShapedDateRange("2011-M2", WEEKDAY))),
                (1.0, _ShapeRatioTree(LoadShapedDateRange("2011-M2", WEEKEND)))]))),
            (1.3, _ShapeRatioTree(LoadShapedDateRange("2011-M3"), frozenset([
                (1.1, _ShapeRatioTree(LoadShapedDateRange("2011-M3", WEEKDAY))),
                (1.0, _ShapeRatioTree(LoadShapedDateRange("2011-M3", WEEKEND)))])))])))]))

    def test_season_win(self):
        """Check that SeadonBasedShapeRatios can create a ShapeRatioTree for a summer period"""
        s_to_q = {BASE: [0.95, 0, 0, 1.05]}
        q_to_m = {BASE: [1.3, 1.4, 1.3, 0, 0, 0, 0, 0, 0, 1.1, 1.2, 1.1]}
        wd_we = {WEEKDAY: 1.1, WEEKEND: 1.0}
        ratios = SeasonBasedDailyShapeCalibration(s_to_q, q_to_m, wd_we)
        period = ratios._find_period(TimePeriodSet([LoadShapedDateRange("2010-WIN")]))
        constructed_tree = ratios._tree(period)
        self.assertEqual(constructed_tree, self.winter10_tree)

    def test_shape_ratio_curve(self):
        s_to_q = {BASE: [0.95, 0, 0, 1.05]}
        q_to_m = {BASE: [1.3, 1.4, 1.3, 0, 0, 0, 0, 0, 0, 1.1, 1.2, 1.1]}
        wd_we = {WEEKDAY: 1.1, WEEKEND: 1.0}
        calibration = SeasonBasedDailyShapeCalibration(s_to_q, q_to_m, wd_we)
        curve = calibration.shape_ratio_curve(TimePeriodSet([LoadShapedDateRange("2010-WIN")]))
        q41_ratio = curve.price(LoadShapedDateRange("2010-Q4")) / curve.price(DateRange("2011-Q1"))
        self.assertAlmostEqual(q41_ratio, 1.05 / 0.95)
        m1011_ratio = curve.price(DateRange("2010-M10")) / curve.price(DateRange("2010-M11"))
        self.assertAlmostEqual(m1011_ratio, 1.1 / 1.2)

    def test_curve_season_shape_ratio(self):
        s_to_q = {BASE: [0, 1.05, 0.95, 0]}
        q_to_m = {BASE: [0, 0, 0, 1.1, 1.2, 1.1, 1.3, 1.4, 1.3, 0, 0, 0]}
        wd_we = {WEEKDAY: 1.1, WEEKEND: 1.0}
        calibration = SeasonBasedDailyShapeCalibration(s_to_q, q_to_m, wd_we)
        curve = calibration.shape_ratio_curve(TimePeriodSet([DateRange("2011-Q2"), DateRange("2011-Q3")]))
        self.assertAlmostEqual(curve.price(DateRange("2011-Q2")), 1.05 * 183 / (1.05 * 91 + 0.95 * 92))
        # cover memoisation
        self.assertAlmostEqual(curve.price(DateRange("2011-Q2")), 1.05 * 183 / (1.05 * 91 + 0.95 * 92))

    def test_curve_calendar_shape_ratio(self):
        cal_to_q = {BASE: [1, 1.05, 0.95, 1]}
        q_to_m = {BASE: [1, 1, 1, 1.1, 1.2, 1.1, 1.3, 1.4, 1.3, 1, 1, 1]}
        wd_we = {WEEKDAY: 1.1, WEEKEND: 1.0}
        calibration = CalendarBasedDailyShapeCalibration(cal_to_q, q_to_m, wd_we)
        curve = calibration.shape_ratio_curve(TimePeriodSet([DateRange("2011-Q2"), DateRange("2011-Q3")]))

        # test cal_to_q
        expected_q_ratio = 1.05 * 365 / (1 * 90 + 1.05 * 91 + 0.95 * 92 + 1 * 92)
        self.assertAlmostEqual(curve.price(DateRange("2011-Q2")), expected_q_ratio)

        # test q_to_m
        expected_m_ratio = 1.2 * 91 / (1.1 * 30 + 1.2 * 31 + 1.1 * 30)
        self.assertAlmostEqual(curve.price(DateRange("2011-M5")), expected_q_ratio * expected_m_ratio)
