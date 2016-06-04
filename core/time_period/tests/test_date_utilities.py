from core.time_period.date_utilities import workdays
import unittest
import pandas as pd
import pandas.tseries.holiday
import datetime as dt


class TestDateUtilities(unittest.TestCase):

    def test_type_checking(self):
        try:
            start = dt.date(2000, 1, 1)
            end = dt.date(2000, 1, 16)
            whichdays = {"Mon", "Tue", "Wed", "Q1"}
            workdays(start, end, whichdays)
        except TypeError as error:
            exp_msg = "whichdays contains {}: should be a set of strings of weekday names"\
                        .format({'Q1'})
            self.assertEqual(exp_msg, error.args[0])

    def test_fulldays(self):
        start = dt.date(2000, 1, 16)
        end = dt.date(2000, 2, 1)
        whichdays = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
        test_dates = pd.date_range(start, end)
        for offset, date in enumerate(test_dates):
            self.assertEqual(offset + 1,
                             workdays(start, date.date(), whichdays))

    def test_working_week(self):
        start = dt.date(2000, 1, 1)
        end = dt.date(2000, 1, 16)
        whichdays = {"Mon", "Tue", "Wed", "Thu", "Fri"}
        test_dates = pd.date_range(start, end)
        expected_output = [0, 0, 1, 2, 3, 4, 5, 5, 5, 6, 7, 8, 9, 10, 10, 10]
        test_output = [workdays(start, date.date(), whichdays)
                       for date in test_dates]
        self.assertEqual(expected_output, test_output)

    def test_weekends(self):
        start = pd.Timestamp('2000-01-01')
        end = pd.Timestamp('2000-01-16')
        whichdays = {"Sat", "Sun"}
        test_dates = pd.date_range(start, end)
        expected_output = [1, 2, 2, 2, 2, 2, 2, 3, 4, 4, 4, 4, 4, 4, 5, 6]
        test_output = [workdays(start, date, whichdays)
                       for date in test_dates]
        self.assertEqual(expected_output, test_output)

    def test_monday(self):
        start = pd.Timestamp('2000-01-01')
        end = pd.Timestamp('2000-01-16')
        whichdays = "Mon"
        test_dates = pd.date_range(start, end)
        expected_output = [0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2]
        test_output = [workdays(start, date, whichdays)
                       for date in test_dates]
        self.assertEqual(expected_output, test_output)

    def test_mon_fri(self):
        start = pd.Timestamp('2000-01-01')
        end = pd.Timestamp('2000-01-16')
        whichdays = ["Mon", "Fri"]
        test_dates = pd.date_range(start, end)
        expected_output = [0, 0, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4]
        test_output = [workdays(start, date, whichdays)
                       for date in test_dates]
        self.assertEqual(expected_output, test_output)

    def test_hols(self):
        hol = pandas.tseries.holiday.get_calendar('USFederalHolidayCalendar')
        start = dt.date(2001, 1, 1)
        end = dt.date(2001, 1, 16)
        whichdays = {"Mon", "Tue", "Wed", "Thu", "Fri"}
        test_dates = pd.date_range(start, end)
        expected_output = [0, 1, 2, 3, 4, 4, 4, 5, 6, 7, 8, 9, 9, 9, 9, 10]
        test_output = [workdays(start, d.date(), whichdays, hol)
                       for d in test_dates]
        self.assertEqual(expected_output, test_output)

    def test_no_hols(self):
        start = dt.date(2001, 1, 1)
        end = dt.date(2001, 1, 16)
        whichdays = {"Mon", "Tue", "Wed", "Thu", "Fri"}
        test_dates = pd.date_range(start, end)
        expected_output = [1, 2, 3, 4, 5, 5, 5, 6, 7, 8, 9, 10, 10, 10, 11, 12]
        test_output = [workdays(start, date.date(), whichdays)
                       for date in test_dates]
        self.assertEqual(expected_output, test_output)
