from core.quantity.quantity import Quantity, DAY, standardise, DIMENSIONLESS, GBP, PENCE, UnitError
from core.time_period.time_period_sets import TimePeriodSet, DateRange
from core.time_period.date_range import LoadShapedDateRange

import numpy as np
import datetime as dt


class Quotes(object):

    @staticmethod
    def test_for_quantities(quotes_dict):
        quantity_flags = set(isinstance(quote, Quantity) for quote in quotes_dict.values())
        if len(quantity_flags) > 1:
            raise UnitError("quotes are ambiguous: contain a mix of Quantities and numbers")
        else:
            return quantity_flags.pop()

    @staticmethod
    def parse_quantities(quotes_dict, unit):
        try:
            quotes = standardise(quotes_dict, unit)
            if unit:
                unit = unit
            else:
                unit = set(quantity.unit for quantity in quotes.values()).pop()
            quotes = {key: float(value.value) for key, value in quotes.items()}
            return unit, quotes
        except UnitError as err:
            raise UnitError("quotes have incompatible units")

class ContinuousQuotes(Quotes):
    """
    Generic dictionary of quotes for continuous delivery periods, from which a forward curve can be built
    """

    def __init__(self, quotes_dict, unit=None, settlement_rule=None):
        """
        Parses input quotes_dict:
            If the quotes_dict doesn't have quantities then it expects a unit to be specified separately.
            If the quotes_dict contains quantities then:
                It tests for compatibility of the units. If mixed but compatible units are specified it converts
                everything to the base unit.
                If a unit is specified separately, it converts values to this unit;
                assuming it's compatible with given units.

        :param quotes_dict: a dictionary who's keys are DateRange or LoadShapedDateRange objects and who's values are
                            int, float or Quantity objects
        :param unit: a Unit, if required
        """
        try:
            self.time_period_set = TimePeriodSet(quotes_dict.keys())
        except ValueError:
            raise ValueError("keys for quotes must be homogeneous DateRange or LoadShapedDateRange objects")
        if Quotes.test_for_quantities(quotes_dict):
            self.unit, self.quotes = Quotes.parse_quantities(quotes_dict, unit)
        elif not unit:
            raise ValueError("quotes have no units, and no unit is provided")
        else:
            self.unit = unit
            self.quotes = quotes_dict

    def __eq__(self, other):
        eq = self.time_period_set == other.time_period_set
        eq &= self.unit == other.unit
        eq &= self.quotes == other.quotes
        return eq