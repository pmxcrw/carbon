from abc import abstractmethod, ABCMeta
from core.time_period.load_shape import NEVER_LS
from core.time_period.date_range import DateRange, LoadShapedDateRange
from core.forward_curves.quotes import AbstractQuotes
from core.forward_curves.shape_ratio import DailyShapeRatioCurve


class AbstractDailyShapeCalibration(object, metaclass=ABCMeta):

    """class which contains all the ratio information used for shaping forward curves down to daily granularity"""

    def __init__(self, within_month, quarter_to_month):
        """
        :param quarter_to_month: dict keyed by LoadShape object(s),and containing list of month to quarter ratios.
        :param within_month: dict keyed by LoadShape object(s) and containing corresponding within month shape ratio.
                             e.g. if the loadshape is WEEKEND, the ratio contains the month to day ratio for weekends.
        """
        self.within_month = within_month
        self.quarter_to_month = quarter_to_month
        self.period_to_quarter = {}  # this is over-written by the concrete sub-class
        self._cached_shape_ratio_forwards = {}

    def shape_ratio_curve(self, time_period_set):
        """
        The shape_ratio_curve is the shaped forward curve that would result if the unshaped forward curve was 1
        everywhere.

        :param time_period_set: TimePeriodSet object
        :return: DailyShapeRatioCurve object
        """
        # period is the Season, Calendar Year or other date range corresponding to the concrete DailyShapeCalibration
        # class. E.g. period is a Season for the SeasonBasedDailtShapeCalibration class.
        period = self._find_period(time_period_set)
        if period not in self._cached_shape_ratio_forwards:
            relative_price_dict = self._tree(period).relative_price_dict
            self._cached_shape_ratio_forwards[period] = DailyShapeRatioCurve(relative_price_dict)
        return self._cached_shape_ratio_forwards[period]

    @abstractmethod
    def _find_period(self, time_period_set):
        """The method implemented by the concrete subclass that finds the period (e.g. Season, Calendar Year) that
        covers the input time_period_set and is of the type corresponding to the concrete DailyShapeCalibration class.
        E.g. if the concrete class is SeasonBasedDailyShapeCalibration then it find the single season that spans the
        time_period_set.
        """

    def _tree(self, period):
        """
        Creates a ShapeRatioTree object containing the calibration data for a given year and load_shape.

        :param period: LoadShapedDateRange object representing the period (from the concrete class)
        :return: ShapeRatioTree object containing the calibration data for this season and load_shape
        """
        ratios_and_subtrees = {(self.period_to_quarter[quarter.load_shape][index], self._quarter_tree(quarter))
                               for index, quarter in enumerate(period.split_by_quarter)}
        return _ShapeRatioTree(period, frozenset(ratios_and_subtrees))

    def _quarter_tree(self, quarter):
        """
        Helper function that creates a ShapeRatioTree object containing the calibration data for a given quarter and
        load_shape. Currently common to all concrete sub-classes.

        :param quarter: LoadShapedDateRange object representing the quarter
        :return: ShapeRatioTree object containing the calibration data for this quarter and load_shape
        """
        ratios_and_subtrees = {(self.quarter_to_month[month.load_shape][index], self._month_tree(month))
                               for index, month in enumerate(quarter.split_by_month)}
        return _ShapeRatioTree(quarter, frozenset(ratios_and_subtrees))

    def _month_tree(self, month):
        """
        Helper function that creates a ShapeRatioTree object containing the calibration data for a given quarter
        and load_shape. Currently common to all concrete sub-classes.

        :param month: LoadShapedDateRange object representing a month.
        :return: ShapeRatioTree object containing the calibration data for this month and load_shape.
        """
        ratio_tree_set = set()
        # Sort to ensure ordering is always the same
        for sub_load_shape in self.within_month.keys():
            sub_tree = _ShapeRatioTree(LoadShapedDateRange(month.date_range, sub_load_shape), frozenset())
            ratio_tree_set.add((self.within_month[sub_load_shape], sub_tree))
        return _ShapeRatioTree(month, frozenset(ratio_tree_set))


class SeasonBasedDailyShapeCalibration(AbstractDailyShapeCalibration):

    """
    DailyShapeCalibraiton specialisation which deals with season to quarter and quarter to month shaping
    """

    def __init__(self, season_to_quarter, quarter_to_month, within_month):
        """
        :param season_to_quarter: dict keyed by LoadShape object(s) containing a list, each element of the list being
                                  the corresponding Q1/WIN, Q2/SUM, Q3/SUM, Q4/WIN ratios
        :param quarter_to_month: dict keyed by LSDR object(s) representing the month,
                                 and containing corresponding month to quarter ratios.
        :param within_month: dict keyed by LoadShape object(s) and containing corresponding within month shape ratio.
                             e.g. if the loadshape is WEEKEND, the ratio contains the month to day ratio for weekends.
        """
        super().__init__(within_month, quarter_to_month)
        self.season_to_quarter = season_to_quarter
        self.period_to_quarter = season_to_quarter
        self.load_shapes = set(season_to_quarter.keys())
        assert self.load_shapes == set(quarter_to_month.keys())

    def _find_period(self, time_period_set):
        """Finds the season that spans the time_period_set"""
        start = min(time_period.start for time_period in time_period_set)
        end = max(time_period.end for time_period in time_period_set)
        try:
            season = DateRange(start, range_type="sum")
            self.period_to_quarter = {key: list[1:3] for key, list in self.season_to_quarter.items()}
        except ValueError:
            season = DateRange(start, range_type="win")
            self.period_to_quarter = {key: [list[0], list[3]] for key, list in self.season_to_quarter.items()}
        if end not in season:
            raise ValueError("shape information doesn't cover the period being priced")
        for available_load_shape in self.load_shapes:
            if time_period_set.within(available_load_shape):
                load_shape = available_load_shape
                break
        else:
            raise ValueError("Couldn't determine relevant load shape for time period set {} given loadshapes{}"
                             .format(str(time_period_set), str(self.load_shapes)))
        return LoadShapedDateRange(season, load_shape)


class CalendarBasedDailyShapeCalibration(AbstractDailyShapeCalibration):

    """
    DailyShapeCalibraiton specialisation which deals with season to quarter and quarter to month shaping
    """

    def __init__(self, calendar_to_quarter, quarter_to_month, within_month):
        """
        :param calendar_to_quarter: dict keyed by LSDR object(s) representing the quater,
                                    and containing corresponding year to quarter ratios.
        :param quarter_to_month: dict keyed by LSDR object(s) representing the month,
                                 and containing corresponding month to quarter ratios.
        :param within_month: dict keyed by LoadShape object(s) and containing corresponding within month shape ratio.
                             e.g. if the loadshape is WEEKEND, the ratio contains the month to day ratio for weekends.
        """
        super().__init__(within_month, quarter_to_month)
        self.period_to_quarter = calendar_to_quarter
        self.load_shapes = set(calendar_to_quarter.keys())
        assert self.load_shapes == set(quarter_to_month.keys())

    def _find_period(self, time_period_set):
        """Finds the calendar year that spans the time_period_set"""
        start = min(time_period.start for time_period in time_period_set)
        end = max(time_period.end for time_period in time_period_set)
        year = DateRange(start, range_type="year")
        if end not in year:
            raise ValueError("shape information doesn't cover the period being priced")
        for available_load_shape in self.load_shapes:
            if time_period_set.within(available_load_shape):
                load_shape = available_load_shape
                break
        else:
            raise ValueError("Couldn't determine relevant load shape for time period set {} given loadshapes{}"
                             .format(str(time_period_set), str(self.load_shapes)))
        return LoadShapedDateRange(year, load_shape)


class _ShapeRatioTree(object):

    """
    Recursive data structure used to represent how shape ratios are applied to a particular time_period. This helper
    class is intended for use with DailyShapeCalibration classes only.
    """

    def __init__(self, load_shaped_date_range, ratios_and_subtrees=frozenset()):
        """
        :param load_shaped_date_range: LoadShapedDateRange object representing the period in which we have shape info.
        :param ratios_and_subtrees: set consisting of a tuple of float and sub-trees. Each float corresponds to the
                                    shape ratio for shaping between load_shaped_date_range and the period represented
                                    by the sub-tree. If empty, then load_shaped_date_range is a leaf on the tree.
        """
        self.time_period = load_shaped_date_range
        self.ratios_and_subtrees = ratios_and_subtrees

    @property
    def relative_price_dict(self):
        """
        Produces a dictionary which can be used (like forward quotes) to construct a pseudo forward curve, which can
        then give hte relative price of any time period covered by the tree.

        :return: Quotes object which gives the relative prices of the time periods at the leaves of this ratio tree.
        """

        if not self.ratios_and_subtrees:
            return AbstractQuotes({self.time_period: 1})  # we are at a leaf node

        # create a pseudo forward curve which can be used to scale the relative price dicts of the sub-trees.
        # this means we can avoid having to have pre-normalised raios in our ratios_and_subtrees set
        immediate_relative_price_dict = {sub_tree.time_period: ratio for ratio, sub_tree in self.ratios_and_subtrees}
        shape_ratio_curve = DailyShapeRatioCurve(AbstractQuotes(immediate_relative_price_dict))
        normalisation = shape_ratio_curve.price(self.time_period)

        # now iterate through each of the sub-trees, building up our results dict
        results = {}
        for ratio, sub_tree in self.ratios_and_subtrees:
            sub_dict = sub_tree.relative_price_dict.quotes
            # normalise using the immediate_period_relative_price
            normalised_sub_dict = {sub_time_period: sub_ratio * shape_ratio_curve.price(sub_time_period) / normalisation
                                   for sub_time_period, sub_ratio in sub_dict.items()}
            results.update(normalised_sub_dict)
        return AbstractQuotes(results)
