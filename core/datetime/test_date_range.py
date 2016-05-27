from core.datetime.date_range import date_ranges, DateRange, RangeType, NeverType,\
    AlwaysType, DayType, WeekType, MonthType, QuarterType, YearType, GasYearType

import unittest
import datetime as dt


class DateRangeGenericTest(unittest.TestCase):

    def setUp(self):
        self.test_start = dt.date(2012,9,13)
        self.test_end = dt.date(2016, 1, 3)
        self.test_range_type = RangeType
        self.test_string = "2012-9-13 to 2016-1-3"
        self.test_DR1 = DateRange(self.test_start, self.test_end)

    def test_init(self):
        self.assertEqual(self.test_DR1.start, self.test_start)
        self.assertEqual(self.test_DR1.end, self.test_end)
        self.assertEqual(self.test_DR1.range_type, self.test_range_type)