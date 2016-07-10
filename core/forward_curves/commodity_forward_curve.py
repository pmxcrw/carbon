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

    def __init__(self, quotes, discount_curve, shape_algorithm):
        if not quotes:
            raise MissingPriceError("Error when trying to construct forward curve: empty quotes")
        super().__init__(quotes.unit)
        self._discount_curve = discount_curve
        self._shape_algorithm = shape_algorithm
        self._settlement_rule = quotes.settlement_rule
        self._prices = self._generate_disjoint_prices(quotes)
        self._calc_price_cache = {}

    def _generate_disjoint_prices(self, quotes):
        quoted_time_periods = sorted(quotes.time_period_set, key=str)
        disjoint_time_periods = sorted(quotes.time_period_set.partition, key=str)
        quoted_values = np.array([quotes[time_period] for time_period in quoted_time_periods])
        matrix = self._transform_time_periods(quoted_time_periods, disjoint_time_periods)
        disjoint_prices = np.linalg.solve(matrix, quoted_values)
        return dict(zip(disjoint_time_periods, disjoint_prices))

    def _transform_time_periods(self, quoted_time_periods, disjoint_time_periods):
        """Builds an NxN square matrix where:
                M_{i,j} = (duration of disjoint_time_period[j] intersecting quoted_time_period[i]) /
                                (duration of quoted_time_period[i])
        """
        matrix = []
        for quoted_time_period in quoted_time_periods:
            quoted_duration = quoted_time_period.discounted_duration(self._settlement_rule, self._discount_curve)
            matrix_row = []
            for disjoint_time_period in disjoint_time_periods:
                intersecting_duration = 0
                for atomic_period in disjoint_time_period:
                    if atomic_period.intersects(quoted_time_period):
                        intersecting_duration += atomic_period.discounted_duration(self._settlement_rule,
                                                                                   self._discount_curve)
                matrix_row.append(intersecting_duration / quoted_duration)
            matrix.append(matrix_row)
        return np.array(matrix)

    def price(self, time_period, intraday_shape_algorithm=None):
        if time_period not in self._calc_price_cache:
            self._calc_price_cache[time_period] = self._calculate_price(time_period, intraday_shape_algorithm)
        return self._calc_price_cache[time_period] * self.unit

    def _calculate_price(self, required_time_period, intraday_shape_algorithm):
        known_time_periods = self.