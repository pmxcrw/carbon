from abc import abstractmethod, ABCMeta

from core.base.quantity import HOUR
from core.forward_curves.shape_ratio import IntradayShapeRatioCurve
from core.time_period.date_range import LoadShapedDateRange
from core.time_period.load_shape import WEEKDAY_OFFPEAK, PEAK, WEEKEND_OFFPEAK, WEEKEND_PEAK, DAYTIME


class BaseIntradayShapeCalibration(object, metaclass=ABCMeta):
    """base class for holding intraday shape ratio information"""

    load_shapes = []  # load shapes are supplied by the concrete sub-class.

    def decorate(self, shape_ratio_curve):
        """Takes a DailyShapeRatioCurve and returns an IntradayShapeRatioCurve that embeds the
        IntradayShapeCalibration data"""
        return IntradayShapeRatioCurve(shape_ratio_curve, self)

    @classmethod
    def _load_shape_index(cls, time_period):
        """helper method common to both concrete subclasses, tells us which loadshape block we are in"""
        i = 0
        while not time_period.intersects(cls.load_shapes[i]):
            i += 1
        return i

    @abstractmethod
    def extract_shape_ratio(self, hour_time_period):
        """
        extracts the shape ratio needed to shape the given hour_time_period using the information contained in this
        calibration object. Also returns details of the denominator period that the ratio is calibrated to.

        :param hour_time_period: a LoadShapedDateRange object that lasts a single hour
        :return: ratio of the price of the hour time period, over the denominator time period
                 and the denominator time period
        """


class PowerIntradayShapeCalibration(BaseIntradayShapeCalibration):
    """class which stores the ratios for shaping intraday power forward curves.
    Each ratio can be used to determine the price of an hour from the price of the block in which the hour resides"""

    load_shapes = [WEEKDAY_OFFPEAK, PEAK, WEEKEND_OFFPEAK, WEEKEND_PEAK]

    def __init__(self, calibration_data):
        """
        calibration data is provided as a list of list of lists, the first list has 4 elements corresponding to

        :param calibration_data: a list of list of lists of floats; 4 blocks * 12 months * 12 hours
        """
        self.ratios = calibration_data
        assert len(self.ratios) == 4, "need data for 4 loadshaptes: only {} provided".format(len(self.ratios))
        for ratios_by_month in self.ratios:
            assert len(ratios_by_month) == 12, "need data for 12 months: only {} provided".format(len(ratios_by_month))
            for ratios_by_hour in ratios_by_month:
                assert len(ratios_by_hour) == 12, "need data for 12 hours: only {} provided".format(len(ratios_by_hour))
                average = sum(ratios_by_hour) / 12
                assert 0.999999 < average < 1.000001, "ratios don't average to 1: {}".format(average)

    def decorate(self, shape_ratio_curve):
        return IntradayShapeRatioCurve(shape_ratio_curve, self)

    def extract_shape_ratio(self, hour_time_period):
        assert hour_time_period.duration == 1 * HOUR, "input time period must be a single hour"
        load_shape = self._load_shape_index(hour_time_period)
        month = self._month_index(hour_time_period)
        hour = self._hour_index(hour_time_period)
        denominator_period = LoadShapedDateRange(hour_time_period.start, self.load_shapes[load_shape])
        return denominator_period, self.ratios[load_shape][month][hour]

    @staticmethod
    def _hour_index(time_period):
        """works out the hour in a 12 hour format - so if time_period has a loadshape that's in DAYTIME, returns
        the index of the hour in DAYTIME, likewise if time_period is in NIGHTTIME"""
        hour = time_period.load_shape.hour
        if time_period.intersects(DAYTIME):
            # take off the 8 hours between midnight and the start of DAYTIME
            return hour - 8
        # hour is in NIGHTTIME
        if hour < 8:
            return hour
        else:
            # take off the 12 hours of DAYTIME
            return hour - 12

    @staticmethod
    def _month_index(time_period):
        return time_period.start.month - 1
