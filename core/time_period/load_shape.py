# TODO: improve docstrings


class LoadShape(object):

    # create the dictionary for the Multiton pattern
    _instances = dict()

    def __new__(cls, bitmap, name=None):
        # Uses __new__ rather than __init__ to implement the
        # multiton pattern
        #
        # because of the use of the multiton patter, name will be ignored
        # if there's an existing LoadShape object with a different name
        try:
            return cls._instances[bitmap]
        except KeyError:
            # either we don't have this bitmap, or we're parsing a string
            if isinstance(bitmap, int):
                # we don't have this bitmap, so need to call __new__ to
                # allocate new memory, set the attributes and store in the
                # class level instances dict.
                load_shape = super(LoadShape, cls).__new__(cls)
                load_shape.name = name
                load_shape.bitmap = bitmap
                cls._instances[bitmap] = load_shape
                return load_shape
            elif isinstance(bitmap, str):
                # see if the class level instances dict already has an
                # instances with a name similar to the input string.
                bitmap = bitmap.lower().strip()
                for known_bitmap in cls._instances:
                    known_name = cls._instances[known_bitmap].name
                    if known_name:
                        if known_name.lower().strip() == bitmap:
                            bitmap = known_bitmap
                            return cls._instances[bitmap]
                else:
                    msg = "cannot parse '{}': ".format(bitmap)
                    msg += "unknown type of LoadShape"
                    raise ValueError(msg)

    @staticmethod
    def create_bitmap(start, end, weekdays, weekends):
        """
        Creates a bitmap that can be used to initialise a LoadShape instance.

        Bitmap is an int who's binary representation indicates the loadshape
        profile: leftmost 24 bits represent weekend loadshape, rightmost 24
        bits represent weekday loadshape

        This helper function creates a bitmap to be True between start and end
        (inclusive on left, exclusive on right) for weekdays and / or weekends
        """
        assert start < end
        bitmap = ['0'] * 48
        if weekdays or weekends:
            ones = ['1'] * (end - start)
            if weekdays:
                bitmap[start:end] = ones
            if weekends:
                bitmap[start+24:end+24] = ones
        return int("0b" + "".join(reversed(bitmap)), 2)

    def intersects(self, other):
        if isinstance(other, LoadShape):
            return self.bitmap & other.bitmap
        return other.intersects(self)

    def intersection(self, other, name=None):
        """
        Creates a new LoadShape with intersecting load shape
        name can optionally be provided and passed to the new object
        """
        if isinstance(other, LoadShape):
            return LoadShape(self.bitmap & other.bitmap, name)
        return other.intersection(self)

    def __contains__(self, lhs):
        return self.intersects(lhs) and self.intersection(lhs) == lhs

    def within(self, other):
        if isinstance(other, LoadShape):
            return self in other
        return False

    def difference(self, other, name=None):
        return LoadShape(self.bitmap ^ (self.bitmap & other.bitmap), name)

    def union(self, other, name=None):
        return LoadShape(self.bitmap | other.bitmap, name)

    def complement(self, name=None):
        # BASE is a pre-computed LoadShape, generated by this module
        return BASE.difference(self, name)

    def _load_factor(self, reference_load):
        """
        Helper function for weekend_load_factor and weekday_load_factor
        reference bitmap is the BASE loadshape for the time period of
        interest
        """
        bitmap = self.bitmap & reference_load.bitmap
        hours = bin(bitmap).count('1')
        return hours / 24

    @property
    def weekday_load_factor(self):
        # WEEKDAY is a pre-computed LoadShape, generated by this module
        return self._load_factor(WEEKDAY)

    @property
    def weekend_load_factor(self):
        # WEEKEND is a pre-computed LoadShape, generated by this module
        return self._load_factor(WEEKEND)

    def __repr__(self):
        return "LoadShape({}, {})".format(self.bitmap, self.name)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return self.display_bitmap

    @property
    def display_bitmap(self):
        # format as a binary string, zfill forces preceeding zeros
        bin_string = "{0:b}".format(self.bitmap).zfill(48)
        weekends = bin_string[:24][::-1]  # reverse so that hour(0) first
        weekdays = bin_string[24:][::-1]  # reverse so that hour(0) first
        return "weekdays: {}\nweekends: {}".format(weekdays, weekends)

    @property
    def is_hour(self):
        """
        Returns true if there's exactly one hour in weekday,
        exactly one hour in weekend, or the same hour occurs exactly once
        in both weekday and weekend
        """
        bin_string = "{0:b}".format(self.bitmap).zfill(48)
        weekends = bin_string[:24][::-1].count('1')
        weekdays = bin_string[24:][::-1].count('1')
        if weekends == 1 and weekdays == 0:
            return True
        elif weekdays == 1 and weekends == 0:
            return True
        elif weekends == 1 and weekdays == 1:
            weekend_posn = bin_string[:24][::-1].find('1')
            weekday_posn = bin_string[24:][::-1].find('1')
            if weekend_posn == weekday_posn:
                return True
        else:
            return False

    @property
    def hour(self):
        bin_string = "{0:b}".format(self.bitmap).zfill(48)
        if self.is_hour:
            hour = bin_string[:24][::-1].find('1')
            if hour > -1:
                return hour
            else:
                return bin_string[24:][::-1].find('1')
        else:
            msg = "hour property can only be called if the loadshape is hourly"
            msg += ": loadshape {} was given".format(str(self))
            raise ValueError(msg)

    def __iter__(self):
        bit = 1
        bit_posn = 0
        while bit_posn <= 48:
            if bit & self.bitmap != 0:
                yield LoadShape(bit)
            bit *= 2
            bit_posn += 1

    def __len__(self):
        return bin(self.bitmap).count('1')

# precompute named load shapes

BASE = LoadShape(LoadShape.create_bitmap(0, 24, True, True), 'Base')
PEAK = LoadShape(LoadShape.create_bitmap(8, 20, True, False), 'Peak')
OFFPEAK = PEAK.complement("Offpeak")
WEEKDAY = LoadShape(LoadShape.create_bitmap(0, 24, True, False), 'Weekday')
WEEKDAY_OFFPEAK = WEEKDAY.difference(PEAK, 'Weekday Offpeak')
WEEKEND = OFFPEAK.difference(WEEKDAY_OFFPEAK, 'Weekend')
WEEKEND_PEAK = LoadShape(LoadShape.create_bitmap(8, 20, False, True),
                         'Weekend Peak')
WEEKEND_OFFPEAK = WEEKEND.difference(WEEKEND_PEAK, 'Weekend Offpeak')
DAYTIME = PEAK.union(WEEKEND_PEAK, 'Daytime')
NIGHTTIME = BASE.difference(DAYTIME, 'Nighttime')
EXTENDED_DAYTIME = LoadShape(LoadShape.create_bitmap(8, 24, True, True),
                             'Extended Daytime')
EXTENDED_PEAK = LoadShape(LoadShape.create_bitmap(8, 24, True, False),
                          'Extended Peak')
WEEKEND_EXTENDED_PEAK = EXTENDED_DAYTIME.difference(EXTENDED_PEAK,
                                                    'Weekend Extended Peak')
NEVER_LS = BASE.complement('Never')

HOURS = [LoadShape(LoadShape.create_bitmap(i, i+1, True, True),
                   'H{:02d}'.format(i)) for i in range(24)]
WEEKDAY_HOURS = [hour.intersection(WEEKDAY, 'Weekday-'+hour.name)
                 for hour in HOURS]
WEEKEND_HOURS = [hour.intersection(WEEKEND, 'Weekend-'+hour.name)
                 for hour in HOURS]
EFAS = [LoadShape(LoadShape.create_bitmap(4*i, 4*(i+1), True, True),
                  'EFA{:d}'.format(i+1)) for i in range(6)]
WEEKDAY_EFAS = [efa.intersection(WEEKDAY, 'Weekday-'+efa.name) for efa in EFAS]
WEEKEND_EFAS = [efa.intersection(WEEKEND, 'Weekend-'+efa.name) for efa in EFAS]
