import datetime as dt
import unittest

from core.base.quantity import DAY
from core.forward_curves.tests.mock_curves import mock_discount_curve
from core.time_period.date_range import DateRange, LoadShapedDateRange
from core.time_period.settlement_rules import GasSettlementRule, UKPowerSettlementRule, DayOfDeliverySettlementRule, \
                                              EUASettlementRule


class GasSettlementRuleTest(unittest.TestCase):

    def test_single_month(self):
        dec_12 = DateRange('2012-M12')
        dec_12_settlement_day = dt.date(2013, 1, 20)
        discount_factor = mock_discount_curve.price(dec_12_settlement_day)
        self.assertEqual(dec_12.duration * discount_factor,
                         dec_12.discounted_duration(GasSettlementRule, mock_discount_curve))

    def test_load_shaped_date_range(self):
        q4_12_peak = LoadShapedDateRange('2012-Q4', 'Peak')
        dfs = [0.99, 0.98, 0.97]
        discounted_time = 0
        for split_time, df in zip(q4_12_peak.split_by_month, dfs):
            discounted_time += split_time.duration * df
        self.assertEqual(discounted_time, q4_12_peak.discounted_duration(GasSettlementRule, mock_discount_curve))
        dict = {LoadShapedDateRange('2012-M10', 'Peak'): dt.date(2012, 11, 20),
                LoadShapedDateRange('2012-M11', 'Peak'): dt.date(2012, 12, 20),
                LoadShapedDateRange('2012-M12', 'Peak'): dt.date(2013, 1, 20)}
        self.assertEqual(dict, q4_12_peak.settlement_dates(GasSettlementRule))

    def test_overlapping_period(self):
        period = LoadShapedDateRange(DateRange(dt.date(2012, 10, 5), dt.date(2013, 1, 5)), 'Peak')
        dict = {
            LoadShapedDateRange(DateRange(dt.date(2012, 10, 5), dt.date(2012, 10, 31)), 'Peak'): dt.date(2012, 11, 20),
            LoadShapedDateRange('2012-M11', 'Peak'): dt.date(2012, 12, 20),
            LoadShapedDateRange('2012-M12', 'Peak'): dt.date(2013, 1, 20),
            LoadShapedDateRange(DateRange(dt.date(2013, 1, 1), dt.date(2013, 1, 5)), 'Peak'): dt.date(2013, 2, 20)}
        self.assertEqual(dict, period.settlement_dates(GasSettlementRule))


class UKPowerSettlementRuleTest(unittest.TestCase):

    def test_single_month(self):
        dec_12 = DateRange('2012-M12')
        dec_12_settlement_day = dt.date(2013, 1, 14)
        discount_factor = mock_discount_curve.price(dec_12_settlement_day)
        self.assertEqual(dec_12.duration * discount_factor,
                         dec_12.discounted_duration(UKPowerSettlementRule, mock_discount_curve))

    def test_load_shaped_date_range(self):
        q4_12_peak = LoadShapedDateRange('2012-Q4', 'Peak')
        dfs = [0.995, 0.985, 0.975]
        discounted_time = 0
        for split_time, df in zip(q4_12_peak.split_by_month, dfs):
            discounted_time += split_time.duration * df
        self.assertEqual(discounted_time, q4_12_peak.discounted_duration(UKPowerSettlementRule, mock_discount_curve))
        dict = {LoadShapedDateRange('2012-M10', 'Peak'): dt.date(2012, 11, 14),
                LoadShapedDateRange('2012-M11', 'Peak'): dt.date(2012, 12, 14),
                LoadShapedDateRange('2012-M12', 'Peak'): dt.date(2013, 1, 14)}
        self.assertEqual(dict, q4_12_peak.settlement_dates(UKPowerSettlementRule))

    def test_overlapping_period(self):
        period = LoadShapedDateRange(DateRange(dt.date(2012,10,5), dt.date(2013,1,5)), 'Peak')
        dict = {
            LoadShapedDateRange(DateRange(dt.date(2012, 10, 5), dt.date(2012, 10, 31)), 'Peak'): dt.date(2012, 11, 14),
            LoadShapedDateRange('2012-M11', 'Peak'): dt.date(2012, 12, 14),
            LoadShapedDateRange('2012-M12', 'Peak'): dt.date(2013, 1, 14),
            LoadShapedDateRange(DateRange(dt.date(2013, 1, 1), dt.date(2013, 1, 5)), 'Peak'): dt.date(2013, 2, 14)}
        self.assertEqual(dict, period.settlement_dates(UKPowerSettlementRule))


class DayOfDeliverySettlementRuleTest(unittest.TestCase):

    def test_single_period(self):
        period = LoadShapedDateRange(DateRange(dt.date(2013, 1, 4), dt.date(2013, 1, 6)), 'offpeak')
        expected = (0.978 / 2 + 0.977 + 0.99) * DAY
        self.assertEqual(expected, period.discounted_duration(DayOfDeliverySettlementRule, mock_discount_curve))
        dict = {LoadShapedDateRange('2013-1-4', 'offpeak'): dt.date(2013, 1, 4),
                LoadShapedDateRange('2013-1-5', 'offpeak'): dt.date(2013, 1, 5),
                LoadShapedDateRange('2013-1-6', 'offpeak'): dt.date(2013, 1, 6)}
        self.assertEqual(dict, period.settlement_dates(DayOfDeliverySettlementRule))

    def test_single_period(self):
        period = DateRange(dt.date(2013, 1, 4), dt.date(2013, 1, 6))
        expected = (0.978 + 0.977 + 0.99) * DAY
        self.assertEqual(expected, period.discounted_duration(DayOfDeliverySettlementRule, mock_discount_curve))
        dict = {DateRange('2013-1-4'): dt.date(2013, 1, 4),
                DateRange('2013-1-5'): dt.date(2013, 1, 5),
                DateRange('2013-1-6'): dt.date(2013, 1, 6)}
        self.assertEqual(dict, period.settlement_dates(DayOfDeliverySettlementRule))


    def test_weekend_peak(self):
        period = LoadShapedDateRange('2014-09-28', 'peak')
        self.assertEqual(period.discounted_duration(DayOfDeliverySettlementRule, mock_discount_curve), 0 * DAY)

class EUASettlementRuleTest(unittest.TestCase):

    def test_settlement_rule(self):
        period = DateRange('2012-WIN')
        expected = mock_discount_curve.price(dt.date(2013, 1, 1)) * DateRange('2012-Q4').duration
        expected += mock_discount_curve.price(dt.date(2014, 1, 1)) * DateRange('2013-Q1').duration
        self.assertEqual(expected, period.discounted_duration(EUASettlementRule, mock_discount_curve))
        dict = {DateRange('2012-Q4'): dt.date(2013, 1, 1),
                DateRange('2013-Q1'): dt.date(2014, 1, 1)}
        self.assertEqual(dict, period.settlement_dates(EUASettlementRule))