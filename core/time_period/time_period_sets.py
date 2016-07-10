# TODO: create promoting operations for union and intersects and intersection. These would be static methods that
# TODO: promote TimePeriodSets with LoadShapeType, or DateRangeType (or individual LoadShape or DateRange objects)
# TODO: into a TimePeriodSet with LoadShapedDateRangeType (or individual LoadShapedDateRange) and then call the existing
# TODO: union, intersect and intersection operations.

from core.time_period.date_range import DateRange, LoadShapedDateRange
from core.time_period.load_shape import LoadShape, BASE

import datetime as dt


class TimePeriodSet(frozenset):

    def __new__(cls, collection, time_period_type=None, default_load_shape=None):
        if len(collection) == 0:
            time_period_set = super().__new__(cls, collection)
            time_period_set.default_load_shape = None
            time_period_set.time_period_type = None
            time_period_set._partition_cache = None
            return time_period_set
        elif time_period_type is None:
            for candidate_type in _TimePeriodType.__subclasses__():
                if all(type(item) == candidate_type.time_period_class for item in collection):
                    if candidate_type == _LoadShapedDateRangeType:
                        load_shapes = set(lsdr.load_shape for lsdr in collection)
                        if len(load_shapes) == 1:
                            default_load_shape = load_shapes.pop()
                    time_period_type = candidate_type
                    time_period_set = super().__new__(cls, collection)
                    time_period_set.time_period_type = time_period_type
                    time_period_set.default_load_shape = default_load_shape
                    time_period_set._partition_cache = {}
                    return time_period_set
            else:
                msg = "time_period_type not provided, and collection isn't all of the same"
                msg += " known time period"
                raise ValueError(msg)
        else:
            if isinstance(default_load_shape, str):
                default_load_shape = LoadShape(default_load_shape)
            if isinstance(time_period_type, str):
                time_period_type = time_period_type.lower().strip()
                for candidate_type in _TimePeriodType.__subclasses__():
                    if time_period_type in candidate_type.aliases:
                        time_period_type = candidate_type
                        break
                else:
                    raise ValueError("cannot parse time_period_type")
            elif isinstance(time_period_type, type):
                if time_period_type not in _TimePeriodType.__subclasses__():
                    for candidate_type in _TimePeriodType.__subclasses__():
                        if candidate_type.time_period_class == time_period_type:
                            time_period_type = candidate_type
                            break
                    else:
                        raise TypeError("time_period_type unknown")
            else:
                raise ValueError("cannot parse time_period_type")
            parsed_collection = time_period_type.parse(collection, default_load_shape)
            time_period_set = super().__new__(cls, parsed_collection)
            time_period_set.time_period_type = time_period_type
            time_period_set.default_load_shape = default_load_shape
            time_period_set._partition_cache = None
            return time_period_set

    def __hash__(self):
        return hash(frozenset(item for item in self)) * hash((self.time_period_type, self.default_load_shape))

    def __eq__(self, other):
        eq = type(self) == type(other)
        eq &= len(self) == len(other)
        eq &= self.default_load_shape == other.default_load_shape
        eq &= self.time_period_type == other.time_period_type
        if not eq:
            # return false if we already know that's true, to save time having to work through loops below
            return False
        eq &= all(s in other for s in self)
        eq &= all(e in self for e in other)
        return eq

    def __ne__(self, other):
        return not self == other

    def union(self, other):
        time_period_type = self.time_period_type
        default_load_shape = self.default_load_shape
        if isinstance(other, TimePeriodSet):
            if time_period_type != other.time_period_type:
                raise TypeError("cannot join TimePeriodSet objects if they have different time_period_type")
            if self.default_load_shape != other.default_load_shape:
                default_load_shape = None
        return TimePeriodSet(super(TimePeriodSet, self).union(other), time_period_type, default_load_shape)

    def intersects(self, other):
        if isinstance(other, (LoadShapedDateRange, DateRange, LoadShape)):
            return any(item.intersects(other) for item in self)
        elif type(other) == TimePeriodSet:
            return any(item.intersects(other_item) for item in self for other_item in other)

    def intersection(self, other):
        # promotion_dict is used to find the correct time_period_type for the intersection
        promotion_dict = {frozenset({LoadShape, LoadShape}): _LoadShapeType,
                          frozenset({LoadShape, DateRange}): _LoadShapedDateRangeType,
                          frozenset({LoadShape, LoadShapedDateRange}): _LoadShapedDateRangeType,
                          frozenset({DateRange, DateRange}): _DateRangeType,
                          frozenset({DateRange, LoadShapedDateRange}): _LoadShapedDateRangeType,
                          frozenset({LoadShapedDateRange, LoadShapedDateRange}): _LoadShapedDateRangeType}
        if isinstance(other, (DateRange, LoadShape, LoadShapedDateRange)):
            collection = [item.intersection(other) for item in self if item.intersects(other)]
            time_period_type = promotion_dict[frozenset({self.time_period_type.time_period_class, type(other)})]
            return TimePeriodSet(collection, time_period_type, self.default_load_shape)
        elif isinstance(other, TimePeriodSet):
            collection = [item.intersection(other_item) for item in self for other_item in other
                          if item.intersects(other_item)]
            lhs_time_period_class = self.time_period_type.time_period_class
            rhs_time_period_class = other.time_period_type.time_period_class
            time_period_type = promotion_dict[frozenset({lhs_time_period_class, rhs_time_period_class})]
            return TimePeriodSet(collection, time_period_type, self.default_load_shape)
        else:
            raise TypeError("intersection only implemented for homogeneous time period types")

    @property
    def partition(self):
        if not self._partition_cache:
            if self.time_period_type:
                self._partition_cache = self.time_period_type.partition(self)
            else:
                raise TypeError("partition not defined for empty TimePeriodSet")
        return self._partition_cache

    def partition_intersecting(self, other):
        """Given a time period (date range etc.) to cover, returns the set of equivalence classes of the TimePeriodSet
        which intersect this time period. The time period must be homogenous with the items in TimePeriodSet

        This is used e.g. when calculating a forward price. Ther partitions are the keys for known non-intersecting
        prices. So partition_intersecting lets us find all of the relevant known prices which provide information
        relevant to the requested forward price."""
        return set(partition for partition in self.partition if partition.intersects(other))


class _TimePeriodType(object):

    aliases = set()
    tiem_period_class = ""

    @staticmethod
    def parse(collection, default_load_shape):
        raise NotImplementedError

    @staticmethod
    def partition(time_period_set):
        raise NotImplementedError


class _LoadShapeType(_TimePeriodType):

    aliases = {'load_shape', 'LoadShape', 'ls', 'load shape'}
    time_period_class = LoadShape

    @staticmethod
    def parse(collection, default_load_shape):
        if not default_load_shape:
            parsed_collection = set()
            for item in collection:
                if isinstance(item, str):
                    item = LoadShape(item)
                if isinstance(item, LoadShape):
                    parsed_collection.add(item)
                else:
                    msg = "Collection can only contain LoadShape objects, or strings that can be parsed into them"
                    raise ValueError(msg)
            return parsed_collection
        else:
            msg = "default_load_shape cannot be given unless parsing into a collection of LoadShapedDateRanges"
            raise TypeError(msg)

    @staticmethod
    def partition(time_period_set):
        """Returns the minimal set of disjoint load shapes such that every element
        of load_shape_set is a union of disjoint load shapes.

        The partition is the set of equivalence classes of the equivalence
        relationship:

            if a and b are two bits from the LoadShape bitmap
            a == b iff they intersect the same members of load_shape_set
        excluding the equivalence class which doesn't intersect any elements
        of load_shape_set"""
        equiv_classes = {}
        # here the atomic units we need to build are bitmaps with a single hour set
        for i in range(48):
            # create the bitmap for the single bit load shape
            single_bit_ls = LoadShape(2 ** i)
            # find the subset of load_shape_set which intersects with
            # the single bit load shape
            intersecting_load_shape_set = frozenset(ls for ls in time_period_set
                                                    if ls.intersects(single_bit_ls))
            # append the single_bit_load_shape into a dictionary keyed by the
            # subset. This dict stores the equivalence classes
            if intersecting_load_shape_set != frozenset({}):
                if intersecting_load_shape_set not in equiv_classes:
                    equiv_classes[intersecting_load_shape_set] = single_bit_ls.bitmap
                else:
                    equiv_classes[intersecting_load_shape_set] |= single_bit_ls.bitmap
        # form the set of LoadShape objects initialised by the bitmaps
        partition_set = set(LoadShape(bmap) for bmap in equiv_classes.values())
        return partition_set


class _DateRangeType(_TimePeriodType):

    aliases = {'date_range', 'DateRange', 'dr', 'date range'}
    time_period_class = DateRange

    @staticmethod
    def parse(collection, default_load_shape):
        if not default_load_shape:
            parsed_collection = set()
            for item in collection:
                if isinstance(item, str):
                    item = DateRange(item)
                elif isinstance(item, dt.date):
                    item = DateRange(item, item)
                if isinstance(item, DateRange):
                    parsed_collection.add(item)
                else:
                    msg = "Collection can only contain DateRange objects, or strings that can be parsed into them"
                    raise ValueError(msg)
            return parsed_collection
        else:
            msg = "default_load_shape cannot be given unless parsing into a collection of LoadShapedDateRanges"
            raise TypeError(msg)

    @staticmethod
    def partition(time_period_set):
        """Takes an iterable collection of DateRange objects and forms a
        partition using the equivalence relationship:

        Let drs(d) be the subset of DateRangeSet s.t. drs contains all the DateRange
        objects which include date d.

        Then d1 == d2 iff drs(d1) == drs(d2)

        Example: if DateRangeSet = {'2013-M2', '2013-Q1'} then
            DateRangeSet.partition = {'2013-M2', {'2013-M1', '2013-M3}}"""

        # first generate a set of atomic non overlapping DateRange objects
        starts = set(dr.start for dr in time_period_set)
        ends = set(dr.end + dt.timedelta(1) for dr in time_period_set)
        stopping_points = sorted(starts.union(ends))
        atomic_date_ranges = [DateRange(start, end - dt.timedelta(1))
                              for (start, end) in zip(stopping_points[:-1], stopping_points[1:])]

        # next loop through these atoms, working out which of the input DateRange objects within
        # the DateRangeSet include this atom.
        equivalence_classes = {}
        for atomic_date_range in atomic_date_ranges:
            intersecting_drs = frozenset(drs for drs in time_period_set if atomic_date_range.intersects(drs))
            # ignore the empty set (if the input DateRange objects have gaps in them, there will be atoms within
            # our loop which don't intersect with the initial DateRangeSet. We need to throw these away.
            if intersecting_drs != frozenset({}):
                # now work out if this atom has a new equivalence class
                if intersecting_drs not in equivalence_classes:
                    equivalence_classes[intersecting_drs] = [atomic_date_range]
                # otherwise add it to the existing equivalence class
                else:
                    equivalence_classes[intersecting_drs].append(atomic_date_range)
        # now build the partition from the values in the equivalence_class dict
        return set(TimePeriodSet(atoms, _DateRangeType) for atoms in equivalence_classes.values())


class _LoadShapedDateRangeType(_TimePeriodType):

    aliases = {'load_shaped_date_range', 'LoadShapedDateRange', 'lsdr', 'load shaped date range'}
    time_period_class = LoadShapedDateRange

    @staticmethod
    def parse(collection, default_load_shape):
        if isinstance(default_load_shape, str):
            default_load_shape = LoadShape(default_load_shape)
        parsed_collection = set()
        for item in collection:
            if isinstance(item, str):
                item = LoadShapedDateRange(item, default_load_shape)
            elif isinstance(item, dt.date):
                item = LoadShapedDateRange(DateRange(item, item), default_load_shape)
            elif isinstance(item, DateRange):
                item = LoadShapedDateRange(item, default_load_shape)
            if isinstance(item, LoadShapedDateRange):
                parsed_collection.add(item)
            else:
                msg = "Collection can only contain LoadShapedDateRange objects, or strings that can be parsed into them"
                raise ValueError(msg)
        return parsed_collection

    @staticmethod
    def partition(time_period_set):
        """
        Returns the set of LoadShapedDateRangeSet objects, each of which is the equivalence class
        of the partition.
        """
        equivalence_classes = {}
        date_range_partition = TimePeriodSet([lsdr.date_range for lsdr in time_period_set], _DateRangeType).partition
        # follows the same pattern as before but the construction of the atomic units (this time a
        # LoadShapedDateRangeSet) are more complex. First partition the DateRangeSet of all date_range_set in
        # time_period_set. Then for each equivalence class of the DateRangeSet:
        # * Find the set of load_shapes in time_period_set which are attached to a DateRange intersecting our
        #   DateRangeSet.
        # * Partition this LoadShapeSet
        # * Loop through the equivalence class of this inner partition
        # The atomic unit is then the LoadShapedDateRangeSet formed from the DateRangeSet equivalence class and the
        # LoadShapeSet equivalence class.

        for date_range_set in date_range_partition:
            promoted_date_range_set = TimePeriodSet(date_range_set, _LoadShapedDateRangeType, BASE)
            intersecting_load_shape_set = TimePeriodSet({lsdr.load_shape for lsdr in time_period_set
                                                        if promoted_date_range_set.intersects(lsdr)})
            intersecting_load_shape_partition = intersecting_load_shape_set.partition
            for load_shape in intersecting_load_shape_partition:
                promoted_date_range_set = TimePeriodSet(date_range_set, _LoadShapedDateRangeType, load_shape)
                intersecting_lsdrs = frozenset(lsdr for lsdr in time_period_set
                                               if promoted_date_range_set.intersects(lsdr))
                if intersecting_lsdrs != frozenset({}):
                    if intersecting_lsdrs not in equivalence_classes:
                        equivalence_classes[intersecting_lsdrs] = promoted_date_range_set
                    else:
                        equivalence_classes[intersecting_lsdrs] = \
                            equivalence_classes[intersecting_lsdrs].union(promoted_date_range_set)
        return set(lsdr_set for lsdr_set in equivalence_classes.values())
