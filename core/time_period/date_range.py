# TODO: improve docstrings
# TODO: see if there's a better place structurally to keep NEVER_DR, ALWAYS_DR, NEVER_LSDR

from core.base.quantity import DAY
from core.time_period.load_shape import LoadShape, BASE
from core.time_period.time_utilities import workdays
from inputs.static_data.time_constants import END_OF_WORLD, START_OF_WORLD

import datetime as dt
import math
import pandas as pd
from abc import abstractmethod, abstractproperty, abstractstaticmethod


class AbstractDateRange(object):

    """
    A DateRange is a time period with various methods specialised to Commodities (e.g. load-shape)
    """

    @abstractproperty
    def intersection(self, other):
        """return a new concrete subclass of AbstractDateRange comprising the intersection with other.
        Other can be a LoadShape object or a concrete subclass of AbstractDateRange."""

    @abstractproperty
    def intersects(self, other):
        """return true if self intersects other. Other can be a LoadShape object or a concrete subclass of
        AbstractDateRange."""

    @abstractproperty
    def difference(self, other):
        """
        Returns a pair of DateRange objects or LSDR's. The first is all days in self which are before other.
        The second is all days in self which are after other
        """

    @abstractproperty
    def duration(self):
        """calculates the duration of the date range"""

    def discounted_duration(self, settlement_rule, discount_curve):
        """
        Calculates the discounted duration of a time period, given a settlement rule and a discount curve.
        Used e.g. for curve construction.

        :param settlement_rule: a concrete subclass of AbstractSettlementRule object.
        :param discount_curve: a DiscountCurve or ForwardDiscountCurve object
        :return: the discounted duration of the time period
        """
        return settlement_rule(self).discounted_duration(discount_curve)

    def settlement_dates(self, settlement_rule):
        """
        Calculates the settlement dates associated with a date range

        :param settlement_rule: a concrete subclass of AbstractSettlementRule object.
        :return: a dict of settlement dates keyed by parts of the time_period
        """
        return settlement_rule(self).settlement_dates

    def weighted_average_duration(self, function):
        """
        Calculates the weighted average duration using a given function

        :param function: an input function, that can date a dt.date object as an input
        :return: the weighted average duration.
        """
        return sum(function(d) * d.duration for d in self) / self.duration

    @abstractmethod
    def split_by_range_type(self, range_type):
        """splits the date range into components each having the desired range_type"""

    @abstractproperty
    def split_by_month(self):
        """convenience property - like split_by_range_type method where range_type is monthly."""

    @abstractproperty
    def split_by_quarter(self):
        """convenience property - like split_by_range_type method where range_type is quarterly."""

    @abstractmethod
    def offset(self, shift=1):
        """offsets a date_range (e.g. a monthly date range is shifted to the next month)"""

    @abstractmethod
    def within(self, other):
        """returns True if self is contained within the "other" date range"""


class DateRange(AbstractDateRange):
    """
    Class to represent a range of dates. Closed under operations of intersection
    """

    def __init__(self, start, end=None, range_type=None):
        """
        Valid ways of generating a DateRange object are:
            1) provide a valid start and end datetime.date object
            2) provide a valid datetime.date object and a non-default RangeType object or string that can be parsed
            3) provide a string which can be parsed
        """
        if isinstance(start, dt.date):
            if isinstance(end, dt.date):
                if range_type:
                    raise TypeError("inputs overspecified: start, end and range_type all specified")
                # this is case 1
                self.start, self.end = self._check_start_and_end(start, end)
                self._cache_interval = {}
            elif range_type:
                # this is case 2
                range_type = self._parse_range_type(range_type)
                self.start, self.end = range_type.bound(start)
                self._cache_interval = range_type
            elif not end:
                self.start = start
                self.end = start
                self._cache_interval = _DayType
            else:
                raise TypeError("if a start date is given then either an end date or  range_type must be given")
        elif isinstance(start, str):
            if end or range_type:
                raise TypeError("if a string input provided, no other arguments can be given")
            # this is case 3
            start = start.lower().strip()
            for known_range_type in _RangeType.__subclasses__():
                try:
                    self.start, self.end = known_range_type.parse(start)
                    self._cache_interval = known_range_type
                    break
                except ValueError:
                    pass
            else:
                raise ValueError("unable to parse {} into DateRange".format(start))

    @staticmethod
    def _check_start_and_end(start, end):
        if start <= end:
            return start, end
        # the DateRange is empty, so we specify a single unique "NEVER"
        return END_OF_WORLD, START_OF_WORLD

    @staticmethod
    def _parse_range_type(range_type):
        if range_type in _RangeType.__subclasses__():
            return range_type
        if isinstance(range_type, str):
            range_type = range_type.lower().strip()
            for known_range_type in _RangeType.__subclasses__():
                if range_type in known_range_type.aliases:
                    return known_range_type
        raise ValueError("range_type {} is unknown. Should be a subclass/alias of _RangeType".format(range_type))

    @property
    def _range_type(self):
        """
        Finds the range_type from self.start and self.end, assuming it wasn't already given in the __init__
        """
        if not self._cache_interval:
            for known_range_type in _RangeType.__subclasses__():
                if known_range_type.validate(self.start, self.end):
                    self._cache_interval = known_range_type
                    break
            else:
                self._cache_interval = _RangeType
        return self._cache_interval

    def offset(self, shift=1):
        """
        Returns a new DateRange where start and end have been shifted. The RangeType object determines the shift size;
        e.g. a DateRange that has a MonthType will offset by 'shift' number of months

        :param shift: the number of _RangeType date-ranges to shift by
        :return: DateRange object
        """
        start, end = self._range_type.shifted(self.start, shift)
        return DateRange(start, end)

    def __repr__(self):
        return "DateRange(start={}, end={})".format(self.start, self.end)

    def __str__(self):
        return self._range_type.str(self.start, self.end)

    def __len__(self):
        """Returns the number of days in self"""
        if self.start <= self.end:
            return (self.end - self.start).days + 1
        return 0

    def __contains__(self, lhs):
        if isinstance(lhs, dt.date):
            return self.start <= lhs <= self.end
        if isinstance(lhs, (DateRange, LoadShapedDateRange)):
            return self.start <= lhs.start and lhs.end <= self.end
        return False

    def within(self, other):
        """
        Returns True if self is contained within the "other" date range
        """
        if isinstance(other, (DateRange, LoadShapedDateRange)):
            return self in other
        elif isinstance(other, LoadShape):
            return other == BASE

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
        """
        Loops through the DateRange, returning individual DateRange objects of 1 day's duration.
        """
        current = self.start
        while current <= self.end:
            yield DateRange(current)
            current += dt.timedelta(1)

    def intersection(self, other):
        if isinstance(other, LoadShape):
            return LoadShapedDateRange(self, other)
        if isinstance(other, DateRange):
            start = max(self.start, other.start)
            end = min(self.end, other.end)
            return DateRange(start, end)
        if isinstance(other, LoadShapedDateRange):
            return other.intersection(self)
        raise TypeError("can only calculate intersection with another time_period")

    def intersects(self, other):
        if isinstance(other, LoadShape):
            return True
        return self.start <= other.end and other.start <= self.end

    def difference(self, other):
        """
        Returns a pair of DateRange objects or LSDR's. The first is all days in self which are before other.
        The second is all days in self which are after other
        """
        if isinstance(other, LoadShapedDateRange):
            return LoadShapedDateRange(self, BASE).difference(other)
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
    def duration(self):
        """Returns the number of days in self"""
        if self.start <= self.end:
            return ((self.end - self.start).days + 1) * DAY
        return 0 * DAY

    @property
    def weekday_and_weekend_duration(self):
        """Returns the number of weekdays and weekend days"""
        weekend_count = len(self)
        if weekend_count:
            weekday_count = workdays(self.start, self.end)
            weekend_count -= weekday_count
            return weekday_count, weekend_count
        return 0, 0

    def split_by_range_type(self, range_type):
        """
        Generates a list of new DateRange objects which splits self into the given range_type. The start and end may be
        "short" periods.

        :param range_type: a concerete subclass of _RangeType or an alias string of such a subclass.
        :return: list of DateRange objects
        """
        range_type = DateRange._parse_range_type(range_type)
        start_range = self._expand_date_to_range(self.start, range_type)
        end_range = self._expand_date_to_range(self.end, range_type)
        output = [self.intersection(start_range)]
        date_range = start_range.offset(1)
        while date_range.start < end_range.start:
            output.append(date_range)
            date_range = date_range.offset(1)
        output.append(self.intersection(end_range))
        return output

    @staticmethod
    def _expand_date_to_range(date, range_type):
        """
        Convenience function for split_by_range_type. Finds the DateRange that spans the given date and has duration
        given by range_type.

        :param date: datetime.date object
        :param range_type: _RangeType or concrete subclass.
        :return: DateRange object
        """
        try:
            return range_type.date_range(date)
        except ValueError:
            # only reason for excepting is if the range_type can't contain the date self.start;
            # which is only the case for SummerType and WinterType. In this case we want to switch types.
            if range_type == _SummerType:
                return _WinterType.date_range(date)
            elif range_type == _WinterType:
                return _SummerType.date_range(date)

    @property
    def split_by_quarter(self):
        return self.split_by_range_type(_QuarterType)

    @property
    def split_by_month(self):
        return self.split_by_range_type(_MonthType)

    def expand(self, range_type):
        """Expands the DateRange to the given range_type"""
        return DateRange(self.start, range_type=range_type)


class _RangeType(object):

    @abstractstaticmethod
    def validate(start, end):
        raise NotImplementedError

    @abstractstaticmethod
    def bound(date):
        raise NotImplementedError

    @abstractstaticmethod
    def parse(date):
        raise NotImplementedError

    @abstractstaticmethod
    def str(start, end):
        return "DateRange({} to {})".format(start, end)

    @abstractstaticmethod
    def date_range(start):
        raise NotImplementedError

    @abstractstaticmethod
    def shifted(date_range, offset):
        raise NotImplementedError


class _NeverType(_RangeType):

    aliases = {"never", "nat", "na"}

    @staticmethod
    def validate(start, end):
        return start == END_OF_WORLD and end == START_OF_WORLD

    @staticmethod
    def parse(string):
        if string in _NeverType.aliases:
            return END_OF_WORLD, START_OF_WORLD
        raise ValueError("cannot parse '{}' as NeverType: Expected one of {}".format(string, _NeverType.aliases))

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


class _AlwaysType(_RangeType):

    aliases = {"always", "forever"}

    @staticmethod
    def validate(start, end):
        return start == START_OF_WORLD and end == END_OF_WORLD

    @staticmethod
    def parse(string):
        if string in _AlwaysType.aliases:
            return START_OF_WORLD, END_OF_WORLD
        raise ValueError("cannot parse '{}' as AlwaysType: Expected one of {}".format(string, _NeverType.aliases))

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


class _DayType(_RangeType):

    aliases = {"day", "d"}

    @staticmethod
    def validate(start, end):
        return start == end

    @staticmethod
    def bound(date):
        return date, date

    @staticmethod
    def parse(date):
        except_msg = "datecannot be parsed, expected 'YYYY-MM-DD' or similar: given {}".format(date)
        if len(date) < 7 or date.count('-') == 1:
            raise ValueError(except_msg)
        try:
            date = pd.Timestamp(date).date()
        except:
            raise ValueError(except_msg)
        return date, date

    @staticmethod
    def date_range(date):
        return DateRange(date)

    @staticmethod
    def shifted(date_range, shift=1):
        return _DayType.bound(date_range + dt.timedelta(shift))

    @staticmethod
    def str(start, end):
        return "{}".format(start)


class _WeekType(_RangeType):

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
            year, week = _WeekType._roll(year, week)
        except:
            raise ValueError(exception_msg)
        return _WeekType._calc_start_and_end(year, week)

    @staticmethod
    def _roll(year, week):
        while week < 0:
            year -= 1
            week += _WeekType._max_weeks_in_year(year)
        while week > _WeekType._max_weeks_in_year(year):
            week -= _WeekType._max_weeks_in_year(year)
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
        _, end_week53 = _WeekType._calc_start_and_end(year, 53)
        start_week1, _ = _WeekType._calc_start_and_end(year + 1, 1)
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
            return _WeekType._roll(year, intervening_week)
        else:
            year -= 1
            week = _WeekType._max_weeks_in_year(year)
            return year, week

    @staticmethod
    def date_range(date):
        start, end = _WeekType.bound(date)
        return DateRange(start, end)

    @staticmethod
    def shifted(date_range, shift=1):
        year, week = _WeekType._get_year_and_week(date_range)
        week += shift
        year, week = _WeekType._roll(year, week)
        start, end = _WeekType._calc_start_and_end(year, week)
        return start, end

    @staticmethod
    def str(start, end):
        year, week = _WeekType._get_year_and_week(start)
        return "{}-W{}".format(year, week)


class _MonthType(_RangeType):

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
        start, end = _MonthType.bound(date)
        return DateRange(start, end)

    @staticmethod
    def shifted(date_range, shift=1):
        y = date_range.year
        m = date_range.month + shift
        year_shift = math.ceil(m / 12) - 1
        y += year_shift
        m -= year_shift * 12
        return _MonthType.bound(dt.date(y, m, 1))

    @staticmethod
    def str(start, end):
        return "{}-M{}".format(start.year, start.month)


class _QuarterType(_RangeType):

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
        start, end = _QuarterType.bound(date)
        return DateRange(start, end)

    @staticmethod
    def shifted(date_range, shift=1):
        y = date_range.year
        q = math.ceil(date_range.month / 3) + shift
        year_shift = math.ceil(q / 4) - 1
        y += year_shift
        q -= year_shift * 4
        return _QuarterType.bound(dt.date(y, 3 * q, 1))

    @staticmethod
    def str(start, end):
        return "{}-Q{}".format(start.year, math.ceil(start.month / 3))


class _SummerType(_RangeType):

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
            start, end = _SummerType.bound(date)
            return DateRange(start, end)
        except:
            raise ValueError("date is not in Summer")

    @staticmethod
    def shifted(date_range, shift=1):
        y = date_range.year
        year_shift = shift // 2
        if shift % 2 != 0:
            return _WinterType.bound(dt.date(y + year_shift, 10, 1))
        else:
            return _SummerType.bound(dt.date(y + year_shift, 4, 1))

    @staticmethod
    def str(start, end):
        return "{}-SUM".format(start.year)


class _WinterType(_RangeType):

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
            start, end = _WinterType.bound(date)
            return DateRange(start, end)
        except:
            raise ValueError("date is not in Winter")

    @staticmethod
    def shifted(date_range, shift=1):
        y = date_range.year
        year_shift = math.ceil(shift / 2)
        if shift % 2 != 0:
            return _SummerType.bound(dt.date(y + year_shift, 4, 1))
        else:
            return _WinterType.bound(dt.date(y + year_shift, 10, 1))

    @staticmethod
    def str(start, end):
        return "{}-WIN".format(start.year)


class _YearType(_RangeType):

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
        start, end = _YearType.bound(date)
        return DateRange(start, end)

    @staticmethod
    def shifted(date_range, shift=1):
        y = date_range.year + shift
        try:
            return _YearType.bound(dt.date(y, 1, 1))
        except:
            raise ValueError("shift size out of bounds")

    @staticmethod
    def str(start, end):
        return "{}".format(start.year)


class _GasYearType(_RangeType):

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
        start, end = _GasYearType.bound(date)
        return DateRange(start, end)

    @staticmethod
    def shifted(date_range, shift=1):
        y = date_range.year + shift
        try:
            return _GasYearType.bound(dt.date(y, 10, 1))
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


class LoadShapedDateRange(AbstractDateRange):

    def __init__(self, date_range, load_shape=BASE):
        if isinstance(date_range, str):
            date_range = DateRange(date_range.lower().strip())
        if isinstance(date_range, dt.date):
            date_range = DateRange(date_range, range_type='d')
        if isinstance(load_shape, str):
            load_shape = LoadShape(load_shape.lower().strip())
        if isinstance(date_range, DateRange) and\
           isinstance(load_shape, LoadShape):
            if date_range == NEVER_DR or load_shape == LoadShape(0):
                self.date_range = NEVER_DR
                self.load_shape = LoadShape(0)
            else:
                self.date_range = date_range
                self.load_shape = load_shape
        else:
            msg = "inputs must be a DateRange object and LoadShape"
            msg += " object, or strings that can be parsed into these"
            raise ValueError(msg)

    def __repr__(self):
        return "LoadShapedDateRange(date_range={}, load_shape={})"\
                .format(self.date_range, self.load_shape)

    def __eq__(self, rhs):
        if self.__class__ == rhs.__class__:
            eq = self.date_range == rhs.date_range
            eq &= self.load_shape == rhs.load_shape
            return eq
        else:
            return False

    def __hash__(self):
        return hash((self.date_range, self.load_shape))

    @property
    def start(self):
        return self.date_range.start

    @property
    def end(self):
        return self.date_range.end

    def offset(self, shift=1):
        return LoadShapedDateRange(self.date_range.offset(shift), self.load_shape)

    @property
    def duration(self):
        """returns the duration in days"""
        weekdays, weekends = self.date_range.weekday_and_weekend_duration
        duration = weekdays * self.load_shape.weekday_load_factor
        duration += weekends * self.load_shape.weekend_load_factor
        return duration * DAY

    def intersection(self, other):
        if isinstance(other, LoadShape):
            if self.load_shape.intersects(other):
                load_shape = self.load_shape.intersection(other)
                return LoadShapedDateRange(self.date_range, load_shape)
            return NEVER_LSDR
        if isinstance(other, DateRange):
            if self.date_range.intersects(other):
                date_range = self.date_range.intersection(other)
                return LoadShapedDateRange(date_range, self.load_shape)
            return NEVER_LSDR
        if self.load_shape.intersects(other.load_shape):
            if self.date_range.intersects(other.date_range):
                date_range = self.date_range.intersection(other.date_range)
                load_shape = self.load_shape.intersection(other.load_shape)
                return LoadShapedDateRange(date_range, load_shape)
        return NEVER_LSDR

    def intersects(self, other):
        if isinstance(other, LoadShape):
            return self.load_shape.intersects(other)
        if isinstance(other, DateRange):
            return self.date_range.intersects(other)
        if self.load_shape.intersects(other.load_shape):
            if self.date_range.intersects(other.date_range):
                # this is expensive to compute, so first test the basic
                # intersections and return false sooner if we can
                return self.intersection(other).duration > 0
        return False

    def equivalent(self, rhs):
        """
        Tests whether two LoadShapedDateRange objects represent the same set of hours. Computationally expensive
        """
        intersection = self.intersection(rhs)
        duration = self.duration
        if duration != intersection.duration:
            return False
        else:
            return duration == rhs.duration

    def __contains__(self, lhs):
        if isinstance(lhs, (dt.date, DateRange)):
            if lhs in self.date_range:
                return self.load_shape == BASE
        elif lhs.date_range in self.date_range:
            return lhs.load_shape in self.load_shape
        else:
            return False

    def within(self, other):
        if isinstance(other, (DateRange, LoadShapedDateRange)):
            return self in other
        elif isinstance(other, LoadShape):
            return self.load_shape in other

    def split_by_range_type(self, range_type):
        date_ranges = self.date_range.split_by_range_type(range_type)
        return [LoadShapedDateRange(dr, self.load_shape) for dr in date_ranges]

    @property
    def split_by_month(self):
        date_ranges = self.date_range.split_by_month
        return [LoadShapedDateRange(dr, self.load_shape) for dr in date_ranges]

    @property
    def split_by_quarter(self):
        date_ranges = self.date_range.split_by_quarter
        return [LoadShapedDateRange(dr, self.load_shape) for dr in date_ranges]

    def expand(self, range_type):
        """Expands the DateRange to the given range_type"""
        return LoadShapedDateRange(self.date_range.expand(range_type), self.load_shape)

    def __iter__(self):
        week_hours = self.load_shape.weekday_load_factor
        weekend_hours = self.load_shape.weekend_load_factor
        for daily_date_range in self.date_range:
            date = daily_date_range.start
            weekday = date.weekday()
            if weekday < 5 and week_hours:
                yield LoadShapedDateRange(DateRange(date, date), self.load_shape)
            elif weekday > 4 and weekend_hours:
                yield LoadShapedDateRange(DateRange(date, date), self.load_shape)

    def difference(self, other):
        """
        Returns a tripple of DateRange objects:

        1) The days in self which are before other (with self's loadshape)
        2) The days in both self and other, with load shape of self - other
        3) The days in self which are after other (with self's loadshape)
        """
        start, end = self.date_range.difference(other.date_range)
        mid = self.date_range.intersection(other.date_range)
        load_shape = self.load_shape.difference(other.load_shape)
        return (LoadShapedDateRange(start, self.load_shape),
                LoadShapedDateRange(mid, load_shape),
                LoadShapedDateRange(end, self.load_shape))

# precompute NEVER_DATE_RANGE for use in other modules efficiently
NEVER_DR = DateRange(END_OF_WORLD, START_OF_WORLD)
ALWAYS_DR = DateRange(START_OF_WORLD, END_OF_WORLD)
NEVER_LSDR = LoadShapedDateRange(NEVER_DR, LoadShape(0))
