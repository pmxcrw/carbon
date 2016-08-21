from core.time_period.time_utilities import SECONDS_PER_DAY
from core.quantity.quantity import DAY
from core.forward_curves.abstract_forward_curve import AbstractContinuousForwardCurve
from core.forward_curves.shape_ratio import ShapeAlgorithm
from core.forward_curves.quotes import MissingPriceError, ContinuousQuotes
from core.forward_curves.fx_rates_forward_curves import DiscountCurve, ForeignDiscountCurve
from core.forward_curves.daily_shape_calibration import AbstractDailyShapeCalibration
from core.forward_curves.intraday_shape_calibration import BaseIntradayShapeCalibration

import numpy as np


class CommodityForwardCurve(AbstractContinuousForwardCurve):
    """
    Generic class for Commodity Forward curves.
    """

    def __init__(self, quotes, discount_curve, daily_shape_calibration=None, intraday_shape_calibration=None):
        """
        :param quotes: a Quotes object
        :param discount_curve: a DiscountCurve object
        :param daily_shape_calibration: a DailyShapeCalibration object
        :param intraday_shape_calibration: an IntradayShapeCalibraiton object
        """
        assert isinstance(quotes, ContinuousQuotes)
        assert isinstance(discount_curve, (DiscountCurve, ForeignDiscountCurve))
        assert discount_curve.currency.equivalent(quotes.unit.numerator)
        if daily_shape_calibration:
            assert isinstance(daily_shape_calibration, AbstractDailyShapeCalibration)
        if intraday_shape_calibration:
            assert isinstance(intraday_shape_calibration, BaseIntradayShapeCalibration)
        self._discount_curve = discount_curve
        self._shape = ShapeAlgorithm(daily_shape_calibration, intraday_shape_calibration)
        self._settlement_rule = quotes.settlement_rule
        self.unit = quotes.unit
        super().__init__(quotes)

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
                intersecting_duration = 0 * DAY
                for atomic_period in disjoint_time_period:
                    if atomic_period.intersects(quoted_time_period):
                        intersecting_duration += atomic_period.discounted_duration(self._settlement_rule,
                                                                                   self._discount_curve)
                matrix_row.append(intersecting_duration / quoted_duration)
            matrix.append(matrix_row)
        return np.array(matrix)

    def _new_price(self, required_time_period):
        known_time_period_sets = set(partition for partition in self._time_period_partition_set
                                     if partition.intersects(required_time_period))
        total_price = 0
        total_time = 0 * DAY
        for known_time_period_set in known_time_period_sets:
            intersecting_time_period_set = known_time_period_set.intersection(required_time_period)
            time = self._discounted_duration_of_time_set(intersecting_time_period_set)
            if time > 0:
                unshaped_price = self._prices[known_time_period_set]
                shape_ratio = self._shape.shape_ratio(intersecting_time_period_set, known_time_period_set)
                price = unshaped_price * shape_ratio
                total_price += price * time
                total_time += time

        # check whether the known time periods (for which we have prices) cover the required time period
        # allow a SECOND of difference given that we're dealing with floats
        required_duration = required_time_period.discounted_duration(self._settlement_rule, self._discount_curve)
        difference = abs(total_time - required_duration)
        if difference > 1 / SECONDS_PER_DAY * DAY:
            msg = "can't calulate price for time period: {}".format(required_time_period)
            msg += " the forward curve doesn't span sufficient range (out by {})".format(difference)
            raise MissingPriceError(msg)

        try:
            return total_price / total_time * self.unit
        except Exception:
            raise MissingPriceError("Couldn't calculate price (null delivery?): {}".format(str(required_time_period)))

    def _discounted_duration_of_time_set(self, time_period_set):
        return sum(time_period.discounted_duration(self._settlement_rule, self._discount_curve)
                   for time_period in time_period_set)
