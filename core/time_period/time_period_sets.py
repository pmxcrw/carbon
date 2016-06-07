# TODO: create an abstract base class for time period sets and lift up any commonality I can find
# TODO: create unit tests

from core.time_period.date_range import DateRange
from core.time_period.load_shape import LoadShape, BASE
from core.time_period.load_shaped_date_range import LoadShapedDateRange

import datetime as dt
import functools


class LoadShapeSet(set):
    def __init__(self, collection):
        self.load_shapes = set()
        for load_shape_candidate in collection:
            if isinstance(load_shape_candidate, LoadShape):
                self.load_shapes.add(load_shape_candidate)
            elif isinstance(load_shape_candidate, str):
                load_shape_candidate = LoadShape(load_shape_candidate)
                self.load_shapes.add(load_shape_candidate)
            else:
                msg = "Collection can only contain LoadShape objects, or strings that can be parsed into them"
                raise ValueError(msg)
        super(LoadShapeSet, self).__init__()

    def __str__(self):
        output = "LoadShapeSet({"
        for i, date_range in enumerate(self.load_shapes):
            output += repr(date_range)
            if i < len(self.load_shapes) - 1:
                output += ", "
            else:
                output += "})"
        return output

    def __repr__(self):
        return self.__str__()

    @property
    def partition(self):
        """Returns the minimal set of disjoint load shapes such that every element
        of load_shape_set is a union of disjoint load shapes.

        The partition is the set of equivalence classes of the equivalence
        relationship:

            if a and b are two bits from the LoadShape bitmap
            a == b iff they intersect the same members of load_shape_set
        excluding the equivalence class which doesn't intersect any elements
        of load_shape_set"""
        load_shapes = self.load_shapes
        equiv_classes = {}
        # here the atomic units we need to build are bitmaps with a single hour set
        for i in range(48):
            # create the bitmap for the single bit load shape
            sbls = LoadShape(2 ** i)
            # find the subset of load_shape_set which intersects with
            # the single bit load shape
            intersecting_load_shape_set = frozenset(ls for ls in load_shapes
                                                    if ls.intersects(sbls))
            # append the single_bit_load_shape into a dictionary keyed by the
            # subset. This dict stores the equivalence classes
            if intersecting_load_shape_set != frozenset([]):
                if intersecting_load_shape_set not in equiv_classes:
                    equiv_classes[intersecting_load_shape_set] = sbls.bitmap
                else:
                    equiv_classes[intersecting_load_shape_set] |= sbls.bitmap

        # form the set of LoadShape objects initialised by the bitmaps
        partition_set = set(LoadShape(bmap) for bmap in equiv_classes.values())
        return partition_set


class DateRangeSet(set):
    """A set of DateRange objects, with a partition method."""

    def __init__(self, collection):
        self.date_ranges = set()
        for candidate_date_range in collection:
            if isinstance(candidate_date_range, DateRange):
                self.date_ranges.add(candidate_date_range)
            elif isinstance(candidate_date_range, str):
                self.date_ranges.add(DateRange(candidate_date_range))
            elif isinstance(candidate_date_range, dt.date):
                self.date_ranges.add(DateRange(candidate_date_range, candidate_date_range))
            else:
                raise ValueError("collection cannot be parsed to DateRange objects")
        super(DateRangeSet, self).__init__(collection)

    def __hash__(self):
        return functools.reduce(lambda x, y: hash(x) * hash(y), self, 1)

    def __str__(self):
        output = "DateRangeSet({"
        for i, date_range in enumerate(self.date_ranges):
            output += repr(date_range)
            if i < len(self.date_ranges) - 1:
                output += ", "
            else:
                output += "})"
        return output

    def __repr__(self):
        return self.__str__()

    def add(self, other):
        if isinstance(other, DateRange):
            self.date_ranges.add(other)
        elif isinstance(other, str):
            self.date_ranges.add(DateRange(other))
        elif isinstance(other, dt.date):
            self.date_ranges.add(DateRange(other, other))
        else:
            raise ValueError("expected a DateRange object, or something that can be parsed to a DateRange object")

    def union(self, other):
        return DateRangeSet(self.date_ranges.union(other.date_ranges))

    def intersects(self, date_range):
        """Given a DateRange, returns True iff the input DateRange intersects with one or more of the
        DaterRange elements of this DateRangeSet"""
        return any(dr.intersects(date_range) for dr in self.date_ranges)

    @property
    def partition(self):
        """Takes an iterable collection of DateRange objects and forms a
        partition using the equivalence relationship:

        Let drs(d) be the subset of DateRangeSet s.t. drs contains all the DateRange
        objects which include date d.

        Then d1 == d2 iff drs(d1) == drs(d2)

        Example: if DateRangeSet = {'2013-M2', '2013-Q1'} then
            DateRangeSet.partition = {'2013-M2', {'2013-M1', '2013-M3}}"""

        # first generate a set of atomic non overlapping DateRange objects
        starts = set(dr.start for dr in self.date_ranges)
        ends = set(dr.end + dt.timedelta(1) for dr in self.date_ranges)
        stopping_points = sorted(starts.union(ends))
        atomic_date_ranges = [DateRange(start, end + dt.timedelta(-1))
                              for (start, end) in zip(stopping_points[:-1], stopping_points[1:])]

        # next loop through these atoms, working out which of the input DateRange objects within
        # the DateRangeSet include this atom.
        equivalence_classes = {}
        for atomic_date_range in atomic_date_ranges:
            intersecting_drs = frozenset(drs for drs in self.date_ranges if atomic_date_range.intersects(drs))
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
        return set(DateRangeSet(atoms) for atoms in equivalence_classes.values())

    def partition_intersecting(self, date_range_to_cover):
        """Given a DateRange to cover, returns the set of equivalence classes of the partition
        which intersects this DateRange"""
        return set(partition for partition in self.partition if partition.intersects(date_range_to_cover))


class LoadShapedDateRangeSet(set):
    def __init__(self, collection, default_load_shape=BASE):
        self.load_shaped_date_ranges = set()
        self.date_ranges = DateRangeSet({})
        for candidate_lsdr in collection:
            if isinstance(candidate_lsdr, LoadShapedDateRange):
                self.date_ranges.add(candidate_lsdr.date_range)
                self.load_shaped_date_ranges.add(candidate_lsdr)
            elif isinstance(candidate_lsdr, DateRange):
                self.date_ranges.add(candidate_lsdr)
                self.load_shaped_date_ranges.add(LoadShapedDateRange(candidate_lsdr,
                                                                     default_load_shape))
            elif isinstance(candidate_lsdr, str):
                date_range = DateRange(candidate_lsdr)
                self.date_ranges.add(date_range)
                self.load_shaped_date_ranges.add(LoadShapedDateRange(date_range,
                                                                     default_load_shape))
            elif isinstance(candidate_lsdr, dt.date):
                date_range = DateRange(candidate_lsdr, candidate_lsdr)
                self.date_ranges.add(date_range)
                self.load_shaped_date_ranges.add(LoadShapedDateRange(date_range,
                                                                     default_load_shape))
            else:
                raise ValueError("collection cannot be parsed to LoadShapedDateRange objects")
        super(LoadShapedDateRangeSet, self).__init__(collection)

    def __hash__(self):
        return functools.reduce(lambda x, y: hash(x) * hash(y), self, 1)

    def __str__(self):
        output = "LoadShapedDateRangeSet({"
        for i, lsdr in enumerate(self.load_shaped_date_ranges):
            output += repr(lsdr)
            if i < len(self.load_shaped_date_ranges) - 1:
                output += ", "
            else:
                output += "})"
        return output

    def __repr__(self):
        return self.__str__()

    def add(self, other):
        if isinstance(other, LoadShapedDateRange):
            self.load_shaped_date_ranges.add(other)
            self.date_ranges.add(other.date_range)
        elif isinstance(other, DateRange):
            other = LoadShapedDateRange(other)
            self.load_shaped_date_ranges.add(other)
            self.date_ranges.add(other.date_range)
        elif isinstance(other, str):
            other = LoadShapedDateRange(DateRange(other))
            self.load_shaped_date_ranges.add(other)
            self.date_ranges.add(other.date_range)
        elif isinstance(other, dt.date):
            other = LoadShapedDateRange(DateRange(other, other))
            self.load_shaped_date_ranges.add(other)
            self.date_ranges.add(other.date_range)
        else:
            msg = "expected a LoadShapedDateRange object, or"
            msg += "something that can be parsed to a DateRange object"
            raise ValueError(msg)

    def union(self, other):
        load_shaped_date_ranges = self.load_shaped_date_ranges.union(other.load_shaped_date_ranges)
        return LoadShapedDateRangeSet(load_shaped_date_ranges)

    def intersects(self, load_shaped_date_range):
        """Given a LoadShapedDateRange, returns True iff the input LoadShapedDateRange intersects with one or
        more of the LoadShapedDaterRange elements of this LoadShapedDateRangeSet"""
        return any(dr.intersects(load_shaped_date_range) for dr in self.load_shaped_date_ranges)

    @property
    def partition(self):
        """
        Returns the set of LoadShapedDateRangeSet objects, each of which is the equivalence class
        of the partition.
        """
        equivalence_classes = {}
        # follows the same pattern as before but the construction of the atomic units (this time a
        # LoadShapedDateRangeSet) are more complex. First partition the DateRangeSet of all date_ranges in self.
        # Then for each equivalence class of the DateRangeSet:
        # * Find the set of load_shapes in self which are attached to a DateRange intersecting our DateRangeSet.
        # * Partition this LoadShapeSet
        # * Loop through the equivalence class of this inner partition
        # The atomic unit is then the LoadShapedDateRangeSet formed from the DateRangeSet equivalence class and the
        # LoadShapeSet equivalence class.
        for date_range_set in self.date_ranges.partition:
            promoted_date_range_set = LoadShapedDateRangeSet(date_range_set)
            load_shape_set = LoadShapeSet({lsdr.load_shape for lsdr in self.load_shaped_date_ranges
                                           if promoted_date_range_set.intersects(lsdr)})
            load_shape_partition = load_shape_set.partition
            for load_shape in load_shape_partition:
                promoted_date_range_set = LoadShapedDateRangeSet(date_range_set, load_shape)
                intersecting_lsdrs = frozenset(lsdr for lsdr in self.load_shaped_date_ranges
                                               if promoted_date_range_set.intersects(lsdr))
                if intersecting_lsdrs != frozenset({}):
                    if intersecting_lsdrs not in equivalence_classes:
                        equivalence_classes[intersecting_lsdrs] = promoted_date_range_set
                    else:
                        equivalence_classes[intersecting_lsdrs] = \
                            equivalence_classes[intersecting_lsdrs].union(promoted_date_range_set)
        return set(lsdr_set for lsdr_set in equivalence_classes.values())


a = LoadShapedDateRangeSet({LoadShapedDateRange('2016', 'Base'), LoadShapedDateRange('2016-M2', 'Peak')})
print(a.partition)
b = LoadShapedDateRangeSet({LoadShapedDateRange('2017'), LoadShapedDateRange('2018')})
c = a.union(b)
print(c.partition)
