import datetime as dt
import unittest

from pandas.util.testing import assertRaises

from core.time_period.date_range import DateRange, _RangeType, _NeverType,\
    _AlwaysType, _DayType, _WeekType, _MonthType, _QuarterType, _YearType, _GasYearType,\
    _SummerType, _WinterType


class DateRangeGenericTest(unittest.TestCase):

    def setUp(self):
        self.test_start = dt.date(2012, 9, 13)
        self.test_end = dt.date(2016, 1, 3)
        self.test_range_type = _RangeType
        self.test_string = "2012-9-13 to 2016-1-3"
        self.test_DR1 = DateRange(self.test_start, self.test_end)
        self.repr_msg = "DateRange(start={}, end={})".format(self.test_start,
                                                             self.test_end)
        self.str_msg = "DateRange({} to {})".format(self.test_start,
                                                    self.test_end)

    def test_init(self):
        self.assertEqual(self.test_DR1.start, self.test_start)
        self.assertEqual(self.test_DR1.end, self.test_end)
        self.assertEqual(self.test_DR1.range_type, self.test_range_type)
        with self.assertRaises(ValueError):
            DateRange(self.test_string)
        with self.assertRaises(TypeError):
            DateRange(self.test_start, "R")

    def test_offset(self):
        with self.assertRaises(NotImplementedError):
            self.test_DR1.offset(3)

    def test_str(self):
        self.assertEqual(str(self.test_DR1), self.str_msg)

    def test_repr(self):
        # doesn't need repeating for other strategy objects
        self.assertEqual(repr(self.test_DR1), self.repr_msg)

    def test_len(self):
        # doesn't need repeating for other strategy objects
        start = dt.date(2000, 1, 1)
        end = dt.date(2000, 1, 31)
        self.assertEqual(31, len(DateRange(start, end)))

    def test_contains(self):
        # doesn't need repeating for other strategy objects
        self.assertTrue(dt.date(2015, 5, 20) in self.test_DR1)
        self.assertFalse(dt.date(1978, 5, 20) in self.test_DR1)

    def test_eq(self):
        # doesn't need repeating for other strategy objects
        a = DateRange(dt.date(2012, 9, 13), dt.date(2016, 1, 3))
        b = DateRange('2014-M3')
        self.assertTrue(self.test_DR1 == a)
        self.assertFalse(self.test_DR1 == b)

    def test_neq(self):
        # doesn't need repeating for other strategy objects
        a = DateRange(dt.date(2012, 9, 13), dt.date(2016, 1, 3))
        b = DateRange('2014-M3')
        self.assertFalse(self.test_DR1 != a)
        self.assertTrue(self.test_DR1 != b)

    def test_iter(self):
        # doesn't need repeating for other strategy objects
        output = [dt.date(2000, 1, i+1) for i in range(31)]
        start = dt.date(2000, 1, 1)
        end = dt.date(2000, 1, 31)
        self.assertEqual(output, [date for date in DateRange(start, end)])

    def test_intersection(self):
        # doesn't need repeating for other strategy objects
        a = DateRange('2015-Q2')
        b = DateRange(dt.date(2015, 6, 1), dt.date(2015, 12, 31))
        c = DateRange('2015-M6')
        self.assertEqual(c, a.intersection(b))
        self.assertEqual(c, b.intersection(a))
        self.assertTrue(a.intersects(b))
        self.assertTrue(b.intersects(a))
        d = DateRange('2016')
        e = DateRange('never')
        self.assertEqual(e, a.intersection(d))
        self.assertFalse(e.intersects(a))

    def test_difference(self):
        # doesn't need repeating for other strategy objects
        a = DateRange('2016')
        b = DateRange('2016-SUM')
        c = DateRange('2016-Q1')
        d = DateRange('2016-Q4')
        self.assertEqual((c, d), a.difference(b))
        e = DateRange(dt.date(2016, 1, 1), dt.date(2016, 9, 30))
        f = DateRange('never')
        self.assertEqual((e, f), a.difference(d))
        g = DateRange(dt.date(2016, 4, 1), dt.date(2016, 12, 31))
        self.assertEqual((f, g), a.difference(c))

    def test_weekend_and_weekday_duration(self):
        # doesn't need repeating for other strategy objects
        a = DateRange('2016-M5')
        b, c = a.weekday_and_weekend_duration
        self.assertEqual(b, 22)
        self.assertEqual(c, 9)

    def test_split_by_range_type(self):
        # doesn't need repeating for other strategy objects
        a = DateRange(dt.date(2000, 1, 1), dt.date(2003, 12, 31))
        output = [DateRange('2000-Q1'),
                  DateRange('2000-SUM'),
                  DateRange('2000-WIN'),
                  DateRange('2001-SUM'),
                  DateRange('2001-WIN'),
                  DateRange('2002-SUM'),
                  DateRange('2002-WIN'),
                  DateRange('2003-SUM'),
                  DateRange('2003-Q4')]
        self.assertEqual(output, a.split_by_range_type(_SummerType))
        output = [DateRange(dt.date(2000, 1, 1), dt.date(2000, 9, 30)),
                  DateRange('2000-GY'),
                  DateRange('GY-2001'),
                  DateRange('GY-2002'),
                  DateRange('2003-Q4')]
        self.assertEqual(output, a.split_by_range_type(_GasYearType))
        output = [DateRange('2000'),
                  DateRange('2001'),
                  DateRange('2002'),
                  DateRange('2003')]
        self.assertEqual(output, a.split_by_range_type(_YearType))
        b = DateRange('2016-M1')
        output = [DateRange(dt.date(2016, 1, 1), dt.date(2016, 1, 3)),
                  DateRange('2016-W1'),
                  DateRange('2016-W2'),
                  DateRange('2016-W3'),
                  DateRange('2016-W4')]
        self.assertEqual(output, b.split_by_range_type(_WeekType))
        c = DateRange('2016-W4')
        output = [DateRange('2016-01-25'),
                  DateRange('2016-01-26'),
                  DateRange('2016-01-27'),
                  DateRange('2016-01-28'),
                  DateRange('2016-01-29'),
                  DateRange('2016-01-30'),
                  DateRange('2016-01-31')]
        self.assertEqual(output, c.split_by_range_type(_DayType))

    def test_split_by_month(self):
        # doesn't need repeating for other strategy objects
        a = DateRange('2016-Q2')
        output = [DateRange('2016-M4'),
                  DateRange('2016-M5'),
                  DateRange('2016-M6')]
        self.assertEqual(output, a.split_by_month)

    def test_split_by_quarter(self):
        # doesn't need repeating for other strategy objects
        a = DateRange('GY-2000')
        output = [DateRange('2000-Q4'),
                  DateRange('2001-Q1'),
                  DateRange('2001-Q2'),
                  DateRange('2001-Q3')]
        self.assertEqual(output, a.split_by_quarter)


class DateRangeNeverTest(unittest.TestCase):

    def test_init(self):
        a = DateRange(dt.date(2016, 10, 1), dt.date(2011, 10, 1))
        c = DateRange('never')
        start = dt.date.max - dt.timedelta(365)
        end = dt.date.min
        self.assertEqual(a.start, start)
        self.assertEqual(a.end, end)
        self.assertEqual(a.range_type, _NeverType)
        self.assertEqual(c.start, start)
        self.assertEqual(c.end, end)
        self.assertEqual(c.range_type, _NeverType)

    def test_offset(self):
        with self.assertRaises(NotImplementedError):
            a = DateRange('never')
            a.offset(10)

    def test_str(self):
        self.assertEqual(str(DateRange('Never')), "Never")


class DateRangeAlwaysTest(unittest.TestCase):

    def test_init(self):
        end = dt.date.max - dt.timedelta(365)
        start = dt.date.min
        a = DateRange(start, end)
        c = DateRange('always')
        self.assertEqual(a.start, start)
        self.assertEqual(a.end, end)
        self.assertEqual(a.range_type, _AlwaysType)
        self.assertEqual(c.start, start)
        self.assertEqual(c.end, end)
        self.assertEqual(c.range_type, _AlwaysType)

    def test_offset(self):
        with self.assertRaises(NotImplementedError):
            a = DateRange('always')
            a.offset(10)

    def test_str(self):
        self.assertEqual(str(DateRange('always')), "Always")


class DateRangeDayTest(unittest.TestCase):

    def test_init(self):
        a = DateRange(dt.date(2016, 10, 1), dt.date(2016, 10, 1))
        b = DateRange(dt.date(2016, 1, 1), range_type="d")
        c = DateRange('2015-10-1')
        self.assertEqual(a.start, dt.date(2016, 10, 1))
        self.assertEqual(a.end, dt.date(2016, 10, 1))
        self.assertEqual(a.range_type, _DayType)
        self.assertEqual(b.start, dt.date(2016, 1, 1))
        self.assertEqual(b.end, dt.date(2016, 1, 1))
        self.assertEqual(b.range_type, _DayType)
        self.assertEqual(c.start, dt.date(2015, 10, 1))
        self.assertEqual(c.end, dt.date(2015, 10, 1))
        self.assertEqual(c.range_type, _DayType)

    def test_offset(self):
        a = DateRange('2015-10-1')
        b = DateRange('2015-10-31')
        self.assertEqual(a.offset(30), b)

    def test_str(self):
        self.assertEqual(str(DateRange('2016-10-1')), "2016-10-01")


class DateRangeWeekendTest(unittest.TestCase):

    def test_init(self):
        start1 = dt.date(2014, 12, 29)
        end1 = dt.date(2015, 1, 4)
        a = DateRange(start1, end1)
        b = DateRange(start1, range_type="w")
        c = DateRange('2015-W1')
        self.assertEqual(a.start, start1)
        self.assertEqual(a.end, end1)
        self.assertEqual(a.range_type, _WeekType)
        self.assertEqual(b.start, start1)
        self.assertEqual(b.end, end1)
        self.assertEqual(b.range_type, _WeekType)
        self.assertEqual(c.start, start1)
        self.assertEqual(c.end, end1)
        self.assertEqual(c.range_type, _WeekType)

        start1 = dt.date(2015, 4, 27)
        end1 = dt.date(2015, 5, 3)
        c = DateRange('2015-W18')
        self.assertEqual(c.start, start1)
        self.assertEqual(c.end, end1)
        self.assertEqual(c.range_type, _WeekType)

        start1 = dt.date(2015, 12, 28)
        end1 = dt.date(2016, 1, 3)
        c = DateRange('2015-W53')
        self.assertEqual(c.start, start1)
        self.assertEqual(c.end, end1)
        self.assertEqual(c.range_type, _WeekType)

        start1 = dt.date(2016, 12, 26)
        end1 = dt.date(2017, 1, 1)
        c = DateRange('2016-W52')
        self.assertEqual(c.start, start1)
        self.assertEqual(c.end, end1)
        self.assertEqual(c.range_type, _WeekType)

    def test_offset(self):
        a = DateRange('W52-2015')
        b = DateRange('2016-W4')
        self.assertEqual(a.offset(5), b)
        a = DateRange('W2-2017')
        b = DateRange('W52-2016')
        self.assertEqual(a.offset(-2), b)

    def test_str(self):
        start1 = dt.date(2016, 12, 26)
        end1 = dt.date(2017, 1, 1)
        self.assertEqual(str(DateRange(start1, end1)), "2016-W52")
        start1 = dt.date(2015, 12, 28)
        end1 = dt.date(2016, 1, 3)
        self.assertEqual(str(DateRange(start1, end1)), "2015-W53")
        start1 = dt.date(2015, 4, 27)
        end1 = dt.date(2015, 5, 3)
        self.assertEqual(str(DateRange(start1, end1)), "2015-W18")
        start1 = dt.date(2014, 12, 29)
        end1 = dt.date(2015, 1, 4)
        self.assertEqual(str(DateRange(start1, end1)), "2015-W1")


class DateRangeMonthTest(unittest.TestCase):

    def test_init(self):
        a = DateRange(dt.date(2016, 5, 1), dt.date(2016, 5, 31))
        b = DateRange(dt.date(2016, 2, 20), range_type="mth")
        c = DateRange('M2-2015')
        self.assertEqual(a.start, dt.date(2016, 5, 1))
        self.assertEqual(a.end, dt.date(2016, 5, 31))
        self.assertEqual(a.range_type, _MonthType)
        self.assertEqual(b.start, dt.date(2016, 2, 1))
        self.assertEqual(b.end, dt.date(2016, 2, 29))
        self.assertEqual(b.range_type, _MonthType)
        self.assertEqual(c.start, dt.date(2015, 2, 1))
        self.assertEqual(c.end, dt.date(2015, 2, 28))
        self.assertEqual(c.range_type, _MonthType)
        with self.assertRaises(ValueError):
            DateRange('2016-month5')
        with self.assertRaises(TypeError):
            DateRange(dt.date(2016, 5, 1), dt.date(2016, 5, 31), "month")

    def test_offset(self):
        a = DateRange('M5-2016')
        b = DateRange('2016-M8')
        self.assertEqual(a.offset(3), b)

    def test_str(self):
        self.assertEqual(str(DateRange('M5-2016')), "2016-M5")


class DateRangeQuarterTest(unittest.TestCase):

    def test_init(self):
        a = DateRange(dt.date(2016, 10, 1), dt.date(2016, 12, 31))
        b = DateRange(dt.date(2016, 2, 20), range_type="q")
        c = DateRange('Q2-2015')
        self.assertEqual(a.start, dt.date(2016, 10, 1))
        self.assertEqual(a.end, dt.date(2016, 12, 31))
        self.assertEqual(a.range_type, _QuarterType)
        self.assertEqual(b.start, dt.date(2016, 1, 1))
        self.assertEqual(b.end, dt.date(2016, 3, 31))
        self.assertEqual(b.range_type, _QuarterType)
        self.assertEqual(c.start, dt.date(2015, 4, 1))
        self.assertEqual(c.end, dt.date(2015, 6, 30))
        self.assertEqual(c.range_type, _QuarterType)

    def test_offset(self):
        a = DateRange('Q3-2016')
        b = DateRange('2018-Q1')
        self.assertEqual(a.offset(6), b)

    def test_str(self):
        self.assertEqual(str(DateRange('Q2-2016')), "2016-Q2")


class DateRangeSummerTest(unittest.TestCase):

    def test_init(self):
        a = DateRange(dt.date(2016, 4, 1), dt.date(2016, 9, 30))
        b = DateRange(dt.date(2016, 5, 20), range_type="SUM")
        c = DateRange('SUM-2015')
        self.assertEqual(a.start, dt.date(2016, 4, 1))
        self.assertEqual(a.end, dt.date(2016, 9, 30))
        self.assertEqual(a.range_type, _SummerType)
        self.assertEqual(b.start, dt.date(2016, 4, 1))
        self.assertEqual(b.end, dt.date(2016, 9, 30))
        self.assertEqual(b.range_type, _SummerType)
        self.assertEqual(c.start, dt.date(2015, 4, 1))
        self.assertEqual(c.end, dt.date(2015, 9, 30))
        self.assertEqual(c.range_type, _SummerType)
        with assertRaises(ValueError):
            DateRange(dt.date(2016, 2, 20), range_type="SUM")

    def test_offset(self):
        a = DateRange('SUM-2016')
        b = DateRange('2017-WIN')
        self.assertEqual(a.offset(3), b)

    def test_str(self):
        self.assertEqual(str(DateRange('SUM-2016')), "2016-SUM")


class DateRangeWinterTest(unittest.TestCase):

    def test_init(self):
        a = DateRange(dt.date(2016, 10, 1), dt.date(2017, 3, 31))
        b = DateRange(dt.date(2016, 11, 20), range_type="WIN")
        c = DateRange('WIN-2015')
        self.assertEqual(a.start, dt.date(2016, 10, 1))
        self.assertEqual(a.end, dt.date(2017, 3, 31))
        self.assertEqual(a.range_type, _WinterType)
        self.assertEqual(b.start, dt.date(2016, 10, 1))
        self.assertEqual(b.end, dt.date(2017, 3, 31))
        self.assertEqual(b.range_type, _WinterType)
        self.assertEqual(c.start, dt.date(2015, 10, 1))
        self.assertEqual(c.end, dt.date(2016, 3, 31))
        self.assertEqual(c.range_type, _WinterType)
        with assertRaises(ValueError):
            DateRange(dt.date(2016, 5, 20), range_type="WIN")

    def test_offset(self):
        a = DateRange('WIN-2016')
        b = DateRange('2018-SUM')
        self.assertEqual(a.offset(3), b)

    def test_str(self):
        self.assertEqual(str(DateRange('WIN-2016')), "2016-WIN")


class DateRangeYearTest(unittest.TestCase):

    def test_init(self):
        a = DateRange(dt.date(2016, 1, 1), dt.date(2016, 12, 31))
        b = DateRange(dt.date(2016, 1, 1), range_type="Y")
        c = DateRange('2015')
        self.assertEqual(a.start, dt.date(2016, 1, 1))
        self.assertEqual(a.end, dt.date(2016, 12, 31))
        self.assertEqual(a.range_type, _YearType)
        self.assertEqual(b.start, dt.date(2016, 1, 1))
        self.assertEqual(b.end, dt.date(2016, 12, 31))
        self.assertEqual(b.range_type, _YearType)
        self.assertEqual(c.start, dt.date(2015, 1, 1))
        self.assertEqual(c.end, dt.date(2015, 12, 31))
        self.assertEqual(c.range_type, _YearType)

    def test_offset(self):
        a = DateRange('2016')
        b = DateRange('2018')
        self.assertEqual(a.offset(2), b)

    def test_str(self):
        self.assertEqual(str(DateRange('2016')), "2016")


class DateRangeGasYearTest(unittest.TestCase):

    def test_init(self):
        a = DateRange(dt.date(2016, 10, 1), dt.date(2017, 9, 30))
        b = DateRange(dt.date(2016, 1, 1), range_type="gas_year")
        c = DateRange('2015-GY')
        self.assertEqual(a.start, dt.date(2016, 10, 1))
        self.assertEqual(a.end, dt.date(2017, 9, 30))
        self.assertEqual(a.range_type, _GasYearType)
        self.assertEqual(b.start, dt.date(2015, 10, 1))
        self.assertEqual(b.end, dt.date(2016, 9, 30))
        self.assertEqual(b.range_type, _GasYearType)
        self.assertEqual(c.start, dt.date(2015, 10, 1))
        self.assertEqual(c.end, dt.date(2016, 9, 30))
        self.assertEqual(c.range_type, _GasYearType)

    def test_offset(self):
        a = DateRange('GY-2016')
        b = DateRange('2018-GY')
        self.assertEqual(a.offset(2), b)

    def test_str(self):
        self.assertEqual(str(DateRange('2016-GY')), "GY-2016")
