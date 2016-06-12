# TODO: work out why __getstate__ and __setstate__ are being used; possibly to allow multiprocessing or pickling
# TODO: need to do this for the entire time_period module too, and see if it needs to be implemented.

from abc import abstractproperty


class UnitError(Exception):
    """Raised when there are mismatched units"""


class _AbstractUnit(object):

    # create the dictionary for the Multiton pattern
    _instances = dict()

    def __new__(cls, name, base_multiplier):
        try:
            cache = cls._instances[name.lower().strip()]
            assert cache.base_multiplier == base_multiplier
            return cache
        except KeyError:
            unit = super().__new__(cls)
            unit.name = name
            unit.base_multiplier = base_multiplier
            unit._hash = None
            cls._instances[unit.name] = unit
            return unit
        except AssertionError:
            raise UnitError("Abstract unit with same name but different base_multiplier already defined")

    @abstractproperty
    def reference_unit(self):
        raise NotImplementedError

    def conversion_factor(self, other):
        if other.reference_unit != self.reference_unit:
            raise UnitError("Can't convert from {} to {}".format(self, other))
        return self.base_multiplier / other.base_multiplier

    def __str__(self):
        return self.name

    def __repr__(self):
        my_repr = "{}(name={}, base_multiplier={})".format(self.__class__.__name__, self.name, self.base_multiplier)
        return my_repr

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        if not self._hash:
            self._hash = hash(self.name)
        return self._hash

    def __lt__(self, other):
        return self.name < other.name


class _BaseUnit(_AbstractUnit):

    def __new__(cls, name, base_multiplier=1):
        assert base_multiplier == 1
        return super().__new__(cls, name, base_multiplier)

    @property
    def reference_unit(self):
        return self


class _DerivedUnit(_AbstractUnit):

    def __new__(cls, name, base_multiplier, base_unit):
        unit = super().__new__(cls, name, base_multiplier)
        if isinstance(base_unit, _BaseUnit):
            unit.base_unit = base_unit
        elif isinstance(base_unit, _DerivedUnit):
            raise UnitError("base_unit of {} is already defined as a derived unit".format)
        else:
            unit.base_unit = _BaseUnit(base_unit)
        return unit

    def __eq__(self, other):
        eq = self.name == other.name
        eq &= self.base_multiplier == other.base_multiplier
        eq &= self.reference_unit == other.reference_unit
        return eq

    def __hash__(self):
        return hash((super().__hash__(), hash(self.base_unit)))

    @property
    def reference_unit(self):
        return self.base_unit


class Unit(object):

    # create the dictionary for the Multiton pattern
    _instances = dict()

    def __new__(cls, units, exponents=None):
        """
        New Unit object.

        :param units: a list who's elements are _AbstractUnit instances
        :param exponents: a list of floats who's elements are exponents of the unit at the same location
        :return: Unit object
        """
        # if we have a single argument which is a string, parse this to get units and exponents lists
# if not exponents and isinstance(units, str):
#     units, exponents = Unit._parse(units)
        # sort both exponent and unit lists in order of increasing exponents
# if len(units) == 0:
#     raise UnitError("units cannot be empty")
        # test for degenerate units: where there are multiple _DerivedUnits with the same _BaseUnit, or a _BaseUnit
        # with one or more of its _DerivedUnits. These are degenerate because they represent floats or quantities
        # (e.g. GBP / PENCE = 100; GBP * MwH / PENCE = 100 MwH)
        unique_units = set(units)
        base_units = set(unit for unit in unique_units if isinstance(unit, _BaseUnit))
        for unit in unique_units:
            if isinstance(unit, _DerivedUnit) and unit.reference_unit in base_units:
                raise UnitError("units cannot have multiple abstract units having the same base unit")
        if len(unique_units) == len(units):
            # there are no repeated units, so we just need to sort alphabetically
            consolidated_units, consolidated_exponents = zip(*sorted(zip(units, exponents)))
            # and then remove any units with an exponent of zero
            consolidated_units = list(consolidated_units)
            consolidated_exponents = list(consolidated_exponents)
            if 0 in consolidated_exponents:
                for index, exponent in enumerate(consolidated_exponents):
                    if exponent == 0:
                        consolidated_exponents.remove(exponent)
                        consolidated_units.pop(index)
        else:
            # there are repeated units, so we need to sum their exponents and consolidate the unit list
            unique_units = sorted(unique_units)
            exponentiated_units = sorted(zip(units, exponents))
            consolidated_exponents = []
            consolidated_units = []
            index = 0
            for unit in unique_units:
                exponent_sum = 0
                for pair in exponentiated_units[index:]:
                    if unit == pair[0]:
                        exponent_sum += pair[1]
                        index += 1
                    else:
                        break
                if exponent_sum != 0:
                    consolidated_units.append(unit)
                    consolidated_exponents.append(exponent_sum)
        consolidated_units = tuple(consolidated_units)
        consolidated_exponents = tuple(consolidated_exponents)
        try:
            return cls._instances[(consolidated_units, consolidated_exponents)]
        except KeyError:
            unit = super().__new__(cls)
            unit.units = consolidated_units
            unit.exponents = consolidated_exponents
            unit._hash = None
            return unit

    @staticmethod
    def simpify(units, exponents):
        """"""

    def __hash__(self):
        if not self._hash:
            self._hash = hash((self.units, self.exponents))
        return self._hash

    # def __lt__(self, other):
    #     return hash(self) < hash(other)

    def __eq__(self, other):
        try:
            return self.units == other.units and self.exponents == other.exponents
        except AttributeError:
            return False
    #
    # def
    #
    # def __mul__(self, other):
    #     """
    #     Multiplies two Units. Returns either a simplified Unit, or a Quantity or a float. Examples:
    #
    #     GBP * (1/GBP) = 1 [Float]
    #     GBP * (1/PENCE) = 100 [Float]
    #     GBP * GBP = GBP**2 [Unit]
    #     GBP * PENCE = 1/100 * GBP**2 [Quantity]
    #     """
    #     if isinstance(other, Unit):
