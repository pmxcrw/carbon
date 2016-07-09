from core.time_period.time_utilities import SECONDS_PER_DAY
from core.quantity.quantity import DAY, unique_unit, DIMENSIONLESS
from core.forward_curves.abstract_forward_curve import AbstractForwardCurve, MissingPriceError
from core.time_period.time_period_sets import TimePeriodSet
from core.time_period.date_range import LoadShapedDateRange

import numpy as np


class CommodityForwardCurve(AbstractForwardCurve):
    """
    Generic class for Commodity Forward curves.
    """

    def __init__(self, quotes):
        if not quotes:
            raise MissingPriceError("Error when trying to construct forward curve: empty quotes")
        super().__init__(quotes.unit)
        disjoint_time_periods = self.quotes.time_period_set.partition
        matrix = self._disjoint_to_quoted_periods(self.quotes.time_period, disjoint_time_periods)
        disjoint_prices = self._linear_solution(matrix, self.quotes.quotes)

