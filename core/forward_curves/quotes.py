from core.quantity.quantity import Quantity, standardise, UnitError
from core.time_period.time_period_sets import TimePeriodSet
from core.time_period.date_range import DateRange, LoadShapedDateRange
from core.time_period.load_shape import BASE

import datetime as dt
import numpy as np

class AbstractQuotes(object):

    """
    Generic dictionary of quotes for building a forward curve
    """

    def __init__(self, input_dict):
        if not input_dict:
            raise MissingPriceError
        self.quotes = input_dict

    def __getitem__(self, item):
        return self.quotes[item]


class AbstractContinuousQuotes(AbstractQuotes):

    """
    Generic dictionary of quotes for continuous delivery periods, from which a forward curve can be built.
    Used (for example) when building shape ratio curves.
    """

    def __init__(self, input_dict):
        super().__init__(input_dict)
        try:
            self.time_period_set = TimePeriodSet(input_dict.keys())
        except ValueError:
            raise ValueError("keys for quotes must be homogeneous DateRange or LoadShapedDateRange objects")


class AbstractDailyQuotes(AbstractQuotes):

    """
    Generic dictionary of quotes which represent a single date, from which a forward curve can be built.
    Concrete classes (for example) are FX quotes and individual points on a Yield Curve.
    """

    def __init__(self, quotes_dict, unit=None):
        super().__init__(quotes_dict)
        self._standardise_keys
        self.dates = np.array(sorted(self.quotes))

    @property
    def _standardise_keys(self):
        """
        changes self.quotes so that the keys are forced to be ordinals
        """
        output = {}
        for date in self.quotes:
            if isinstance(date, dt.date):
                output[date.toordinal()] = self.quotes[date]
            elif isinstance(date, DateRange) and date.start == date.end:
                output[date.start.toordinal()] = self.quotes[date]
            elif isinstance(date, LoadShapedDateRange) and date.start == date.end and date.load_shape == BASE:
                output[date.start.toordinal()] = self.quotes[date]
            else:
                raise TypeError("FX quotes must be daily: {} provided".format(date))
        self.quotes = output


class PriceQuotes(AbstractQuotes):

    """
    Contains functions used for checking that quotes have valid units
    """

    @property
    def _contains_quantities(self):
        """tests whether the quantities within quotes_dict are values or numbers"""
        quantity_flags = set(isinstance(quote, Quantity) for quote in self.quotes.values())
        if len(quantity_flags) > 1:
            raise UnitError("quotes are ambiguous: contain a mix of Quantities and numbers")
        else:
            return quantity_flags.pop()

    def _parse_quantities(self, unit):
        try:
            quotes = standardise(self.quotes, unit)
            if unit:
                unit = unit
            else:
                unit = set(quantity.unit for quantity in self.quotes.values()).pop()
            quotes = {key: float(value.value) for key, value in quotes.items()}
            return unit, quotes
        except UnitError:
            raise UnitError("quotes have incompatible units")


class ContinuousQuotes(AbstractContinuousQuotes, PriceQuotes):

    """
    Generic dictionary of price quotes for continuous delivery periods, from which a forward curve can be built
    """

    def __init__(self, quotes_dict, settlement_rule, unit=None):
        """
        Parses input quotes_dict:
            If the quotes_dict doesn't have quantities then it expects a unit to be specified separately.
            If the quotes_dict contains quantities then:
                It tests for compatibility of the units. If mixed but compatible units are specified it converts
                everything to the base unit.
                If a unit is specified explicitly, it converts quantitites to this unit;
                assuming it's compatible with given units.

        :param quotes_dict: a dictionary who's keys are DateRange or LoadShapedDateRange objects and who's values are
                            int, float or Quantity objects
        :param unit: a Unit, if required
        """
        super().__init__(quotes_dict)
        self.settlement_rule = settlement_rule
        if self._contains_quantities:
            self.unit, self.quotes = self._parse_quantities(unit)
        elif not unit:
            raise ValueError("quotes have no units, and no unit is provided")
        else:
            self.unit = unit

    def __eq__(self, other):
        eq = self.time_period_set == other.time_period_set
        eq &= self.settlement_rule == other.settlement_rule
        eq &= self.unit == other.unit
        eq &= self.quotes == other.quotes
        return eq


class FxQuotes(AbstractDailyQuotes, PriceQuotes):

    def __init__(self, quotes_dict, unit=None):
        """
        Quotes represent FX rates for a given time.

        :param quotes_dict: a dict keyed by dt.Date, DateRange or LoadShapedDateRange with corresponding FX rate.
        :param unit: [optional] a Unit object.
        """
        super().__init__(quotes_dict)
        if self._contains_quantities:
            self.unit, self.quotes = self._parse_quantities(unit)
        elif not unit:
            raise ValueError("quotes have no units, and no unit is provided")
        else:
            self.unit = unit


class RatesQuotes(AbstractDailyQuotes):

    def __init__(self, quotes_dict):
        """
        Quotes represent points on a yield curve. A yield curve is a set of actuarial rates r(t, T), meaning that the
        discount factors / ZCB prices are defined as:

        B(t, T) = 1 / (1 + r(t, T)) ^ (T - t)

        :param quotes_dict: a dict keyed by dt.Date, DateRange or LoadShapedDateRange objects with corresponding yield.
        """
        super().__init__(quotes_dict)
        if not all(isinstance(value, (int, float)) for value in self.quotes.values()):
            raise TypeError("RatesQuotes can only contain numbers: {} provided"
                            .format({type(value) for value in self.quotes.values()}))
        self.rates = np.array([self.quotes[date] for date in self.dates])

    @property
    def is_null(self):
        return all(self.rates == 0)

class MissingPriceError(Exception):
    """raised when there is a quote missing that's needed to build a forward curve"""