from core.time_period.relative_date_range import RelativeDateRange

from core.time_period.date_range import DateRange

import unittest
import datetime as dt


class TestRelativeDateRange(unittest.TestCase):

    def setUp(self):
        self.date = dt.date(2012, 9, 13)
        self.weekend = self.date + dt.timedelta(3)

    def test_calendar_day_ahead(self):
        for i in range(-10, 10):
            test_date = self.date + dt.timedelta(i)
            self.assertEqual(DateRange(test_date, test_date),
                             RelativeDateRange('cda', i).fix(self.date))
        self.assertEqual("CalendarDayAhead(offset=10)",
                         str(RelativeDateRange('cda', 10)))

    def test_day_ahead(self):
        wkd_start = self.date
        wend_start = self.weekend

        # test no offset
        self.assertEqual(DateRange(wkd_start, wkd_start),
                         RelativeDateRange('da', 0).fix(wkd_start))
        with self.assertRaises(ValueError):
            RelativeDateRange('da', 0).fix(wend_start)

        # test positive offsets
        test_date = self.date + dt.timedelta(1)
        self.assertEqual(DateRange(test_date, test_date),
                         RelativeDateRange('da').fix(self.date))
        for i in range(2, 7):
            test_date = self.date + dt.timedelta(i + 2)
            self.assertEqual(DateRange(test_date, test_date),
                             RelativeDateRange('da', i).fix(self.date))
        for i in range(7, 12):
            test_date = self.date + dt.timedelta(i + 4)
            self.assertEqual(DateRange(test_date, test_date),
                             RelativeDateRange('da', i).fix(self.date))

        # test negative offsets
        for i in range(-3, 0):
            test_date = self.date + dt.timedelta(i)
            self.assertEqual(DateRange(test_date, test_date),
                             RelativeDateRange('da', i).fix(self.date))
        for i in range(-8, -3):
            test_date = self.date + dt.timedelta(i - 2)
            self.assertEqual(DateRange(test_date, test_date),
                             RelativeDateRange('da', i).fix(self.date))

        self.assertEqual("DayAhead(offset=7)", str(RelativeDateRange('da', 7)))

    def test_weekend_ahead(self):

        # test zero offsets
        wkd_start = self.date + dt.timedelta(2)
        wkd_end = self.weekend
        self.assertEqual(DateRange(wkd_start, wkd_end),
                         RelativeDateRange('wenda', offset=0).fix(wkd_end))
        with self.assertRaises(ValueError):
            RelativeDateRange('wenda', offset=0).fix(self.date)

        # test positive offsets
        for i in range(1, 10):
            output = DateRange(self.date + dt.timedelta(2 + (i-1)*7),
                               self.date + dt.timedelta(3 + (i-1)*7))
            self.assertEqual(output,
                             RelativeDateRange('wenda', offset=i).fix(self.date))
            output = DateRange(self.weekend + dt.timedelta(-1 + i*7),
                               self.weekend + dt.timedelta(i*7))
            self.assertEqual(output,
                             RelativeDateRange('wenda', offset=i).fix(self.weekend))

        # test negative offsets
        for i in range(-2, 0):
            output = DateRange(self.date + dt.timedelta(-5 + (i+1)*7),
                               self.date + dt.timedelta(-4 + (i+1)*7))
            self.assertEqual(output,
                             RelativeDateRange('wenda', offset=i).fix(self.date))
            self.assertEqual(output,
                             RelativeDateRange('wenda', offset=i).fix(self.weekend))

        self.assertEqual('WeekendAhead(offset=-4)',
                         str(RelativeDateRange('wenda', offset=-4)))

    def test_week_ahead(self):

        # test zero offsets
        self.assertEqual(DateRange(start=self.date, range_type="w"),
                         RelativeDateRange('wa', offset=0).fix(self.date))

        # test positive offsets
        self.assertEqual(DateRange(start=self.date, range_type="w").offset(1),
                         RelativeDateRange('wa').fix(self.date))

        # test negative offsets
        self.assertEqual(DateRange(start=self.date, range_type="w").offset(-5),
                         RelativeDateRange('wa', offset=-5).fix(self.date))

        self.assertEqual('WeekAhead(offset=-4)',
                         str(RelativeDateRange('wa', offset=-4)))

    def test_quarter_ahead(self):

        # test zero offsets
        self.assertEqual(DateRange(start=self.date, range_type="q"),
                         RelativeDateRange('qa', offset=0).fix(self.date))

        # test positive offsets
        self.assertEqual(DateRange(start=self.date, range_type="q").offset(1),
                         RelativeDateRange('qa').fix(self.date))

        # test negative offsets
        self.assertEqual(DateRange(start=self.date, range_type="q").offset(-5),
                         RelativeDateRange('qa', offset=-5).fix(self.date))

        self.assertEqual('QuarterAhead(offset=-4)',
                         str(RelativeDateRange('qa', offset=-4)))

    def test_year_ahead(self):

        # test zero offsets
        self.assertEqual(DateRange(start=self.date, range_type="y"),
                         RelativeDateRange('ya', offset=0).fix(self.date))

        # test positive offsets
        self.assertEqual(DateRange(start=self.date, range_type="y").offset(1),
                         RelativeDateRange('ya').fix(self.date))

        # test negative offsets
        self.assertEqual(DateRange(start=self.date, range_type="y").offset(-5),
                         RelativeDateRange('ya', offset=-5).fix(self.date))

        self.assertEqual('YearAhead(offset=-4)',
                         str(RelativeDateRange('ya', offset=-4)))

    def test_gasyear_ahead(self):

        # test zero offsets
        self.assertEqual(DateRange(start=self.date, range_type="gy"),
                         RelativeDateRange('gya', offset=0).fix(self.date))

        # test positive offsets
        self.assertEqual(DateRange(start=self.date, range_type="gy").offset(1),
                         RelativeDateRange('gya').fix(self.date))

        # test negative offsets
        self.assertEqual(DateRange(start=self.date, range_type="gy").offset(-5),
                         RelativeDateRange('gya', offset=-5).fix(self.date))

        self.assertEqual('GasYearAhead(offset=-4)',
                         str(RelativeDateRange('gya', offset=-4)))

    def test_balmo(self):
        expected = DateRange(self.date, dt.date(2012, 9, 30))
        self.assertEqual(expected,
                         RelativeDateRange('balmo', offset=1110).fix(self.date))

        self.assertEqual('BalanceOfMonth(offset=-4)',
                         str(RelativeDateRange('balmo', offset=-4)))

    def test_season_ahead(self):

        # test zero offsets
        self.assertEqual(DateRange(start=self.date, range_type="sum"),
                         RelativeDateRange('sa', offset=0).fix(self.date))

        # test positive offsets
        self.assertEqual(DateRange(start=self.date, range_type="sum").offset(7),
                         RelativeDateRange('sa', 7).fix(self.date))

        # test negative offsets
        self.assertEqual(DateRange(start=self.date, range_type="sum").offset(-5),
                         RelativeDateRange('sa', -5).fix(self.date))

        self.assertEqual('SeasonAhead(offset=-4)',
                         str(RelativeDateRange('sa', offset=-4)))

    def test_summer_ahead(self):

        # test zero offsets
        self.assertEqual(DateRange(start=self.date, range_type="sum"),
                         RelativeDateRange('suma', offset=0).fix(self.date))
        new_date = dt.date(1978, 12, 25)
        with self.assertRaises(ValueError):
            RelativeDateRange('suma', 0).fix(new_date)

        # test positive offsets
        self.assertEqual(DateRange(start=self.date, range_type="sum").offset(8),
                         RelativeDateRange('suma', 4).fix(self.date))
        self.assertEqual(DateRange(start=new_date, range_type="win").offset(3),
                         RelativeDateRange('suma', 2).fix(new_date))

        # test negative offsets
        self.assertEqual(DateRange(start=self.date, range_type="sum").offset(-6),
                         RelativeDateRange('suma', -3).fix(self.date))
        self.assertEqual(DateRange(start=new_date, range_type="win").offset(-5),
                         RelativeDateRange('suma', -3).fix(new_date))

        self.assertEqual('SummerAhead(offset=-4)',
                         str(RelativeDateRange('suma', offset=-4)))

    def test_winter_ahead(self):

        # test zero offsets
        new_date = dt.date(1978, 12, 25)
        self.assertEqual(DateRange(start=new_date, range_type="win"),
                         RelativeDateRange('wina', offset=0).fix(new_date))
        with self.assertRaises(ValueError):
            RelativeDateRange('wina', 0).fix(self.date)

        # test positive offsets
        self.assertEqual(DateRange(start=self.date, range_type="sum").offset(7),
                         RelativeDateRange('wina', 4).fix(self.date))
        self.assertEqual(DateRange(start=new_date, range_type="win").offset(4),
                         RelativeDateRange('wina', 2).fix(new_date))

        # test negative offsets
        self.assertEqual(DateRange(start=self.date, range_type="sum").offset(-5),
                         RelativeDateRange('wina', -3).fix(self.date))
        self.assertEqual(DateRange(start=new_date, range_type="win").offset(-6),
                         RelativeDateRange('wina', -3).fix(new_date))

        self.assertEqual('WinterAhead(offset=-4)',
                         str(RelativeDateRange('wina', offset=-4)))

    def test_december_ahead(self):

        new_date = dt.date(2012, 12, 25)

        # test zero offsets
        self.assertEqual(DateRange(start=new_date, range_type='m'),
                         RelativeDateRange('deca', 0).fix(new_date))
        with self.assertRaises(ValueError):
            RelativeDateRange('deca', 0).fix(self.date)

        # test positive offsets
        self.assertEqual(DateRange(start=new_date, range_type='m').offset(24),
                         RelativeDateRange('deca', 3).fix(self.date))
        self.assertEqual(DateRange(start=new_date, range_type='m').offset(36),
                         RelativeDateRange('deca', 3).fix(new_date))

        # test negative offsets
        self.assertEqual(DateRange(start=new_date, range_type='m').offset(-12),
                         RelativeDateRange('deca', -1).fix(self.date))
        self.assertEqual(DateRange(start=new_date, range_type='m').offset(-12),
                         RelativeDateRange('deca', -1).fix(new_date))
 