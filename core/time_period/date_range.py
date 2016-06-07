# TODO: improve docstrings

import datetime as dt
import math
import pandas as pd
from core.time_period.date_utilities import workdays, START_OF_WORLD, END_OF_WORLD


class DateRange(object):
    """
    Class to represent a range of dates.
    Closed under operations of intersection
    """

    def __init__(self, start, end=None, range_type=None):
        """
        Valid ways of generating a DateRange object are:
            1) provide a valid start and end datetime.date object
            2) provide a valid datetime.date object and a non-default
               RangeType object
            3) provide a string which can be parsed
        """
        if isinstance(start, dt.date):
            if isinstance(end, dt.date):
                # this is case 1
                if start <= end:
                    self.start = start
                    self.end = end
                else:
                    self.start = dt.date.max - dt.timedelta(365)
                    self.end = dt.date.min
                if range_type:
                    msg = "start={} and end={} both given ".format(start, end)
                    msg += "so range type cannot be defined: "
                    msg += "range_type={} given".format(range_type)
                    raise TypeError(msg)
            elif range_type:
                # this is case 2
                range_type = range_type.lower().strip()
                for known_range_type in RangeType.__subclasses__():
                    if range_type in known_range_type.aliases:
                        self.start, self.end = known_range_type.bound(start)
                        self._cache_interval = known_range_type
                        break
                else:
                    msg = "range type unknown, should be a member of the"
                    msg += " alias set for a subclass of RangeType object"
                    raise ValueError(msg)
            else:
                msg = "if a start date is given then either an end date or "
                msg += " range_type must be given"
                raise TypeError(msg)
        elif isinstance(start, str):
            if end or range_type:
                msg = "if a string input provided, no other arguments "
                msg += "can be given"
                raise TypeError(msg)
            else:
                # this is case 3
                start = start.lower().strip()
                for known_range_type in RangeType.__subclasses__():
                    try:
                        self.start, self.end = known_range_type.parse(start)
                        break
                    except ValueError:
                        pass
                else:
                    msg = "unable to parse {} into DateRange".format(start)
                    raise ValueError(msg)

    @property
    def range_type(self):
        """
        Finds the range_type from self.start and self.end, assuming
        it wasn't already given in the __init__
        """
        try:
            return self._cache_interval
        except AttributeError:
            for known_range_type in RangeType.__subclasses__():
                if known_range_type.validate(self.start, self.end):
                    self._cache_interval = known_range_type
                    return self._cache_interval
            else:
                self._cache_interval = RangeType
                return self._cache_interval

    def offset(self, shift=1):
        """
        Returns a new DateRange where start and end have been shifted.
        The RangeType object determines the shift size; e.g. a DateRange
        that has a MonthType will shift by 'shift' number of months
        """
        start, end = self.range_type.shifted(self.start, shift)
        return DateRange(start, end)

    def __repr__(self):
        return "DateRange(start={}, end={})".format(self.start, self.end)

    def __str__(self):
        return self.range_type.str(self.start, self.end)

    def __len__(self):
        """Returns the number of days in self"""
        if self.start <= self.end:
            return (self.end - self.start).days + 1
        return 0

    def __contains__(self, lhs):
        if isinstance(lhs, dt.date):
            return self.start <= lhs <= self.end
        elif isinstance(lhs, DateRange):
            return self.start <= lhs.start and lhs.end <= self.end

    def __eq__(self, rhs):
        # avoid equating with a LoadShapedDateRange
        eq = self.__class__ == rhs.__class__
        eq &= self.start == rhs.start
        eq &= self.end == rhs.end
        return eq

    def __ne__(self, rhs):
        return not self == rhs

    def __hash__(self):
        return hash((self.start, self.end))

    def __iter__(self):
        current = self.start
        while current <= self.end:
            yield current
            current += dt.timedelta(1)

    def intersection(self, other):
        start = max(self.start, other.start)
        end = min(self.end, other.end)
        return DateRange(start, end)

    def intersects(self, other):
        return self.start <= other.end and other.start <= self.end

    def difference(self, other):
        """
        Returns a pair of DateRange objects. The first is all days in
        self which are before other. The second is all days in self
        which are after other
        """
        diff = []
        if self.start < other.start:
            diff.append(DateRange(self.start, other.start - dt.timedelta(1)))
        else:
            diff.append(DateRange("never"))
        if other.end < self.end:
            diff.append(DateRange(other.end + dt.timedelta(1), self.end))
        else:
            diff.append(DateRange("never"))
        return tuple(diff)

    @property
    def weekday_and_weekend_duration(self):
        """Returns the number of weekdays and weekend days"""
        weekend_count = len(self)
        if weekend_count:
            weekday_count = workdays(self.start, self.end)
            weekend_count -= weekday_count
            return weekday_count, weekend_count
        else:
            return 0, 0

    def split_by_range_type(self, range_type):
        try:
            start_range = range_type.date_range(self.start)
        except ValueError:
            # only reason for excepting is if the range_type can't contain
            # the date self.start - which is only the case for SummerType
            # and WinterType. In this case we want to switch types.
            if range_type == SummerType:
                start_range = WinterType.date_range(self.start)
            elif range_type == WinterType:
                start_range = SummerType.date_range(self.start)
            else:
                raise ValueError("range_type is unknown")
        try:
            end_range = range_type.date_range(self.end)
        except ValueError:
            # only reason for excepting is if the range_type can't contain
            # the date self.start - which is only the case for SummerType
            # and WinterType. In this case we want to switch types.
            if range_type == SummerType:
                end_range = WinterType.date_range(self.end)
            elif range_type == WinterType:
                end_range = SummerType.date_range(self.end)
            else:
                raise ValueError("range_type is unknown")
        output = [self.intersection(start_range)]
        start_range = start_range.offset(1)
        while start_range.start < end_range.start:
            output.append(start_range)
            start_range = start_range.offset(1)
        output.append(self.intersection(end_range))
        return output

    @property
    def split_by_quarter(self):
        return self.split_by_range_type(QuarterType)

    @property
    def split_by_month(self):
        return self.split_by_range_type(MonthType)


class RangeType(object):

    @staticmethod
    def validate(start, end):
        raise NotImplementedError

    @staticmethod
    def bound(date):
        raise NotImplementedError

    @staticmethod
    def parse(date):
        raise NotImplementedError

    @staticmethod
    def str(start, end):
        return "DateRange({} to {})".format(start, end)

    @staticmethod
    def date_range(start):
        raise NotImplementedError

    @staticmethod
    def shifted(date_range, offset):
        raise NotImplementedError


class NeverType(RangeType):

    aliases = {"never", "nat", "na"}

    @staticmethod
    def validate(start, end):
        return start == END_OF_WORLD and end == START_OF_WORLD

    @staticmethod
    def parse(string):
        if string in NeverType.aliases:
            return END_OF_WORLD, START_OF_WORLD
        else:
            msg = "cannot parse '{}' as NeverType: Expected one of {}"\
                    .format(string, NeverType.aliases)
            raise ValueError(msg)

    @staticmethod
    def str(start, end):
        return "Never"

    @staticmethod
    def bound(date):
        raise NotImplementedError

    @staticmethod
    def date_range(start):
        raise NotImplementedError

    @staticmethod
    def shifted(date_range, offset):
        raise NotImplementedError


class AlwaysType(RangeType):

    aliases = {"always", "forever"}

    @staticmethod
    def validate(start, end):
        return start == START_OF_WORLD and end == END_OF_WORLD

    @staticmethod
    def parse(string):
        if string in AlwaysType.aliases:
            return START_OF_WORLD, END_OF_WORLD
        else:
            msg = "cannot parse '{}' as AlwaysType: Expected one of {}"\
                    .format(string, NeverType.aliases)
            raise ValueError(msg)

    @staticmethod
    def str(start, end):
        return "Always"

    @staticmethod
    def bound(date):
        raise NotImplementedError

    @staticmethod
    def date_range(start):
        raise NotImplementedError

    @staticmethod
    def shifted(date_range, offset):
        raise NotImplementedError


class DayType(RangeType):

    aliases = {"day", "d"}

    @staticmethod
    def validate(start, end):
        return start == end

    @staticmethod
    def bound(date):
        return date, date

    @staticmethod
    def parse(date):
        except_msg = "date cannot be parsed, expected 'YYYY-MM-DD' or similar"
        if len(date) > 7 and date.count('-') != 1:
            try:
                date = pd.Timestamp(date).date()
            except:
                raise ValueError(except_msg)
            return DayType.bound(date)
        raise ValueError(except_msg)

    @staticmethod
    def date_range(date):
        start, end = DayType.bound(date)
        return DateRange(start, end)

    @staticmethod
    def shifted(date_range, shift=1):
        return DayType.bound(date_range + dt.timedelta(shift))

    @staticmethod
    def str(start, end):
        return "{}".format(start)


class WeekType(RangeType):

    aliases = {"week", "wk", "w"}

    @staticmethod
    def validate(start, end):
        week = pd.Period(start, 'W')
        return start == week.start_time.date() and end == week.end_time.date()

    @staticmethod
    def bound(date):
        week = pd.Period(date, 'W')
        return week.start_time.date(), week.end_time.date()

    @staticmethod
    def parse(date):
        exception_msg = "date cannot be parsed, expected 'YYYY-WX' or similar"
        try:
            date = date.split('-')
            date.sort()
            if len(date[0]) == 4 and date[1][0] == "w":
                year = int(date[0])
                week = int(date[1][1:])
            else:
                raise ValueError(exception_msg)
            year, week = WeekType._roll(year, week)
        except:
            raise ValueError(exception_msg)
        return WeekType._calc_start_and_end(year, week)

    @staticmethod
    def _roll(year, week):
        while week < 0:
            year -= 1
            week += WeekType._max_weeks_in_year(year)
        while week > WeekType._max_weeks_in_year(year):
            week -= WeekType._max_weeks_in_year(year)
            year += 1
        return year, week

    @staticmethod
    def _calc_start_and_end(year, week):
        # by ISO convention, the first week of the year contains the first
        # thursday of the year, so always contains the 4th of January
        first_week_contains = dt.date(year, 1, 4)
        start_wk1 = pd.Period(first_week_contains, 'W').start_time.date()
        start = start_wk1 + dt.timedelta((week - 1) * 7)
        end = start + dt.timedelta(6)
        return start, end

    @staticmethod
    def _max_weeks_in_year(year):
        _, end_week53 = WeekType._calc_start_and_end(year, 53)
        start_week1, _ = WeekType._calc_start_and_end(year + 1, 1)
        if end_week53 < start_week1:
            return 53
        else:
            return 52

    @staticmethod
    def _get_year_and_week(date):
        year = date.year
        first_day_of_year = dt.date(year, 1, 4)
        start_wk1 = pd.Period(first_day_of_year, 'W').start_time.date()
        intervening_days = (date - start_wk1).days
        intervening_week = intervening_days // 7 + 1
        if intervening_week:
            return WeekType._roll(year, intervening_week)
        else:
            year -= 1
            week = WeekType._max_weeks_in_year(year)
            return year, week

    @staticmethod
    def date_range(date):
        start, end = WeekType.bound(date)
        return DateRange(start, end)

    @staticmethod
    def shifted(date_range, shift=1):
        year, week = WeekType._get_year_and_week(date_range)
        week += shift
        year, week = WeekType._roll(year, week)
        start, end = WeekType._calc_start_and_end(year, week)
        return start, end

    @staticmethod
    def str(start, end):
        year, week = WeekType._get_year_and_week(start)
        return "{}-W{}".format(year, week)


class MonthType(RangeType):

    aliases = {"month", "mth", "m"}

    @staticmethod
    def validate(start, end):
        m = pd.Period(start, 'M')
        return start == m.start_time.date() and end == m.end_time.date()

    @staticmethod
    def bound(date):
        month = pd.Period(date, 'M')
        return month.start_time.date(), month.end_time.date()

    @staticmethod
    def parse(date):
        exception_msg = "date cannot be parsed, expected 'YYYY-MX' or similar"
        try:
            date = date.split('-')
            date.sort()
            if len(date[0]) == 4 and date[1][0] == "m":
                year = int(date[0])
                month = int(date[1][1:])
            else:
                raise ValueError(exception_msg)
            month = pd.Period(dt.date(year, month, 1), 'M')
        except:
            raise ValueError(exception_msg)
        return month.start_time.date(), month.end_time.date()

    @staticmethod
    def date_range(date):
        start, end = MonthType.bound(date)
        return DateRange(start, end)

    @staticmethod
    def shifted(date_range, shift=1):
        y = date_range.year
        m = date_range.month + shift
        year_shift = math.ceil(m / 12) - 1
        y += year_shift
        m -= year_shift * 12
        return MonthType.bound(dt.date(y, m, 1))

    @staticmethod
    def str(start, end):
        return "{}-M{}".format(start.year, start.month)


class QuarterType(RangeType):

    aliases = {"quarter", "qtr", "q"}

    @staticmethod
    def validate(start, end):
        q = pd.Period(start, 'Q')
        return start == q.start_time.date() and end == q.end_time.date()

    @staticmethod
    def bound(date):
        quarter = pd.Period(date, 'Q')
        return quarter.start_time.date(), quarter.end_time.date()

    @staticmethod
    def parse(date):
        exception_msg = "date cannot be parsed, expected 'YYYY-QX' or similar"
        try:
            date = date.split('-')
            date.sort()
            if len(date[0]) == 4 and date[1][0] == "q":
                year = int(date[0])
                quarter = int(date[1][1:])
            else:
                raise ValueError(exception_msg)
            quarter = pd.Period(dt.date(year, quarter * 3, 1), 'Q')
        except:
            raise ValueError(exception_msg)
        return quarter.start_time.date(), quarter.end_time.date()

    @staticmethod
    def date_range(date):
        start, end = QuarterType.bound(date)
        return DateRange(start, end)

    @staticmethod
    def shifted(date_range, shift=1):
        y = date_range.year
        q = math.ceil(date_range.month / 3) + shift
        year_shift = math.ceil(q / 4) - 1
        y += year_shift
        q -= year_shift * 4
        return QuarterType.bound(dt.date(y, 3 * q, 1))

    @staticmethod
    def str(start, end):
        return "{}-Q{}".format(start.year, math.ceil(start.month / 3))


class SummerType(RangeType):

    aliases = {"summer", "sum"}

    @staticmethod
    def validate(start, end):
        year = start.year
        return start == dt.date(year, 4, 1) and end == dt.date(year, 9, 30)

    @staticmethod
    def bound(date):
        year = date.year
        month = date.month
        if month < 4 or month > 9:
            raise ValueError("date is not in Summer")
        return dt.date(year, 4, 1), dt.date(year, 9, 30)

    @staticmethod
    def parse(date):
        exception_msg = "date cannot be parsed, expected 'YYYY-SUM' or similar"
        try:
            date = date.split('-')
            date.sort()
            if len(date[0]) == 4 and date[1] == "sum":
                year = int(date[0])
            else:
                raise ValueError(exception_msg)
        except:
            raise ValueError(exception_msg)
        return dt.date(year, 4, 1), dt.date(year, 9, 30)

    @staticmethod
    def date_range(date):
        try:
            start, end = SummerType.bound(date)
            return DateRange(start, end)
        except:
            raise ValueError("date is not in Summer")

    @staticmethod
    def shifted(date_range, shift=1):
        y = date_range.year
        year_shift = shift // 2
        if shift % 2 != 0:
            return WinterType.bound(dt.date(y + year_shift, 10, 1))
        else:
            return SummerType.bound(dt.date(y + year_shift, 4, 1))

    @staticmethod
    def str(start, end):
        return "{}-SUM".format(start.year)


class WinterType(RangeType):

    aliases = {"winter", "win"}

    @staticmethod
    def validate(start, end):
        year = start.year
        valid_end = dt.date(year + 1, 4, 1) - dt.timedelta(1)
        return start == dt.date(year, 10, 1) and end == valid_end

    @staticmethod
    def bound(date):
        year = date.year
        month = date.month
        if month < 4:
            end = dt.date(year, 4, 1) - dt.timedelta(1)
            return dt.date(year-1, 10, 1), end
        elif month > 9:
            end = dt.date(year+1, 4, 1) - dt.timedelta(1)
            return dt.date(year, 10, 1), end
        else:
            raise ValueError("date is not in Winter")

    @staticmethod
    def parse(date):
        exception_msg = "date cannot be parsed, expected 'YYYY-WIN' or similar"
        try:
            date = date.split('-')
            date.sort()
            if len(date[0]) == 4 and date[1] == "win":
                year = int(date[0])
            else:
                raise ValueError(exception_msg)
        except:
            raise ValueError(exception_msg)
        end = dt.date(year+1, 4, 1) - dt.timedelta(1)
        return dt.date(year, 10, 1), end

    @staticmethod
    def date_range(date):
        try:
            start, end = WinterType.bound(date)
            return DateRange(start, end)
        except:
            raise ValueError("date is not in Winter")

    @staticmethod
    def shifted(date_range, shift=1):
        y = date_range.year
        year_shift = math.ceil(shift / 2)
        if shift % 2 != 0:
            return SummerType.bound(dt.date(y + year_shift, 4, 1))
        else:
            return WinterType.bound(dt.date(y + year_shift, 10, 1))

    @staticmethod
    def str(start, end):
        return "{}-WIN".format(start.year)


class YearType(RangeType):

    aliases = {"year", "yr", "y"}

    @staticmethod
    def validate(start, end):
        year = start.year
        return start == dt.date(year, 1, 1) and end == dt.date(year, 12, 31)

    @staticmethod
    def bound(date):
        year = date.year
        return dt.date(year, 1, 1), dt.date(year, 12, 31)

    @staticmethod
    def parse(date):
        exception_msg = "date cannot be parsed, expected 'YYYY' or similar"
        try:
            if len(date) == 4:
                year = int(date)
            else:
                raise ValueError(exception_msg)
        except:
            raise ValueError(exception_msg)
        return dt.date(year, 1, 1), dt.date(year, 12, 31)

    @staticmethod
    def date_range(date):
        start, end = YearType.bound(date)
        return DateRange(start, end)

    @staticmethod
    def shifted(date_range, shift=1):
        y = date_range.year + shift
        try:
            return YearType.bound(dt.date(y, 1, 1))
        except:
            raise ValueError("shift size out of bounds")

    @staticmethod
    def str(start, end):
        return "{}".format(start.year)


class GasYearType(RangeType):

    aliases = {"gasyear", "gas year", "gas_year", "gy"}

    @staticmethod
    def validate(start, end):
        year = start.year
        return start == dt.date(year, 10, 1) and end == dt.date(year+1, 9, 30)

    @staticmethod
    def bound(date):
        year = date.year
        month = date.month
        if month > 9:
            return dt.date(year, 10, 1), dt.date(year+1, 9, 30)
        if month < 10:
            return dt.date(year-1, 10, 1), dt.date(year, 9, 30)

    @staticmethod
    def parse(date):
        exception_msg = "date cannot be parsed, expected 'GY-YYYY' or similar"
        try:
            date = date.split("-")
            date.sort()
            if len(date[0]) == 4 and date[1] == "gy":
                year = int(date[0])
            else:
                raise ValueError(exception_msg)
        except:
            raise ValueError(exception_msg)
        return dt.date(year, 10, 1), dt.date(year+1, 9, 30)

    @staticmethod
    def date_range(date):
        start, end = GasYearType.bound(date)
        return DateRange(start, end)

    @staticmethod
    def shifted(date_range, shift=1):
        y = date_range.year + shift
        try:
            return GasYearType.bound(dt.date(y, 10, 1))
        except:
            raise ValueError("shift size out of bounds")

    @staticmethod
    def str(start, end):
        return "GY-{}".format(start.year)


# helper function for use in other modules
def date_ranges(dates):
    """
    Builds a sequence of DateRanges that spans the
    input (sorted) list of dates
    """
    return [DateRange(start, end - dt.timedelta(1))
            for start, end in zip(dates[:-1], dates[1:])]


# precompute NEVER_DATE_RANGE for use in other modules efficiently
NEVER_DR = DateRange(END_OF_WORLD, START_OF_WORLD)
