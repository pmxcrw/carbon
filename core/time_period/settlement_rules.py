from abc import abstractproperty, abstractmethod
from core.time_period.date_range import DateRange

import datetime as dt


class AbstractSettlementRule(object):

    def __init__(self, time_period):
        self.time_period = time_period

    @abstractmethod
    def discounted_duration(self, discount_curve):
        """Computes the discounted duration of a time period"""

    @abstractproperty
    def settlement_dates(self):
        """Returns a dict of settlement dates keyed by parts of the time_period"""


class DayOfDeliverySettlementRule(AbstractSettlementRule):

    def discounted_duration(self, discount_curve):
        discounted_duration = sum(discount_curve.price(date) * date.duration for date in self.time_period)
        return discounted_duration

    @property
    def settlement_dates(self):
        return {date: date.start for date in self.time_period}


class PeriodicSettlementRule(AbstractSettlementRule):
    """
    Base class for settlement rules which happen periodically during the date range.
    """

    def __init__(self, range_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.range_type = range_type

    @property
    def settlement_dates(self):
        return {period: self._settlement_date(period)
                for period in self.time_period.split_by_range_type(self.range_type)}

    def _settlement_date(self, period):
        """Defines how to get from the individual monthly delivery period to settlement date"""

    def discounted_duration(self, discount_curve):
        duration = sum(period.duration * discount_curve.price(settlement_date)
                       for period, settlement_date in self.settlement_dates.items())
        return duration


class GasSettlementRule(PeriodicSettlementRule):
    """
    Default rule for Gas markets is that gas is settled on the 20th of the month following delivery.
    """

    def __init__(self, *args, **kwargs):
        super().__init__("month", *args, **kwargs)

    def _settlement_date(self, month):
        month_end = month.expand("month").end
        return month_end + dt.timedelta(20)


class UKPowerSettlementRule(PeriodicSettlementRule):

    def __init__(self, *args, **kwargs):
        super().__init__("month", *args, **kwargs)

    def _settlement_date(self, month):
        month_end = month.expand("month").end
        day = month_end.isoweekday()
        if day < 6:
            return month_end + dt.timedelta(14)
        if day == 6:
            return month_end + dt.timedelta(13)
        if day == 7:
            return month_end + dt.timedelta(12)


class EUASettlementRule(PeriodicSettlementRule):
    """
    Settles on the first day of the next year
    """

    def __init__(self, *args, **kwargs):
        super().__init__("year", *args, **kwargs)

    def _settlement_date(self, year):
        year_end = year.expand("year").end
        return year_end + dt.timedelta(1)
