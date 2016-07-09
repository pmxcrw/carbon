from abc import ABCMeta, abstractmethod


class AbstractForwardCurve(metaclass=ABCMeta):
    """
    Abstract class to define a forward curve
    """

    def __init__(self, unit):
        self.unit = unit

    @abstractmethod
    def price(self, delivery_period):
        """
        Calculate the price of the requested delivery period

        :param delivery_period: The delivery period for the price being requested.
        :return: Quantity object with the calculated price.
        """

    def shift(self, shift_time_period, shift_factor):
        """
        Multiplicative shift on the forward curve time period.

        :param shift_time_period: the time period to be shifted
        :param shift_factor: the multiplicative factor for the shift, e.g. 0.99 / 1.01 for down / up shift
        :return: New ShiftedForwardCurve
        """


class ShiftedForwardCurve(AbstractForwardCurve):
    """
    Applies a multiplicative shift to a forward curve. Uses Decorator pattern.
    """

    def __init__(self, input_curve, shift_time_period, shift_factor):
        super().__init__(input_curve.unit)
        self.input_curve = input_curve
        self.shift_time_period = shift_time_period
        self.shift_factor = shift_factor

    def price(self, delivery_period):
        input_price = self.input_curve.price(delivery_period)
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
                    difference_duration = self.price(difference)
                    if difference_duration:
                        value += self.price(difference) * difference_duration
                        duration += difference_duration
                assert duration > 0
                return value / duration
        # case 3
        else:
            return input_price


class MissingPriceError(Exception):
    """raised when there is a quote missing that's needed to builds a forward curve"""
