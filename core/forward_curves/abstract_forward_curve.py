from abc import ABCMeta, abstractmethod

import numpy as np


class AbstractForwardCurve(object, metaclass=ABCMeta):

    @abstractmethod
    def price(self, delivery_period):
        """
        Calculate the price of the requested delivery period

        :param delivery_period: The delivery period for the price being requested.
        :return: Quantity object with the calculated price.
        """


class AbstractContinuousForwardCurve(AbstractForwardCurve, metaclass=ABCMeta):

    """An abstract class for curves that may have overlapping quotes. Provides common methods for resolving the
    quotes into non-overlapping data"""

    def __init__(self, quotes):
        super().__init__()
        if not quotes:
            raise MissingPriceError("Error when trying to construct forward curve: empty quotes")
        self._time_period_partition_set = quotes.time_period_set.parition
        self._prices = self._generate_disjoint_prices(quotes)
        self._calc_price_cache = {}

    def _generate_disjoint_prices(self, quotes):
        """
        Transforms the input dictionary, which may contain overlapping quotes, into an equivalent dictionary with
        non-overlapping quotes (respecting non-arb rules).

        :param quotes: the input Dictionary of potentially overlapping quotes
        :return: a new Dictionary of non-overlapping quotes.
        """
        quoted_time_periods = sorted(quotes.time_period_set, key=str)
        disjoint_time_periods = sorted(self._time_period_partition_set, key=str)
        quoted_values = np.array([quotes[time_period] for time_period in quoted_time_periods])
        transformation_matrix = self._transform_time_periods(quoted_time_periods, disjoint_time_periods)
        disjoint_prices = np.linalg.solve(transformation_matrix, quoted_values)
        return dict(zip(disjoint_time_periods, disjoint_prices))

    @abstractmethod
    def _transform_time_periods(self, quoted_time_periods, disjoint_time_periods):
        """Provided by concrete sub-classes, e.g. because CommodityForwardCurve needs settlement rules and
        discount curve to do this transformation, whereas DailyShapeRatioCurve doesn't"""


class AbstractForwardPriceCurve(AbstractForwardCurve, metaclass=ABCMeta):
    """
    Abstract class to define a forward price curve
    """

    def __init__(self, quotes):
        super().__init__()
        self.unit = quotes.unit

    def shift(self, shift_time_period, shift_factor):
        """
        Multiplicative shift on the forward curve time period.

        :param shift_time_period: the time period to be shifted
        :param shift_factor: the multiplicative factor for the shift, e.g. 0.99 / 1.01 for down / up shift
        :return: New ShiftedForwardCurve
        """
        return ShiftedForwardPriceCurve(self, shift_time_period, shift_factor)


class ShiftedForwardPriceCurve(AbstractForwardPriceCurve):
    """
    Applies a multiplicative shift to a forward curve. Uses Decorator pattern.
    """

    def __init__(self, input_curve, shift_time_period, shift_factor):
        super().__init__(input_curve.unit)
        self.input_curve = input_curve
        self.shift_time_period = shift_time_period
        self.shift_factor = shift_factor

    def price(self, delivery_period):
        input_price = self.input_curve.price_time_period_set(delivery_period)
        # 3 cases:
        #   1) shift_time_period contains delivery_period -> transform the price
        #   2) shift_time_period intersects but does not contain delivery_period -> compute the partition and
        #      transform the price within the relevant part of the partition.
        #   3) shift_time_period does not intersect time_period -> do not transform the price.
        if self.shift_time_period.intersects(delivery_period):
            # case 1
            if delivery_period in self.shift_time_period:
                return self.shift_factor * input_price
            # case 2
            else:
                intersection = self.shift_time_period.intersection(delivery_period)
                differences = delivery_period.difference(self.shift_time_period)
                duration = intersection.duration
                # first get the intersection price, which contains the shift and time weight.
                value = self.price(intersection) * duration
                # now get the unshifted prices, for all of the other parts of delivery_period, and time weight them too.
                for difference in differences:
                    difference_duration = difference.duration
                    if difference_duration:
                        value += self.price(difference) * difference_duration
                        duration += difference_duration
                assert duration > 0
                return value / duration
        # case 3
        else:
            return input_price


class AbstractContinuousForwardPriceCurve(AbstractContinuousForwardCurve, AbstractForwardPriceCurve, metaclass=ABCMeta):
    """
    Abstract class to define a forward price curve
    """

    def __init__(self, quotes):
        super().__init__(quotes)
        self.unit = quotes.unit

    def shift(self, shift_time_period, shift_factor):
        """
        Multiplicative shift on the forward curve time period.

        :param shift_time_period: the time period to be shifted
        :param shift_factor: the multiplicative factor for the shift, e.g. 0.99 / 1.01 for down / up shift
        :return: New ShiftedForwardCurve
        """
        return ShiftedForwardPriceCurve(self, shift_time_period, shift_factor)


class MissingPriceError(Exception):
    """raised when there is a quote missing that's needed to builds a forward curve"""
