import datetime as dt
import unittest

from core.time_period.date_range import DateRange
from core.time_period.load_shape import LoadShape, BASE, PEAK, OFFPEAK, \
    DAYTIME, NIGHTTIME, WEEKDAY, WEEKEND, WEEKEND_OFFPEAK, WEEKDAY_OFFPEAK, WEEKEND_PEAK
from core.time_period.time_period_sets import TimePeriodSet, DateRangeSet, LoadShapeSet, LoadShapedDateRangeSet, LoadShapeType, DateRangeType, LoadShapedDateRangeType
from core.time_period.load_shaped_date_range import LoadShapedDateRange


class TestTimePeriodSet(unittest.TestCase):

    def setUp(self):
        self.drs = TimePeriodSet({DateRange('2016'),
                                  DateRange('2016-SUM'),
                                  DateRange('2016-M1'),
                                  DateRange(dt.date(2016, 1, 31), dt.date(2016, 2, 29)),
                                  DateRange('2016-Q3'),
                                  DateRange('2018')})

    def test_init(self):

        # test homogeneous collections
        lss = TimePeriodSet([LoadShape('peak'), LoadShape('offpeak'), BASE])
        expected = {LoadShape('peak'), LoadShape('offpeak'), BASE}
        self.assertEqual(len(lss), len(expected))
        self.assertTrue(all(ls in expected for ls in lss))
        self.assertTrue(all(e in lss for e in expected))
        self.assertEqual(LoadShapeType, lss.time_period_type)
        self.assertEqual(None, lss.default_load_shape)
        drs = TimePeriodSet([DateRange('2012-M2'), DateRange('2016'), DateRange('2017')])
        expected = {DateRange('2012-M2'), DateRange('2016'), DateRange('2017')}
        self.assertEqual(len(drs), len(expected))
        self.assertTrue(all(dr in expected for dr in drs))
        self.assertTrue(all(e in drs for e in expected))
        self.assertEqual(DateRangeType, drs.time_period_type)
        self.assertEqual(None, drs.default_load_shape)
        lsdrs = TimePeriodSet([LoadShapedDateRange('2012-M2'), LoadShapedDateRange('2015', 'offpeak')])
        expected = {LoadShapedDateRange('2012-M2'), LoadShapedDateRange('2015', 'offpeak')}
        self.assertEqual(len(lsdrs), len(expected))
        self.assertTrue(all(lsdr in expected for lsdr in lsdrs))
        self.assertTrue(all(e in lsdrs for e in expected))
        self.assertEqual(LoadShapedDateRangeType, lsdrs.time_period_type)
        self.assertEqual(None, drs.default_load_shape)
        with self.assertRaises(ValueError):
            TimePeriodSet({LoadShape('peak'), DateRange('2015'), LoadShapedDateRange('2016', 'weekend')})

        # test parsing LoadShape types
        lss_parse = TimePeriodSet({'peak', 'offpeak', 'base'}, LoadShape)
        self.assertEqual(lss, lss_parse)
        lss_parse = TimePeriodSet(['peak', LoadShape('offpeak'), BASE], 'load shape')
        self.assertEqual(lss, lss_parse)
        lss_parse = TimePeriodSet(('peak', LoadShape('offpeak'), BASE), LoadShapeType)
        self.assertEqual(lss, lss_parse)
        with self.assertRaises(ValueError):
            TimePeriodSet({'peak', 'offpeak', 'base'}, 'xyz')
        with self.assertRaises(ValueError):
            TimePeriodSet({'peak', 'offpeak', 'base'}, 3)
        with self.assertRaises(ValueError):
            TimePeriodSet({'peak', BASE, DateRange('2015')}, LoadShapeType)
        with self.assertRaises(ValueError):
            TimePeriodSet({'peak', BASE, LoadShapedDateRange('2015', 'base')}, LoadShapeType)
        with self.assertRaises(TypeError):
            TimePeriodSet({'peak', 'offpeak', 'base'}, int)
        with self.assertRaises(TypeError):
            TimePeriodSet({'peak', 'offpeak', 'base'}, LoadShape, BASE)

        # test parsing DateRange types
        drs_parse = TimePeriodSet({'2012-M2', DateRange('2016'), '2017'}, DateRange)
        self.assertEqual(drs, drs_parse)
        drs_parse = TimePeriodSet({'2012-M2', '2016', '2017'}, 'date range')
        self.assertEqual(drs, drs_parse)
        drs_parse = TimePeriodSet({'2012-M2', '2016', '2017'}, DateRangeType)
        self.assertEqual(drs, drs_parse)
        drs_parse = TimePeriodSet({'2016', dt.date(2016, 5, 20), DateRange('2017')}, DateRangeType)
        expected = TimePeriodSet({DateRange('2016'), DateRange('2016-05-20'), DateRange('2017')})
        self.assertEqual(expected, drs_parse)
        with self.assertRaises(ValueError):
            TimePeriodSet({'2012-M2', '2016', '2017'}, 'xyz')
        with self.assertRaises(ValueError):
            TimePeriodSet({'2012-M2', '2016', '2017'}, 3)
        with self.assertRaises(ValueError):
            TimePeriodSet({BASE, DateRange('2015')}, DateRangeType)
        with self.assertRaises(ValueError):
            TimePeriodSet({'2016', LoadShapedDateRange('2015', 'base')}, LoadShapeType)
        with self.assertRaises(TypeError):
            TimePeriodSet({'peak', 'offpeak', 'base'}, int)
        with self.assertRaises(TypeError):
            TimePeriodSet({'peak', 'offpeak', 'base'}, LoadShape, BASE)

        # test parsing LoadShapedDateRange types
        lsdrs = TimePeriodSet({LoadShapedDateRange('2012-M2', 'offpeak'),
                               LoadShapedDateRange('2016', 'offpeak'),
                               LoadShapedDateRange('2017', 'offpeak')})
        lsdrs_parse = TimePeriodSet({'2012-M2', DateRange('2016'), '2017'}, LoadShapedDateRange, 'offpeak')
        self.assertEqual(lsdrs, lsdrs_parse)
        lsdrs_parse = TimePeriodSet({'2012-M2', '2016', '2017'}, 'load shaped date range', 'offpeak')
        self.assertEqual(lsdrs, lsdrs_parse)
        lsdrs_parse = TimePeriodSet({'2012-M2', '2016', '2017'}, LoadShapedDateRangeType, OFFPEAK)
        self.assertEqual(lsdrs, lsdrs_parse)
        lsdrs_parse = TimePeriodSet({LoadShapedDateRange('2016', 'peak'),
                                     dt.date(2016, 5, 20),
                                     DateRange('2017')},
                                    LoadShapedDateRange, 'peak')
        expected = TimePeriodSet({LoadShapedDateRange('2016', 'peak'),
                                  LoadShapedDateRange('2016-05-20', 'peak'),
                                  LoadShapedDateRange('2017', PEAK)})
        self.assertEqual(expected, lsdrs_parse)
        with self.assertRaises(ValueError):
            TimePeriodSet({'peak', LoadShapedDateRange('2015', 'base')}, LoadShapedDateRangeType, BASE)
        with self.assertRaises(ValueError):
            TimePeriodSet({'2015', '2016', '2017'}, LoadShapedDateRange)

    def test_eq(self):
        lss = TimePeriodSet([LoadShape('peak'), LoadShape('offpeak'), BASE])
        drs = TimePeriodSet([DateRange('2012-M2'), DateRange('2016'), DateRange('2017')])
        self.assertFalse(lss == drs)
        lss2 = TimePeriodSet({'peak', 'offpeak', 'base'}, LoadShapeType)
        self.assertTrue(lss == lss2)
        lss2.default_load_shape = BASE
        self.assertFalse(lss == lss2)
        drs2 = TimePeriodSet({'2012-M2', '2016', '2017'}, DateRangeType)
        drs2.time_period_type = LoadShapeType
        self.assertNotEqual(drs, drs2)
        self.assertEqual(drs, TimePeriodSet({'2012-M2', '2016', '2017'}, DateRangeType))

    def test_union(self):
        left = TimePeriodSet(['base', 'peak'], LoadShape)
        expected = TimePeriodSet([BASE, PEAK, OFFPEAK])
        self.assertEqual(expected, left.union(['offpeak']))
        expected = TimePeriodSet([BASE, PEAK, WEEKDAY_OFFPEAK, WEEKEND_OFFPEAK])
        self.assertEqual(expected, left.union(TimePeriodSet([WEEKDAY_OFFPEAK, WEEKEND_OFFPEAK])))
        with self.assertRaises(TypeError):
            left.union(TimePeriodSet([DateRange('2012'), DateRange('2013')]))
        expected = TimePeriodSet({DateRange('2016'),
                                 DateRange('2016-SUM'),
                                 DateRange('2016-M1'),
                                 DateRange(dt.date(2016, 1, 31), dt.date(2016, 2, 29)),
                                 DateRange('2016-Q3'),
                                 DateRange('2018'),
                                 DateRange('2019')})
        self.assertEqual(expected, self.drs.union(['2019']))

    def test_str(self):
        expected = "TimePeriodSet({DateRange(start=2018-01-01, end=2018-12-31)})"
        self.assertEqual(expected, str(TimePeriodSet([DateRange('2018')])))

    def test_repr(self):
        expected = "TimePeriodSet({DateRange(start=2018-01-01, end=2018-12-31)})"
        self.assertEqual(expected, repr(TimePeriodSet([DateRange('2018')])))

    def test_intersects(self):
        self.assertTrue(self.drs.intersects(DateRange('2017-WIN')))
        self.assertFalse(self.drs.intersects(DateRange('2017-SUM')))
        with self.assertRaises(TypeError):
            self.drs.intersects(BASE)
        self.assertTrue(self.drs.intersects(TimePeriodSet({'2017-WIN', '2020'}, DateRange)))
        self.assertFalse(self.drs.intersects(TimePeriodSet({'2017-SUM', '2020'}, DateRange)))
        with self.assertRaises(TypeError):
            self.drs.intersects(TimePeriodSet({'2017-WIN', '2020'}, LoadShapedDateRange, BASE))

    def test_intersection(self):
        expected = TimePeriodSet({'2018-Q1'}, DateRange)
        self.assertEqual(expected, self.drs.intersection(DateRange('2017-WIN')))
        self.assertEqual(expected, self.drs.intersection(TimePeriodSet({'2017-WIN', '2020'}, DateRange)))
        expected = TimePeriodSet([])
        self.assertEqual(expected, self.drs.intersection(DateRange('2017-SUM')))
        self.assertEqual(expected, self.drs.intersection(TimePeriodSet({'2017-SUM', '2020'}, DateRange)))

    def test_LoadShape_partition(self):
        self.assertEqual(TimePeriodSet({PEAK}).partition, {PEAK})
        base_peak = {BASE, PEAK}
        peak_offpeak = {PEAK, OFFPEAK}
        self.assertEqual(TimePeriodSet(base_peak).partition, peak_offpeak)
        dt_nt = {DAYTIME, NIGHTTIME}
        self.assertEqual(TimePeriodSet(dt_nt).partition, dt_nt)
        wd_we = {WEEKDAY, WEEKEND}
        self.assertEqual(TimePeriodSet(wd_we).partition, wd_we)
        weop_wdop_wepk = {WEEKEND_OFFPEAK, WEEKDAY_OFFPEAK, WEEKEND_PEAK}
        self.assertEqual(TimePeriodSet(weop_wdop_wepk).partition, weop_wdop_wepk)
        weop_base_wdop_wepk = {WEEKEND_OFFPEAK, BASE, WEEKDAY_OFFPEAK,
                               WEEKEND_PEAK}
        weop_peak_wdop_wepk = {WEEKEND_OFFPEAK, PEAK, WEEKDAY_OFFPEAK,
                               WEEKEND_PEAK}
        self.assertEqual(TimePeriodSet(weop_base_wdop_wepk).partition,
                         weop_peak_wdop_wepk)
        wdop_wdp_weop_wep = {WEEKEND_OFFPEAK, PEAK, WEEKEND_PEAK,
                             WEEKDAY_OFFPEAK}
        self.assertEqual(TimePeriodSet(wdop_wdp_weop_wep).partition,
                         wdop_wdp_weop_wep)

        with self.assertRaises(TypeError):
            TimePeriodSet({}).partition

    def test_DateRange_partition(self):
        expected = set([TimePeriodSet({DateRange(dt.date(2016, 1, 1), dt.date(2016, 1, 30))}),
                    TimePeriodSet({DateRange(dt.date(2016, 1, 31), dt.date(2016, 1, 31))}),
                    TimePeriodSet({DateRange(dt.date(2016, 2, 1), dt.date(2016, 2, 29))}),
                    TimePeriodSet({DateRange(dt.date(2016, 10, 1), dt.date(2016, 12, 31)),
                                  DateRange(dt.date(2016, 3, 1), dt.date(2016, 3, 31))}),
                    TimePeriodSet({DateRange(dt.date(2016, 4, 1), dt.date(2016, 6, 30))}),
                    TimePeriodSet({DateRange(dt.date(2016, 7, 1), dt.date(2016, 9, 30))}),
                    TimePeriodSet({DateRange(dt.date(2018, 1, 1), dt.date(2018, 12, 31))})])

        self.assertEqual(expected, self.drs.partition)

        expected = {TimePeriodSet([DateRange('2012-M12')]),
                    TimePeriodSet({DateRange(dt.date(2012, 10, 1), dt.date(2012, 11, 30))})}
        example = TimePeriodSet({DateRange('2012-M12'), DateRange('2012-Q4')})
        self.assertEqual(expected, example.partition)


class TestLoadShapeSet(unittest.TestCase):

    def test_init(self):
        collection = [BASE, 'Offpeak', PEAK]
        expected = {BASE, OFFPEAK, PEAK}
        self.assertEqual(expected, LoadShapeSet(collection))
        with self.assertRaises(ValueError):
            LoadShapeSet([BASE, 'Offpeak', PEAK, 'xyz'])

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

    def test_hash(self):
        self.assertEqual(hash(LoadShapeSet([PEAK, 'Offpeak'])), hash(LoadShapeSet((OFFPEAK, 'Peak'))))

    def test_union(self):
        left = LoadShapeSet(['base', 'peak'])
        expected = LoadShapeSet([BASE, PEAK, OFFPEAK])
        self.assertEqual(expected, left.union(['offpeak']))

class TestDateRangeSet(unittest.TestCase):

    def setUp(self):
        self.drs = DateRangeSet({DateRange('2016'),
                                 DateRange('2016-SUM'),
                                 DateRange('2016-M1'),
                                 DateRange(dt.date(2016, 1, 31), dt.date(2016, 2, 29)),
                                 DateRange('2016-Q3'),
                                 DateRange('2018')})

    def test_init(self):
        collection = [DateRange('2015-05-20'), DateRange('2014'), '2015', dt.date(1978, 5, 20)]
        expected = {DateRange('2015-05-20'),
                    DateRange('2014'),
                    DateRange('2015'),
                    DateRange(dt.date(1978, 5, 20), range_type='d')}
        self.assertEqual(DateRangeSet(collection), expected)
        with self.assertRaises(ValueError):
            DateRangeSet((DateRange('2012'), '2013', 'xyz'))

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

        expected = {DateRangeSet([DateRange('2012-M12')]),
                    DateRangeSet({DateRange(dt.date(2012, 10, 1), dt.date(2012, 11, 30))})}
        example = DateRangeSet({DateRange('2012-M12'), DateRange('2012-Q4')})
        self.assertEqual(expected, example.partition)

    def test_union(self):
        expected = DateRangeSet({DateRange('2016'),
                                 DateRange('2016-SUM'),
                                 DateRange('2016-M1'),
                                 DateRange(dt.date(2016, 1, 31), dt.date(2016, 2, 29)),
                                 DateRange('2016-Q3'),
                                 DateRange('2018'),
                                 DateRange('2019')})
        self.assertEqual(expected, self.drs.union(['2019']))

    def test_intersects(self):
        self.assertTrue(self.drs.intersects(DateRange('2017-WIN')))
        self.assertFalse(self.drs.intersects(DateRange('2017-SUM')))

    def test_partition_cover(self):
        expected = {DateRangeSet({DateRange(dt.date(2018, 1, 1), dt.date(2018, 12, 31))})}
        self.assertEqual(expected, self.drs.partition_intersecting(DateRange('2018-SUM')))
        self.assertEqual(set(), self.drs.partition_intersecting(DateRange('2017-SUM')))

        example = DateRangeSet({DateRange('2012-M12'), DateRange('2012-Q4')})
        expected = {DateRangeSet({DateRange(dt.date(2012, 10, 1), dt.date(2012, 11, 30))})}
        self.assertEqual(expected, example.partition_intersecting(DateRange('2012-11-28')))

        da = DateRange('2012-1-26')
        wend = DateRange(dt.date(2012, 1, 28), dt.date(2012, 1, 29))
        bom = DateRange(dt.date(2012, 1, 27), dt.date(2012, 1, 31))
        drs = DateRangeSet((da, wend, bom))
        output = drs.partition_intersecting(DateRange('2012-1-27'))
        expected = {DateRangeSet([DateRange('2012-1-27'),
                                 DateRange(dt.date(2012, 1, 30), dt.date(2012, 1, 31))])}
        self.assertEqual(expected, output)


    def test_str(self):
        expected = "DateRangeSet({DateRange(start=2018-01-01, end=2018-12-31)})"
        self.assertEqual(expected, str(DateRangeSet([DateRange('2018')])))

    def test_repr(self):
        expected = "DateRangeSet({DateRange(start=2018-01-01, end=2018-12-31)})"
        self.assertEqual(expected, repr(DateRangeSet([DateRange('2018')])))


class LoadShapedDateRangeSetTest(unittest.TestCase):

    def setUp(self):
        self.feb_12_peak = LoadShapedDateRange('2012-M2', 'Peak')
        self.feb_12_offpeak = LoadShapedDateRange('2012-M2', 'Offpeak')
        self.q1_12_base = LoadShapedDateRange('2012-Q1', 'Base')
        self.test_set = LoadShapedDateRangeSet([self.feb_12_peak, self.q1_12_base])
        self.A = LoadShapedDateRangeSet([self.feb_12_peak])
        self.B = LoadShapedDateRangeSet([self.feb_12_offpeak])
        self.C = LoadShapedDateRangeSet([LoadShapedDateRange('2012-M1', 'Base'),
                                         LoadShapedDateRange('2012-M3', 'Base')])
        self.D = self.B.union(self.C)

    def test_init(self):
        expected_drs = DateRangeSet([DateRange('2012-M2'), DateRange('2012-Q1')])
        expected_lsdr_set = {self.feb_12_peak, self.q1_12_base}
        self.assertEqual(expected_drs, self.test_set.date_range_set)
        self.assertEqual(expected_lsdr_set, self.test_set)

    def test_equivalence(self):
        expected = {LoadShapedDateRangeSet({LoadShapedDateRange('2012-M2', 'Peak')})}
        input = LoadShapedDateRangeSet({LoadShapedDateRange('2012-M2', 'Peak')})
        self.assertEqual(expected, input.partition)

        expected = {LoadShapedDateRangeSet({LoadShapedDateRange('2012-M2', 'Peak')}),
                    LoadShapedDateRangeSet({LoadShapedDateRange('2012-M1', 'Base'),
                                            LoadShapedDateRange('2012-M2', 'Offpeak'),
                                            LoadShapedDateRange('2012-M3', 'Base')})}
        self.assertEqual(expected, self.test_set.partition)