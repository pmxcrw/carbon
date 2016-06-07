# TODO: update for LoadShapedDateRangeSet unit tests
# TODO: compare against Thorn unit tests

import datetime as dt
import unittest

from core.time_period.date_range import DateRange
from core.time_period.load_shape import BASE, PEAK, OFFPEAK, \
    DAYTIME, NIGHTTIME, WEEKDAY, WEEKEND, WEEKEND_OFFPEAK, WEEKDAY_OFFPEAK, WEEKEND_PEAK
from core.time_period.time_period_sets import DateRangeSet, LoadShapeSet


class TestLoadShapeSet(unittest.TestCase):

    def test_parse_collection(self):
        collection = [BASE, 'Offpeak', PEAK]
        expected = {BASE, OFFPEAK, PEAK}
        self.assertEqual(expected, LoadShapeSet(collection).load_shapes)

    def test_partition(self):
        self.assertEqual(LoadShapeSet({PEAK}).partition, {PEAK})
        base_peak = {BASE, PEAK}
        peak_offpeak = {PEAK, OFFPEAK}
        self.assertEqual(LoadShapeSet(base_peak).partition, peak_offpeak)
        dt_nt = {DAYTIME, NIGHTTIME}
        self.assertEqual(LoadShapeSet(dt_nt).partition, dt_nt)
        wd_we = {WEEKDAY, WEEKEND}
        self.assertEqual(LoadShapeSet(wd_we).partition, wd_we)
        weop_wdop_wepk = {WEEKEND_OFFPEAK, WEEKDAY_OFFPEAK, WEEKEND_PEAK}
        self.assertEqual(LoadShapeSet(weop_wdop_wepk).partition, weop_wdop_wepk)
        weop_base_wdop_wepk = {WEEKEND_OFFPEAK, BASE, WEEKDAY_OFFPEAK,
                               WEEKEND_PEAK}
        weop_peak_wdop_wepk = {WEEKEND_OFFPEAK, PEAK, WEEKDAY_OFFPEAK,
                               WEEKEND_PEAK}
        self.assertEqual(LoadShapeSet(weop_base_wdop_wepk).partition,
                         weop_peak_wdop_wepk)
        wdop_wdp_weop_wep = {WEEKEND_OFFPEAK, PEAK, WEEKEND_PEAK,
                             WEEKDAY_OFFPEAK}
        self.assertEqual(LoadShapeSet(wdop_wdp_weop_wep).partition,
                         wdop_wdp_weop_wep)

        self.assertEqual(LoadShapeSet({}).partition, set())


class TestDateRangeSet(unittest.TestCase):
    def setUp(self):
        self.drs = DateRangeSet({DateRange('2016'),
                                 DateRange('2016-SUM'),
                                 DateRange('2016-M1'),
                                 DateRange(dt.date(2016, 1, 31), dt.date(2016, 2, 29)),
                                 DateRange('2016-Q3'),
                                 DateRange('2018')})

    def test_parse_collection(self):
        collection = [DateRange('2015-05-20'), DateRange('2014'), '2015', dt.date(1978, 5, 20)]
        expected = {DateRange('2015-05-20'),
                    DateRange('2014'),
                    DateRange('2015'),
                    DateRange(dt.date(1978, 5, 20), range_type='d')}
        self.assertEqual(expected, DateRangeSet(collection).date_ranges)

    def test_partition(self):
        expected = {DateRangeSet({DateRange(dt.date(2016, 1, 1), dt.date(2016, 1, 30))}),
                    DateRangeSet({DateRange(dt.date(2016, 1, 31), dt.date(2016, 1, 31))}),
                    DateRangeSet({DateRange(dt.date(2016, 2, 1), dt.date(2016, 2, 29))}),
                    DateRangeSet({DateRange(dt.date(2016, 10, 1), dt.date(2016, 12, 31)),
                                  DateRange(dt.date(2016, 3, 1), dt.date(2016, 3, 31))}),
                    DateRangeSet({DateRange(dt.date(2016, 4, 1), dt.date(2016, 6, 30))}),
                    DateRangeSet({DateRange(dt.date(2016, 7, 1), dt.date(2016, 9, 30))}),
                    DateRangeSet({DateRange(dt.date(2018, 1, 1), dt.date(2018, 12, 31))})}
        self.assertEqual(expected, self.drs.partition)

    def test_intersects(self):
        self.assertTrue(self.drs.intersects(DateRange('2017-WIN')))
        self.assertFalse(self.drs.intersects(DateRange('2017-SUM')))

    def test_partition_cover(self):
        expected = {DateRangeSet({DateRange(dt.date(2018, 1, 1), dt.date(2018, 12, 31))})}
        self.assertEqual(expected, self.drs.partition_intersecting(DateRange('2018-SUM')))
        self.assertNotEqual(expected, self.drs.partition_intersecting(DateRange('2017-SUM')))

    def test_str(self):
        expected = "DateRangeSet({DateRange(start=2018-01-01, end=2018-12-31)})"
        self.assertEqual(expected, str(DateRangeSet([DateRange('2018')])))

    def test_repr(self):
        expected = "DateRangeSet({DateRange(start=2018-01-01, end=2018-12-31)})"
        self.assertEqual(expected, repr(DateRangeSet([DateRange('2018')])))
