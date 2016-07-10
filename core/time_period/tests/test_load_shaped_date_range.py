import datetime as dt
import unittest

from core.quantity.quantity import DAY
from core.time_period.date_range import DateRange, _YearType, _DayType, LoadShapedDateRange, NEVER_LSDR
from core.time_period.load_shape import BASE, PEAK, OFFPEAK, \
    WEEKDAY_OFFPEAK, \
    WEEKEND_OFFPEAK, \
    WEEKEND_PEAK, \
    EFAS, \
    WEEKEND, \
    NIGHTTIME, \
    HOURS, \
    WEEKDAY_HOURS, \
    NEVER_LS


class LoadShapedDateRangeTestCase(unittest.TestCase):
    def setUp(self):
        self.dec = DateRange('2012-M12')
        self.dec_base = LoadShapedDateRange('2012-M12', 'Base')
        self.dec_peak = LoadShapedDateRange('2012-M12', 'Peak')
        self.dec_offpeak = LoadShapedDateRange(self.dec, OFFPEAK)
        self.q4 = DateRange('2012-Q4')
        self.sum12 = DateRange('2012-SUM')
        self.sat = DateRange(dt.date(2012, 12, 8), dt.date(2012, 12, 8))
        self.sun = self.sat.offset(1)
        self.sat_base = LoadShapedDateRange(self.sat)
        self.sat_offpeak = LoadShapedDateRange(self.sat, 'Offpeak')
        self.sat_peak = LoadShapedDateRange(self.sat, PEAK)
        self.sun_peak = LoadShapedDateRange(self.sun, 'Peak')
        self.fri = self.sat.offset(-1)
        self.fri_base = LoadShapedDateRange(self.fri, BASE)
        self.fri_peak = LoadShapedDateRange(self.fri, PEAK)
        self.fri_offpeak = LoadShapedDateRange(self.fri, OFFPEAK)
        self.jan_efa1 = LoadShapedDateRange('2014-M1', 'EFA1')

    def test_init(self):
        self.assertEqual(self.dec_base.date_range, self.dec)
        self.assertEqual(self.dec_base.load_shape, BASE)
        self.assertEqual(self.sat_base.date_range, self.sat)
        self.assertEqual(self.sat_base.load_shape, BASE)

    def test_offset(self):
        self.assertEqual(self.sat_peak.offset(), self.sun_peak)

    def test_null(self):
        null = LoadShapedDateRange(self.sat, PEAK)
        self.assertEqual(null.duration, 0)

    def test_duration(self):
        self.assertEqual(self.dec_peak.duration, 10.5 * DAY)
        self.assertEqual(self.dec_offpeak.duration, 20.5 * DAY)
        self.assertTrue(abs(self.jan_efa1.duration - 31 * 4 / 24 * DAY) < 1e-10 * DAY)

        # dec_12 has 10 weekend-days and 21 weekdays
        expected = {BASE: 31,
                    PEAK: 21 * 0.5,
                    OFFPEAK: 21 * 0.5 + 10,
                    WEEKDAY_OFFPEAK: 21 * 0.5,
                    WEEKEND_OFFPEAK: 10 * 0.5,
                    WEEKEND_PEAK: 10 * 0.5,
                    WEEKEND: 10,
                    NIGHTTIME: 31 * 0.5,
                    NEVER_LS: 0,
                    HOURS[2]: 31 / 24,
                    WEEKDAY_HOURS[2]: 21 / 24}
        for load_shape, expected in expected.items():
            lsdr = LoadShapedDateRange('2012-M12', load_shape)
            self.assertTrue(abs(lsdr.duration - expected * DAY) < 1e-10 * DAY)

    def test_eq(self):
        self.assertNotEqual(self.sat, self.sat_offpeak)
        self.assertNotEqual(self.sat_offpeak, self.sat)
        self.assertNotEqual(self.sat, self.sat_base)
        self.assertNotEqual(self.sat_offpeak, self.sat_base)
        self.assertNotEqual(self.sat_peak, NEVER_LSDR)

    def test_equivalent(self):
        # equivalance means the same delivery hours
        self.assertTrue(self.sat_base.equivalent(self.sat_offpeak))
        self.assertFalse(self.fri_base.equivalent(self.fri_offpeak))
        self.assertTrue(self.sat_peak.equivalent(NEVER_LSDR))
        self.assertTrue(self.sat_peak.equivalent(self.sun_peak))

    def test_intersection(self):
        self.assertEqual(self.fri_peak.intersection(self.fri_offpeak),
                         NEVER_LSDR)
        self.assertEqual(self.sat_peak.intersection(self.fri_peak),
                         NEVER_LSDR)
        self.assertEqual(self.dec_offpeak.intersection(self.fri_base),
                         self.fri_offpeak)
        self.assertEqual(self.fri_peak.intersection(OFFPEAK), NEVER_LSDR)
        self.assertEqual(OFFPEAK.intersection(self.fri_peak), NEVER_LSDR)
        self.assertEqual(self.fri_base.intersection(OFFPEAK), self.fri_offpeak)
        self.assertEqual(OFFPEAK.intersection(self.fri_base), self.fri_offpeak)

    def test_intersects(self):
        self.assertFalse(self.sat_base.intersects(self.sun_peak))
        self.assertTrue(self.fri_base.intersects(self.fri_peak))
        self.assertTrue(self.fri_peak.intersects(self.fri_base))
        self.assertFalse(self.fri_peak.intersects(self.fri_offpeak))
        self.assertFalse(self.sat_peak.intersects(self.sat_base))
        self.assertTrue(self.fri_base.intersects(OFFPEAK))
        self.assertFalse(self.fri_peak.intersects(OFFPEAK))
        self.assertTrue(OFFPEAK.intersects(self.fri_base))
        self.assertFalse(OFFPEAK.intersects(self.fri_peak))
        # intersection is sat_peak, which has a duration of zero
        # intersects method only returns true if duration is non-zero

    def test_start(self):
        self.assertEqual(self.dec_peak.start, dt.date(2012, 12, 1))

    def test_end(self):
        self.assertEqual(self.dec_peak.end, dt.date(2012, 12, 31))

    def test_contains(self):
        self.assertTrue(LoadShapedDateRange('2012-Q4', PEAK) in
                        LoadShapedDateRange('2012-Q4', BASE))
        self.assertFalse(LoadShapedDateRange('2012-Q4', BASE) in
                         LoadShapedDateRange('2012-Q4', PEAK))
        self.assertTrue(LoadShapedDateRange('2012-M11', BASE) in
                        LoadShapedDateRange('2012-Q4', BASE))
        self.assertFalse(LoadShapedDateRange('2012-Q4', BASE) in
                         LoadShapedDateRange('2012-M11', BASE))
        self.assertTrue(LoadShapedDateRange('2012-M11', HOURS[1]) in
                        LoadShapedDateRange('2012-Q4', EFAS[0]))
        self.assertFalse(LoadShapedDateRange('2012-Q4', EFAS[0]) in
                         LoadShapedDateRange('2012-M11', HOURS[1]))

    def test_split_by_month(self):
        lsdr = LoadShapedDateRange(DateRange(dt.date(2011, 11, 17),
                                             dt.date(2012, 3, 4)),
                                   PEAK)
        ranges = [DateRange(dt.date(2011, 11, 17), dt.date(2011, 11, 30)),
                  DateRange('2011-M12'),
                  DateRange('2012-M1'),
                  DateRange('2012-M2'),
                  DateRange(dt.date(2012, 3, 1), dt.date(2012, 3, 4))]
        self.assertEqual(lsdr.split_by_month,
                         [LoadShapedDateRange(x, PEAK) for x in ranges])

    def test_split_by_quarter(self):
        lsdr = LoadShapedDateRange(DateRange(dt.date(2011, 11, 17),
                                             dt.date(2012, 3, 4)),
                                   PEAK)
        ranges = [DateRange(dt.date(2011, 11, 17), dt.date(2011, 12, 31)),
                  DateRange(dt.date(2012, 1, 1), dt.date(2012, 3, 4))]
        self.assertEqual(lsdr.split_by_quarter,
                         [LoadShapedDateRange(x, PEAK) for x in ranges])

    def test_split_by_range_type(self):
        lsdr = LoadShapedDateRange(DateRange(dt.date(2011, 11, 17),
                                             dt.date(2013, 3, 4)),
                                   PEAK)
        ranges = [DateRange(dt.date(2011, 11, 17), dt.date(2011, 12, 31)),
                  DateRange('2012'),
                  DateRange(dt.date(2013, 1, 1), dt.date(2013, 3, 4))]
        self.assertEqual(lsdr.split_by_range_type(_YearType),
                         [LoadShapedDateRange(x, PEAK) for x in ranges])

    def test_iter(self):
        ls = LoadShapedDateRange(DateRange(dt.date(2011, 11, 17),
                                           dt.date(2011, 11, 23)),
                                 PEAK)
        dr = [DateRange(dt.date(2011, 11, 17), range_type='d')]
        dr += [DateRange(dt.date(2011, 11, 18), dt.date(2011, 11, 18))]
        drl = DateRange(dt.date(2011, 11, 21), dt.date(2011, 11, 23))
        dr += drl.split_by_range_type(_DayType)
        self.assertEqual([l for l in ls],
                         [LoadShapedDateRange(i, PEAK) for i in dr])

    def test_difference(self):
        q4_base = LoadShapedDateRange(self.q4, BASE)
        win12_base = LoadShapedDateRange('2012-WIN', 'Base')
        q1_13 = win12_base.difference(q4_base)
        self.assertTrue(q1_13[0].equivalent(NEVER_LSDR) and
                        q1_13[1].equivalent(NEVER_LSDR) and
                        q1_13[2].equivalent(LoadShapedDateRange('2013-Q1',
                                                                'Base')))
        never = q4_base.difference(win12_base)
        self.assertTrue(never[0].equivalent(NEVER_LSDR) and
                        never[1].equivalent(NEVER_LSDR) and
                        never[2].equivalent(NEVER_LSDR))

        winter = LoadShapedDateRange('2012')
        winter = winter.difference(LoadShapedDateRange('2012-SUM', 'Peak'))
        self.assertTrue(winter[0].equivalent(LoadShapedDateRange('2012-Q1')) and
                        winter[1].equivalent(LoadShapedDateRange('2012-SUM', 'Offpeak')) and
                        winter[2].equivalent(LoadShapedDateRange('2012-Q4')))
