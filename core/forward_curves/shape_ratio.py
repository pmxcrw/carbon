from core.time_period.date_range import LoadShapedDateRange, DateRange
from core.time_period.time_utilities import SECONDS_PER_DAY
from core.time_period.load_shape import BASE
from core.forward_curves.abstract_forward_curve import AbstractContinuousForwardCurve, AbstractForwardCurve
from core.quantity.quantity import DAY
from core.forward_curves.quotes import MissingPriceError

import numpy as np
import datetime as dt


class ShapeAlgorithm(object):
    """
    Contains all of the information to shape one forward curve, and a method to calculate the shape_ratio to apply
    given a pair of time_periods as numerator and denominator
    """

    def __init__(self, daily_shape_calibration=None, intraday_shape_calibration=None):
        """
        :param daily_shape_calibration: a dict of DailyShapeCalibration objects, keyed by the releavnt LoadShape object.
        :param intraday_shape_calibration: a BaseIntradayShapeCalibration object (or sub-class)
        """
        self.daily_shape_calibration = daily_shape_calibration
        self.intraday_shape_calibration = intraday_shape_calibration
        self._cache_shape_ratio_curves = {}

    def shape_ratio(self, numerator, denominator):
        """
        Determines the ratio of the price of the numerator time period set to the price of the denominator
        time period set,

        :param numerator: TimePeriodSet representing the sub-period we are trying to price
        :param denominator: TimePeriodSet representing the period we already know how to price
        :return: the ratio of the two prices.
        """
        shape_ratio_curve = self._shape_ratio_curve(denominator)
        numerator_price = self.price_time_period_set(shape_ratio_curve, numerator)
        denominator_price = self.price_time_period_set(shape_ratio_curve, denominator)
        return numerator_price / denominator_price

    def _shape_ratio_curve(self, time_period_set):
        """
        A shape ratio curve is the equivalent forward curve that we'd get if all of the commodity prices were 1.

        :param time_period_set: TimePeriodSet that we want the curve to cover
        :return: shape ratio curve
        """
        if time_period_set not in self._cache_shape_ratio_curves:
            if self.daily_shape_calibration:
                shape_ratio_curve = self.daily_shape_calibration.shape_ratio_curve(time_period_set)
            else:
                shape_ratio_curve = UnshapedDailyRatioCurve()
            if self.intraday_shape_calibration:
                shape_ratio_curve = self.intraday_shape_calibration.decorate(shape_ratio_curve)
            self._cache_shape_ratio_curves[time_period_set] = shape_ratio_curve
        return self._cache_shape_ratio_curves[time_period_set]

    @staticmethod
    def price_time_period_set(shape_ratio_curve, time_period_set):
        value = 0
        time = 0
        for time_period in time_period_set:
            duration = time_period.duration
            value += shape_ratio_curve.price(time_period) * duration
            time += duration
        return value / time


class UnshapedDailyRatioCurve(AbstractForwardCurve):

    def _new_price(self, time_period):
        return 1


class IntradayShapeRatioCurve(AbstractForwardCurve):
    """
    Class which applies intraday_shape_calibration to an initial curve. Uses the Decorator pattern.
    """

    def __init__(self, input_curve, intraday_shape_calibration):
        """
        :param input_curve: a ShapeRatioCurve object
        :param intraday_shape_calibration: an IntraDayShapeCalibration object
        """
        super().__init__()
        self.input_curve = input_curve
        self.intraday_shape_calibration = intraday_shape_calibration

    def _new_price(self, time_period):
        """
        decorates the input_curve's price function, to overlay hourly shaping if the time_period if relevant

        :param time_period: the input dt.date, DateRange or LoadShapedDateRange object
        :return: the price with hourly shaping applied
        """
        assert time_period.duration > 0, time_period
        return time_period.weighted_average_duration(self._daily_price)

    def _hourly_price(self, hour_time_period):
        denominator_period, ratio = self.intraday_shape_calibration.extract_shape_ratio(hour_time_period)
        return ratio * self.input_curve.price(denominator_period)

    def _daily_price(self, day):
        # extract the date, using start method for DateRange or LoadShapedDateRange, else the dt.date itself
        date = getattr(day, 'start', day)
        if isinstance(day, (dt.date, DateRange)):
            load_shape = BASE
        else:
            load_shape = day.load_shape
        # calculate a list of hourly LoadShapedDateRanges by iterating through all of the hours in the load shape
        # associated with the input day (using the LoadShape objects __iter__)
        hour_time_periods = [LoadShapedDateRange(date, hour) for hour in load_shape]
        hour_time_periods = [hour_tp for hour_tp in hour_time_periods if hour_tp.duration > 0]
        hour_prices = [self._hourly_price(hour_time_period) for hour_time_period in hour_time_periods]
        return sum(hour_prices) / len(hour_prices)


class DailyShapeRatioCurve(AbstractContinuousForwardCurve):

    """
    A DailyShapeRatioCurve is the equivalent curve we'd get for a daily shaped commodity forward, if all the
    input quotes had a price of 1.
    """

    def _transform_time_periods(self, quoted_time_periods, disjoint_time_periods):
        """Builds an NxN square matrix where:
                M_{i,j} = (duration of disjoint_time_period[j] intersecting quoted_time_period[i]) /
                                (duration of quoted_time_period[i])
        """
        matrix = []
        for quoted_time_period in quoted_time_periods:
            quoted_duration = quoted_time_period.duration
            matrix_row = []
            for disjoint_time_period in disjoint_time_periods:
                intersecting_duration = 0 * DAY
                for atomic_period in disjoint_time_period:
                    if atomic_period.intersects(quoted_time_period):
                        intersecting_duration += atomic_period.duration
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
            time = sum(time_period.duration for time_period in intersecting_time_period_set)
            if time > 0:
                total_price += self._prices[known_time_period_set] * time
                total_time += time

        # check whether the known time periods (for which we have prices) cover the required time period
        # allow a SECOND of difference given that we're dealing with floats
        required_duration = required_time_period.duration
        difference = abs(total_time - required_duration)
        if difference > 1 / SECONDS_PER_DAY * DAY:
            msg = "can't calulate price for time period: {}".format(required_time_period)
            msg += " the forward curve doesn't span sufficient range (out by {})".format(difference)
            raise MissingPriceError(msg)

        try:
            return total_price / total_time
        except Exception:
            raise MissingPriceError("Couldn't calculate price (null delivery?): {}".format(str(required_time_period)))
