# TODO: improve doc strings

from core.time_period.date_range import DateRange, NEVER_DR
from core.time_period.load_shape import LoadShape, BASE

import datetime as dt


class LoadShapedDateRange(object):

    def __init__(self, date_range, load_shape=BASE):
        if isinstance(date_range, str):
            date_range = DateRange(date_range.lower().strip())
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

    @property
    def duration(self):
        """returns the duration in days"""
        weekdays, weekends = self.date_range.weekday_and_weekend_duration
        duration = weekdays * self.load_shape.weekday_load_factor
        duration += weekends * self.load_shape.weekend_load_factor
        return duration

    def intersection(self, other):
        if self.load_shape.intersects(other.load_shape):
            if self.date_range.intersects(other.date_range):
                date_range = self.date_range.intersection(other.date_range)
                load_shape = self.load_shape.intersection(other.load_shape)
                return LoadShapedDateRange(date_range, load_shape)
        return NEVER_LSDR

    def intersects(self, other):
        if self.load_shape.intersects(other.load_shape):
            if self.date_range.intersects(other.date_range):
                # this is expensive to compute, so first test the basic
                # intersections to see if we nest inside the cheaper
                # calculations and return false sooner if we can
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

    def __iter__(self):
        week_hours = self.load_shape.weekday_load_factor
        weekend_hours = self.load_shape.weekend_load_factor
        for d in self.date_range:
            weekday = d.weekday()
            if weekday < 5 and week_hours:
                yield LoadShapedDateRange(DateRange(d, d), self.load_shape)
            elif weekday > 4 and weekend_hours:
                yield LoadShapedDateRange(DateRange(d, d), self.load_shape)

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
        return [LoadShapedDateRange(start, self.load_shape),
                LoadShapedDateRange(mid, load_shape),
                LoadShapedDateRange(end, self.load_shape)]

NEVER_LSDR = LoadShapedDateRange(NEVER_DR, LoadShape(0))
