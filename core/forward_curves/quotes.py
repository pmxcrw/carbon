from core.quantity.quantity import Quantity, standardise, UnitError
from core.time_period.time_period_sets import TimePeriodSet


class AbstractQuotes(object):

    """
    Generic dictionary of quotes for continuous delivery periods, from which a forward curve can be built
    """

    def __init__(self, input_dict):
        if not input_dict:
            raise MissingPriceError
        self.quotes = input_dict
        try:
            self.time_period_set = TimePeriodSet(input_dict.keys())
        except ValueError:
            raise ValueError("keys for quotes must be homogeneous DateRange or LoadShapedDateRange objects")

    def __getitem__(self, item):
        return self.quotes[item]

class ContinuousQuotes(AbstractQuotes):
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

    @property
    def _contains_quantities(self):
        """tests whether the quotes_dict has quantitities as values, or numbers"""
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

    def __eq__(self, other):
        eq = self.time_period_set == other.time_period_set
        eq &= self.settlement_rule == other.settlement_rule
        eq &= self.unit == other.unit
        eq &= self.quotes == other.quotes
        return eq


class MissingPriceError(Exception):
    """raised when there is a quote missing that's needed to builds a forward curve"""