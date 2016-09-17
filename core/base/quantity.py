# TODO: work out why __getstate__ and __setstate__ are being used; possibly to allow multiprocessing or pickling
# TODO: need to do this for the entire time_period module too, and see if it needs to be implemented.

from inputs.static_data.time_constants import DAYS_PER_YEAR

import abc
import numpy as np
import ast


class UnitError(Exception):
    """Raised when there are mismatched units"""


class _AbstractUnit(object):
    # create the dictionary for the Multiton pattern
    instances = dict()

    def __new__(cls, name, base_multiplier):
        try:
            cache = cls.instances[name.lower().strip()]
            assert cache.base_multiplier == base_multiplier
            return cache
        except KeyError:
            new = super().__new__(cls)
            new.name = name
            new.base_multiplier = base_multiplier
            new._hash = None
            cls.instances[new.name] = new
            return new
        except AssertionError:
            raise UnitError("Abstract unit with same name but different base_multiplier already defined")

    @abc.abstractproperty
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
        new = super().__new__(cls, name, base_multiplier)
        if isinstance(base_unit, _BaseUnit):
            new.base_unit = base_unit
        elif isinstance(base_unit, _DerivedUnit):
            raise UnitError("base_unit of {} is already defined as a derived unit".format)
        else:
            new.base_unit = _BaseUnit(base_unit)
        return new

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
    # create a cache for operations on units
    _cache = dict()

    def __new__(cls, units, exponents=None):
        """
        New Unit object.

        :param units: a list who's elements are _AbstractUnit instances
        :param exponents: a list of floats who's elements are exponents of the unit at the same location
        :return: Unit object
        """

        # if we have a single argument which is a string, parse this to get units and exponents lists
        if not exponents and isinstance(units, str):
            units, exponents = Unit._parse(units)

        # raise a UnitError if we have degenerate units
        unique_units = set(units)
        Unit._degeneracy_test(unique_units)

        # simplify the list of units and exponents:
        if len(unique_units) == len(units):
            # there are no repeated units, so sort alphabetically on the unit name and remove units with zero exponent
            reduced_units, reduced_exponents = Unit._simplify_no_repeats(units, exponents)
        else:
            # there are repeated units, so we need to sum their exponents then consolidate the unit list as above
            reduced_units, reduced_exponents = Unit._simplify(sorted(unique_units), sorted(zip(units, exponents)))

        # implement multiton
        try:
            return cls._instances[(reduced_units, reduced_exponents)]
        except KeyError:
            new = super().__new__(cls)
            new.units = reduced_units
            new.exponents = reduced_exponents
            new._hash = None
            cls._instances[(reduced_units, reduced_exponents)] = new
            return new

    @staticmethod
    def _parse(string):
        """
        Parses units in a variety of sensible formats:
            - gbp / mwhp
            - mwhg.mwhp^2
            - mwhg / (bbl^3)
            - 1 / mwhg
            - (mwhg^2.mwhp) / (mwhp^3)
            - (mwhg^2.mwhp) / (gbp^3.bbl^2)

        :param string: the string to be parsed
        :return: a pair of tuples, the first having the units and the second the corresponding exponents
        """
        units = []
        exponents = []

        # check for empty string
        if string.strip() == '':
            return (), ()

        # split positive and negative sub-units
        for i, half in enumerate(string.split('/')):
            if not half:
                raise ValueError("{} is not a validly formatted unit".format(string))
            sign = (-1) ** i
            half = half.strip()
            if half == "":
                raise ValueError("{} is not a validly formatted unit".format(string))

            # deal with parenthesis
            if "(" in half or ")" in half:
                if half.startswith("(") and half.endswith(")"):
                    half = half[1:-1]
                else:
                    raise ValueError("{} is not a validly formatted unit".format(string))

            # deal with no unit case
            if half == '1':
                half = ""

            # parse and aggregate components of this half
            for token in half.split("."):
                if token:
                    split = token.split("^")
                    if len(split) == 1:
                        weight = 1
                    else:
                        weight = int(split[1].strip())
                    try:
                        new = _AbstractUnit.instances[split[0].strip()]
                    except KeyError:
                        raise ValueError("{} has an unknown abstract unit {}".format(string, split[0].strip()))
                    units.append(new)
                    exponents.append(weight * sign)
        return tuple(units), tuple(exponents)

    @staticmethod
    def _degeneracy_test(unique_units):
        """
        Test for degenerate units: raises a UnitError where there are multiple _DerivedUnits with the same _BaseUnit,
        or a _BaseUnit with one or more of its _DerivedUnits. These are degenerate because they represent floats or
        quantities (e.g. GBP / PENCE = 100; GBP * MwH / PENCE = 100 MwH)

        :param unique_units: a set of abstract units
        :return: raises a UnitError if unique_units is degenerate
        """
        base_units = set([])
        for unit in unique_units:
            if unit.reference_unit in base_units:
                raise UnitError("unit cannot have multiple abstract units having the same base unit")
            else:
                base_units.add(unit.reference_unit)

    @staticmethod
    def _simplify_no_repeats(units, exponents):
        """
        Sorts both units and exponents, in alphabetical order on the units. Removes from both lists if a unit has an
        exponent of zero.

        :param units: a list of _AbstractUnit objects
        :param exponents: a list of integers representing the exponents of the units
        :return: a pair of tuples, containing the units and exponents respectively
        """
        # first sort both units and exponents alphabetically by units
        if len(units) != 0:
            consolidated_units, consolidated_exponents = zip(*sorted(zip(units, exponents)))
        else:
            return (), ()
        # and then remove any units with an exponent of zero
        if 0 in consolidated_exponents:
            new_units = []
            new_exponents = []
            for index, exponent in enumerate(consolidated_exponents):
                if exponent != 0:
                    new_units.append(consolidated_units[index])
                    new_exponents.append(exponent)
            consolidated_exponents = new_exponents
            consolidated_units = new_units
        return tuple(consolidated_units), tuple(consolidated_exponents)

    @staticmethod
    def _simplify(sorted_unique_units, sorted_tuples):
        """
        Simplify the list of units and exponents:
            - sort both lists alphabetically by unit name
            - remove any duplicates, summing the exponents on the repeated unit names
            - remove any units with a (net) exponent of zero

        :param sorted_unique_units: a list of unique _AbstractUnit objects, sorted alphabetically by unit name
        :param sorted_tuples: sorted list of tuples of _AbstractUnit objects and their exponents
        :return: a pair of tuples, containing the grouped units and exponents respectively
        """
        reduced_units = []
        reduced_exponents = []
        index = 0
        for unit in sorted_unique_units:
            exponent_sum = 0
            for pair in sorted_tuples[index:]:
                if unit == pair[0]:
                    exponent_sum += pair[1]
                    index += 1
                else:
                    break
            if exponent_sum != 0:
                reduced_units.append(unit)
                reduced_exponents.append(exponent_sum)
        return tuple(reduced_units), tuple(reduced_exponents)

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

    @staticmethod
    def standardise(lhs, rhs):
        """
        If both units have _AbstractUnits with the same _BaseUnit then any such _DerivedUnits are converted into their
        reference _BaseUnit. Returns a tuple with two Quantities, the value holds the product of any conversion factors.

        :param lhs: Unit
        :param rhs: Unit
        :return: tuple of Quantities
        """
        new_lhs_units = list(lhs.units)
        new_rhs_units = list(rhs.units)
        lhs_conversion_factor = 1
        rhs_conversion_factor = 1
        for lhs_index, lhs_unit in enumerate(lhs.units):
            for rhs_index, rhs_unit in enumerate(rhs.units):
                if lhs_unit.reference_unit == rhs_unit.reference_unit and lhs_unit != rhs_unit:
                    new_lhs_units[lhs_index] = lhs_unit.reference_unit
                    new_rhs_units[rhs_index] = rhs_unit.reference_unit
                    lhs_conversion_factor *= lhs_unit.base_multiplier ** lhs.exponents[lhs_index]
                    rhs_conversion_factor *= rhs_unit.base_multiplier ** rhs.exponents[rhs_index]
        return (Quantity(lhs_conversion_factor, Unit(new_lhs_units, lhs.exponents)),
                Quantity(rhs_conversion_factor, Unit(new_rhs_units, rhs.exponents)))

    @staticmethod
    def _consolidate(abstract_units, exponents):
        """
        Converts a list of _AbstractUnits into a standardised form, where any _DerivedUnits have been converted into
        _BaseUnits if there are one or more units with the same _BaseUnit. Returns either:

            - Unit:             if no conversion has taken place
            - Quantity:         if conversion has taken place and the units haven't all cancelled out
            - float or int:     if conversion has taken place, and all the units have cancelled out

        :param abstract_units: a list or tuple of _AbstractUnits
        :param exponents: the exponents of each _AbstractUnit
        :return: a Unit, Quantity or int or float with the consolidated output
        """
        conversion_factor = 1
        new_units = []
        new_exponents = []
        done = set([])
        for outer_index, outer_unit in enumerate(abstract_units):
            if outer_index not in done:
                found_equivalent = False
                exponent = exponents[outer_index]
                for inner_index in range(outer_index + 1, len(abstract_units)):
                    if inner_index not in done:
                        inner_unit = abstract_units[inner_index]
                        if outer_unit.reference_unit == inner_unit.reference_unit:
                            done.add(inner_index)
                            exponent += exponents[inner_index]
                            if outer_unit != inner_unit:
                                conversion_factor *= inner_unit.base_multiplier ** exponents[inner_index]
                                if not found_equivalent:
                                    found_equivalent = True
                                    conversion_factor *= outer_unit.base_multiplier ** exponents[outer_index]
                                    outer_unit = outer_unit.reference_unit
                if exponent:
                    new_units.append(outer_unit)
                    new_exponents.append(exponent)
                done.add(outer_index)
        if len(new_units) == 0:
            return conversion_factor
        if conversion_factor == 1:
            return Unit(new_units, new_exponents)
        else:
            return Quantity(conversion_factor, Unit(new_units, new_exponents))

    @property
    def reference_unit(self):
        """
        Converts any components which are _DerivedUnit into their _BaseUnit, the resulting conversion factors
        are multiplied and become the value on the Quantity. Note that by definition a Unit can't have a mix of
        _DerivedUnits and _BaseUnits with the same _BaseUnit. So the resulting Unit will always be non-empty.

        :return: Quantity
        """
        conversion_factor = 1
        new_units = []
        for index, unit in enumerate(self.units):
            new_units.append(unit.reference_unit)
            conversion_factor *= unit.base_multiplier ** self.exponents[index]
        return Quantity(conversion_factor, Unit(new_units, self.exponents))

    def __mul__(self, rhs):
        """
        Multiplies two Units. Returns either a simplified Unit, or a Quantity or a float. Examples:

        GBP * (1/GBP) = 1 [Float]
        GBP * (1/PENCE) = 100 [Float]
        GBP * GBP = GBP**2 [Unit]
        GBP * PENCE = 1/100 * GBP**2 [Quantity]
        """
        if isinstance(rhs, Unit):
            if ('*', self, rhs) in Unit._cache:
                return Unit._cache[('*', self, rhs)]
            elif ('*', rhs, self) in Unit._cache:
                return Unit._cache[('*', rhs, self)]
            combined_units = list(self.units + rhs.units)
            combined_exponents = self.exponents + rhs.exponents
            try:
                product = Unit(combined_units, combined_exponents)
                if product == DIMENSIONLESS:
                    return 1
                Unit._cache[('*', self, rhs)] = Unit(combined_units, combined_exponents)
            except UnitError:
                Unit._cache[('*', self, rhs)] = Unit._consolidate(combined_units, combined_exponents)
            return Unit._cache[('*', self, rhs)]
        elif isinstance(rhs, Quantity):
            return (self * rhs.unit) * rhs.value
        elif isinstance(rhs, (int, float)):
            return Quantity(rhs, self)
        else:
            try:
                if rhs.dtype == object:
                    return rhs * self
                return Quantity(rhs, self)
            except:
                raise UnitError("cannot multiply Unit {} with {}".format(self, rhs))

    def __rmul__(self, lhs):
        assert isinstance(lhs, (int, float, np.ndarray))
        return Quantity(lhs, self)

    def __truediv__(self, rhs):
        """
        Multiplies two Units. Returns either a simplified Unit, or a Quantity or a float. Examples:

            GBP / GBP = 1 [Float]
            GBP / PENCE = 100 [Float]
            GBP / (1/GBP) = GBP**2 [Unit]
            GBP / PENCE = 100 * GBP**2 [Quantity]
        """
        if isinstance(rhs, Unit):
            if ('/', self, rhs) in Unit._cache:
                return Unit._cache[('*', self, rhs)]
            elif ('/', rhs, self) in Unit._cache:
                return Unit._cache[('*', rhs, self)]
            rhs = rhs.inverse
            combined_units = list(self.units + rhs.units)
            combined_exponents = self.exponents + rhs.exponents
            try:
                division = Unit(combined_units, combined_exponents)
                if division == DIMENSIONLESS:
                    return 1
                Unit._cache[('/', self, rhs)] = Unit(combined_units, combined_exponents)
            except UnitError:
                Unit._cache[('/', self, rhs)] = Unit._consolidate(combined_units, combined_exponents)
            return Unit._cache[('/', self, rhs)]
        elif isinstance(rhs, Quantity):
            return (self * rhs.unit.inverse) / rhs.value
        elif isinstance(rhs, (int, float)):
            return Quantity(1 / rhs, self)
        else:
            try:
                if rhs.dtype == object:
                    return 1 / (rhs / self)
                return Quantity(1 / rhs, self)
            except:
                raise UnitError("cannot multiply Unit with {}".format(self))

    def __rtruediv__(self, lhs):
        assert isinstance(lhs, (int, float, np.ndarray))
        return Quantity(lhs, self.inverse)

    @property
    def inverse(self):
        return Unit(self.units, (-exponent for exponent in self.exponents))

    def conversion_factor(self, other):
        if self == other:
            return 1
        original = self.reference_unit
        target = other.reference_unit
        if original.unit == target.unit:
            return original.value / target.value
        else:
            msg = "cannot convert between units {} and {}, since they don't have the same ".format(self, other)
            msg += "standard form: {} has standard form {} ".format(self, original)
            msg += "whereas {} has standard form: {}".format(other, target)
            raise UnitError(msg)

    def equivalent(self, other):
        try:
            _ = self.conversion_factor(other)
            return True
        except UnitError:
            return False

    def _separate(self):
        def _gen_from_zip(pairs):
            if pairs:
                units, exponents = zip(*pairs)
                return Unit(units, exponents)
            else:
                return None

        numerator = []
        denominator = []
        for unit, exponent in zip(self.units, self.exponents):
            if exponent > 0:
                numerator.append((unit, exponent))
            else:
                denominator.append((unit, exponent))
        numerator = _gen_from_zip(numerator)
        denominator = _gen_from_zip(denominator)
        return numerator, denominator

    @property
    def numerator(self):
        if self._separate()[0]:
            return self._separate()[0]
        return DIMENSIONLESS

    @property
    def denominator(self):
        if self._separate()[1]:
            return self._separate()[1].inverse
        return DIMENSIONLESS

    def __str__(self):
        def _format(unit, exponent):
            if exponent == 1:
                return unit
            else:
                return "{}^{}".format(unit, exponent)

        numerator, denominator = self._separate()
        if numerator:
            numerator = list(zip(numerator.units, numerator.exponents))
            string = ".".join([_format(unit.name, exponent) for unit, exponent in numerator])
            if denominator and len(numerator) > 1:
                string = "(" + string + ")"
        else:
            if denominator:
                string = "1"
            else:
                return "DIMENSIONLESS"
        if denominator:
            denominator = list(zip(denominator.units, denominator.exponents))
            string += " / "
            denom_string = ".".join([_format(unit.name, -exponent) for unit, exponent in denominator])
            if len(denominator) > 1:
                denom_string = "(" + denom_string + ")"
            string += denom_string
        return string

    @property
    def name(self):
        return str(self)

    def __repr__(self):
        return "{}(".format(self.__class__.__name__) + self.__str__() + ")"


class Quantity(object):
    def __init__(self, value, unit=Unit([], [])):
        if isinstance(value, str):
            value, unit = Quantity._parse(value)
        self.value = np.array(value, np.float64)
        # TODO work out whether we need to hash Quantity, and if so think about making a "FrozenQuantity" where these
        # TODO are uncommented, similarly for the __hash__ function below.
        # self.value.flags.writeable = False
        # self._hash = None
        if isinstance(unit, Unit):
            self.unit = unit
        else:
            raise UnitError("{} is not a Unit".format(unit))

    @staticmethod
    def _parse(string):
        """
        parses a string into a separate value (numpy array) and instance of Unit. Can understand:
        "value * unit"
        "[value, value] * unit"
        "value unit"
        "[value, value] unit

        :param string: the input string
        :return: value, unit
        """
        if string.startswith("Quantity"):
            start, end = string.find("("), string.rfind(")")
            if start == -1 or end == -1:
                raise ValueError("unbalanced parentheses")
            value, unit = string[start + 1:end].rsplit(",", 1)
        elif "*" in string:
            value, unit = string.split("*")
        else:
            index = 0
            while index < len(string) and string[index] in "0123456789+-.eE ,[]":
                index += 1
            value, unit = string[:index], string[index:]
        try:
            if "[" in value:
                value = np.array(ast.literal_eval(value))
            else:
                value = np.array(float(value))
            unit = Unit(unit)
            return value, unit
        except ValueError as e:
            raise ValueError("Can't parse base {}: {}".format(string, e))

    # TODO as above, work out whether we need to hash, and implement a FrozenQuantity
    # def __hash__(self):
    #     if not self._hash:
    #         self._hash = hash((self.value.tostring(), self.unit))
    #     return self._hash

    def __repr__(self):
        return "{}(value={}, unit={})".format(self.__class__.__name__, self.value.tolist(), self.unit)

    def __str__(self):
        return "{} * {}".format(self.value.tolist(), self.unit)

    def convert(self, other_unit):
        """
        Converts a base into another base with a different unit. The value is multiplied by any conversion
        factor.

        :param other_unit: a Unit object
        :return: Quantity
        """
        if isinstance(other_unit, Unit):
            return Quantity(self.value * self.unit.conversion_factor(other_unit), other_unit)
        else:
            raise UnitError("Can only convert to a Unit, not {} of type {}".format(other_unit, type(other_unit)))

    def __mul__(self, rhs):
        """
        Multiplies a Quantity with another Quantity, Unit or value like object
        :param rhs: another Quantity, Unit or value like object
        :return: Quantity or value like object
        """
        if isinstance(rhs, Quantity):
            return Quantity(self.value * rhs.value, self.unit) * rhs.unit
        elif isinstance(rhs, Unit):
            new_unit = self.unit * rhs
            if isinstance(new_unit, Unit):
                return Quantity(self.value, new_unit)
            elif isinstance(new_unit, Quantity):
                return Quantity(self.value * new_unit.value, new_unit.unit)
            elif isinstance(new_unit, (float, int)):
                if self.value.shape:
                    # we don't want to return a "regular" np.ndarray because we can't overload right multiplication
                    # better to return a Quantity object so that left and right multiplication are equivalent
                    return Quantity(self.value * new_unit, Unit([],[]))
                else:
                    return self.value * new_unit
        elif isinstance(rhs, (int, float, np.ndarray)):
            return Quantity(self.value * rhs, self.unit)

    def __rmul__(self, lhs):
        return self.__mul__(lhs)

    def __truediv__(self, rhs):
        if isinstance(rhs, Unit):
            return self * rhs.inverse
        elif isinstance(rhs, Quantity):
            new_unit = self.unit * rhs.unit.inverse
            if isinstance(new_unit, Unit):
                return Quantity(self.value / rhs.value, new_unit)
            elif isinstance(new_unit, Quantity):
                return Quantity(self.value / rhs.value * new_unit.value, new_unit.unit)
            elif isinstance(new_unit, (float, int)):
                if self.value.shape:
                    # we don't want to return a "regular" np.ndarray because we can't overload right multiplication
                    # better to return a Quantity object so that left and right multiplication are equivalent
                    return Quantity(self.value / rhs.value * new_unit, Unit([], []))
                else:
                    return self.value / rhs.value * new_unit
        elif isinstance(rhs, (int, float, np.ndarray)):
            if np.any(rhs == 0):
                raise ZeroDivisionError
            return Quantity(self.value / rhs, self.unit)

    def __rtruediv__(self, lhs):
        assert isinstance(lhs, (int, float, np.ndarray))
        return Quantity(lhs / self.value, self.unit.inverse)

    def __add__(self, rhs):
        """
        Adds two numbers with units
            If they share the same unit, keep this unit
            If they have a different but equivalent unit, convert to the reference unit
            If they have a different unit and aren't equivalent, raise a UnitError

        :param rhs: Quantity
        :return: Quantity
        """
        if isinstance(rhs, Quantity):
            if self.unit == rhs.unit or (rhs.unit == DIMENSIONLESS and rhs.value == 0):
                return Quantity(self.value + rhs.value, self.unit)
            elif self.unit == DIMENSIONLESS:
                return Quantity(self.value + rhs.value, rhs.unit)
            else:
                std_lhs, std_rhs = Unit.standardise(self.unit, rhs.unit)
                if std_lhs.unit == std_rhs.unit:
                    return Quantity(self.value * std_lhs.value + rhs.value * std_rhs.value, std_lhs.unit)
            raise UnitError("Cannot add quantities of different units: {} and {}".format(self.unit, rhs.unit))
        # allow addition of a scalar with a number or array, dropping the result back down to a number or array
        elif self.unit == DIMENSIONLESS:
            return self.value + rhs
        # need to allow for addition of zero, otherwise the sum function/method breaks
        elif isinstance(rhs, np.ndarray):
            if all(rhs == 0):
                # here we don't return self, because we potentially want to broadcast the array, e.g.
                # Quantity(1, GBP) + array([0,0,0]) -> Quantity([1, 1, 1], GBP)
                return Quantity(self.value + rhs, self.unit)
        elif rhs == 0:
            return self
        raise TypeError("Cannot add Quantity and unitless object")

    def __radd__(self, lhs):
        if lhs == 0:
            return self
        return self + lhs

    def __neg__(self):
        return Quantity(-self.value, self.unit)

    def __sub__(self, rhs):
        return self.__add__(-rhs)

    def __rsub__(self, lhs):
        return -self.__add__(lhs)

    def __pow__(self, exponent):
        new_exponents = []
        for old_exponent in self.unit.exponents:
            new_exponents.append(old_exponent * exponent)
        #new_exponents = (old_exponent * exponent for old_exponent in self.unit.exponents)
        return Quantity(self.value ** exponent, Unit(self.unit.units, new_exponents))

    def __abs__(self):
        return Quantity(abs(self.value), self.unit)

    def __len__(self):
        return len(self.value)

    def __iter__(self):
        for i in range(len(self.value)):
            yield Quantity(self.value[i], self.unit)

    def __getitem__(self, index):
        return Quantity(self.value[index], self.unit)

    def __setitem__(self, index, new_value):
        if self.unit == DIMENSIONLESS:
            if isinstance(new_value, Quantity):
                self.unit = new_value.unit
                self.value[index] = new_value.value
            else:
                self.value[index] = new_value
        else:
            try:
                new_value = new_value.convert(self.unit)
            except AttributeError:
                raise UnitError("Can't assign {} to {} Quantity[Item={}]".format(new_value, self.unit, index))
            self.value[index] = new_value.value

    def is_zero(self):
        return all(self.value == 0)

    def __eq__(self, other):
        """
        Tests equality of base with another object. Is forgiving:

            - Two quantities are equal even if they have different units, provided the units
              are compatible and the values compare after converting to equal units
            - A base and unit are equal, provided the units are equal and the value of the base is 1
            - A base is equal to zero (integer, float) if all it's values are zero
            - A quanitty with DIMENSIONLESS unit can be equal to an interger / float if the values are equal.

        :param other: the object being compared
        :return: boolean
        """
        try:
            if isinstance(other, Quantity):
                # quantities can be equal even if they are quoted in different, but comparable units
                if self.unit != DIMENSIONLESS and other.unit != DIMENSIONLESS:
                    other = other.convert(self.unit)
                return np.all(self.value == other.value) and (self.unit == other.unit or np.all(other.value == 0))
            elif isinstance(other, Unit) and np.all(self.value == 1):
                return self.unit == other
            elif np.all(self.value == 0) or self.unit == DIMENSIONLESS:
                return np.all(self.value == other)
            else:
                return False
        except UnitError:
            return False


    def __ne__(self, other):
        return not self == other

    def __gt__(self, other):
        if isinstance(other, (int, float)):
            if other == 0:
                return self.value > 0
            if self.unit == DIMENSIONLESS:
                return self.value > other
        try:
            other = other.convert(self.unit)
            return self.value > other.value
        except AttributeError:
            raise TypeError("{} ({}) is not a Quantity of {}".format(other, type(other), self.unit))
        except UnitError:
            raise UnitError("units of {} ({}) are not equivalent to {} ({})".format(other, other.unit, self, self.unit))

    def __ge__(self, other):
        if isinstance(other, (int, float)):
            if other == 0:
                return self.value >= 0
            if self.unit == DIMENSIONLESS:
                return self.value >= other
        try:
            other = other.convert(self.unit)
            return self.value >= other.value
        except AttributeError:
            raise TypeError("{} ({}) is not a Quantity of {}".format(other, type(other), self.unit))
        except UnitError:
            raise UnitError("units of {} ({}) are not equivalent to {} ({})".format(other, other.unit, self, self.unit))

    def __lt__(self, other):
        if isinstance(other, (int, float)):
            if other == 0:
                return self.value < 0
            if self.unit == DIMENSIONLESS:
                return self.value < other
        try:
            other = other.convert(self.unit)
            return self.value < other.value
        except AttributeError:
            raise TypeError("{} ({}) is not a Quantity of {}".format(other, type(other), self.unit))
        except UnitError:
            raise UnitError("units of {} ({}) are not equivalent to {} ({})",
                            format(other, other.unit, self, self.unit))

    def __le__(self, other):
        if isinstance(other, (int, float)):
            if other == 0:
                return self.value <= 0
            if self.unit == DIMENSIONLESS:
                return self.value <= other
        try:
            other = other.convert(self.unit)
            return self.value <= other.value
        except AttributeError:
            raise TypeError("{} ({}) is not a Quantity of {}".format(other, type(other), self.unit))
        except UnitError:
            raise UnitError("units of {} ({}) are not equivalent to {} ({})",
                            format(other, other.unit, self, self.unit))

    def __bool__(self):
        return bool(np.all(self.value))

    def round(self, ndigits):
        return Quantity(np.round(self.value, ndigits), self.unit)

    def argmax(self, axis=None):
        return self.value.argmax(axis)

    @property
    def shape(self):
        return self.value.shape

    def mean(self):
        return Quantity(np.mean(self.value), self.unit)


# Convenience functions


def unit(quantity):
    return getattr(quantity, "unit", DIMENSIONLESS)


def value(quantity):
    return getattr(quantity, "value", quantity)


def unique_unit(iterable):
    """
    Checks that the units in an iterable are consistent and returns it. Ignores any plain numbers.

    :param iterable: Quantities or numbers
    :return: Unit or UnitError
    """
    units = set(unit(x) for x in iterable)
    units = units.difference({DIMENSIONLESS})
    if len(units) == 0:
        return DIMENSIONLESS
    if len(units) == 1:
        return units.pop()
    else:
        raise UnitError("Mixed units: {}".format(units))


# Numpy functions mapped to Units
def ones(length, unit=Unit([],[])):
    return Quantity(np.ones(length), unit)


def zeros(length, unit=Unit([],[])):
    return Quantity(np.zeros(length), unit)


def array(iterable, unit=Unit([],[])):
    """
    An np.ndarray like object, primarily exists because multiplying an np.ndarray by a unit gives different
    behaviour between left multiplication (a Quantity, with the array as it's value) and right multiplication (an array
    who's elements are Quantities). This function always returns a Quantity, defaulting to DIMENSIONLESS unit so that it can
    be used as an alternative to an np.ndarray. This array has consistent behaviour between left multiplication and
    right multiplication. Both of them return a new Quantity, who's value is the array.

    :param iterable: quantities to be initialised as an np.ndarray in the objects value
    :param unit: the unit for the array, defaults to DIMENSIONLESS
    :return: Quantity object
    """
    return Quantity(np.array(iterable), unit)


def empty(shape, unit=Unit([],[])):
    return Quantity(np.empty(shape), unit)

def var(quantity_array, *args, **kwargs):
    if isinstance(quantity_array, Quantity):
        return quantity_array.unit * quantity_array.unit * np.var(quantity_array.value, *args, **kwargs)
    return np.var(quantity_array, *args, **kwargs)


def maximum(*args):
    # TODO Thorn specifically allows unit-less quantities in max and min. Work out if this is correct. The reason
    # TODO given is to support max(x, 0) etc. I think that zero should more naturally have the same units as x.
    # TODO e.g. the strike price has units.
    try:
        np_arrays = [x.value for x in args]
        units = set(x.unit for x in args)
        if len(units) == 1:
            return Quantity(np.maximum(*np_arrays), args[0].unit)
        else:
            raise UnitError("Quantities can only be compared if they have the same units: {} given".format(units))
    except AttributeError:
        raise UnitError("Arguments {} must all be Quantities".format(args))


def minimum(*args):
    # TODO Thorn specifically allows unit-less quantities in max and min. Work out if this is correct. The reason
    # TODO given is to support max(x, 0) etc. I think that zero should more naturally have the same units as x.
    # TODO e.g. the strike price has units.
    try:
        np_arrays = [x.value for x in args]
        units = set(x.unit for x in args)
        if len(units) == 1:
            return Quantity(np.minimum(*np_arrays), args[0].unit)
        else:
            raise UnitError("Quantities can only be compared if they have the same units: {} given".format(units))
    except AttributeError:
        raise UnitError("Arguments {} must all be Quantities".format(args))


def arange(start, stop, step):
    assert start.unit == stop.unit == step.unit
    return Quantity(np.arange(start.value, stop.value, step.value), start.unit)


def standardise(collection, unit=None):
    """
    If the collection has quantities with compatible units, they are converted to the common base unit.
    Optionallly, if a unit is specified, the quantities are converted to this unit, provided it's compatible.

    :param collection:
    :param unit:
    :return:
    """

    try:
        if unit:
            base_unit = unit
        else:
            if isinstance(collection, (list, tuple, set)):
                units = set(quantity.unit for quantity in collection)
            elif isinstance(collection, dict):
                units = set(quantity.unit for quantity in collection.values())
            else:
                raise ValueError("can only standardise lists, tuples, sets or dicts")
            if len(units) == 1:
                base_unit = units.pop()
            elif len(units) != 1:
                base_units = set(unit.reference_unit.unit for unit in units)
                if len(base_units) == 1:
                    base_unit = base_units.pop()
                else:
                    raise UnitError("can only standardise list of Quantities with equivalent units")
        if isinstance(collection, list):
            return [quantity.convert(base_unit) for quantity in collection]
        if isinstance(collection, tuple):
            return tuple(quantity.convert(base_unit) for quantity in collection)
        if isinstance(collection, set):
            return set(quantity.convert(base_unit) for quantity in collection)
        if isinstance(collection, dict):
            for key, value in collection.items():
                collection[key] = value.convert(base_unit)
            return collection
    except AttributeError:
        raise ValueError("can only standardise collection of Quantities")


def concatenate(quantity_list, axis=0):
    try:
        values = [quantity.value for quantity in quantity_list]
        units = set(quantity.unit for quantity in quantity_list)
        if len(units) == 1:
            try:
                return Quantity(np.concatenate(values, axis), units.pop())
            except ValueError:
                # quantity_list is a list of zero dimensional ndarrays, so can't be concatenated.
                return Quantity(values, units.pop())
    except AttributeError:
        raise ValueError("concatenate must be passed a list of Quantities")
    values = quantity_list[0].value
    unit = quantity_list[0].unit
    for quantity in quantity_list[1:]:
        done, new = Unit.standardise(unit, quantity.unit)
        unit = done.unit
        if unit == new.unit:
            try:
                values = np.concatenate([values * done.value, quantity.value * new.value], axis)
            except ValueError:
                # base list is a list of zero dimensional ndarrays, so can't be concatenated.
                values = [values] if isinstance(values, np.ndarray) else values
                values = [existing * done.value for existing in values]
                values += [quantity.value * new.value]
        else:
            raise UnitError("can only concatenate list of Quantities with equivalent units")
    return Quantity(values, unit)


def np_covariant(np_fn):
    def quantity_fn(quantity_array, *args, **kwargs):
        return Quantity(np_fn(quantity_array.value, *args, **kwargs), quantity_array.unit)
    quantity_fn.__name__ = np_fn.__name__
    return quantity_fn


amax = np_covariant(np.amax)
amin = np_covariant(np.amin)
matrix = np_covariant(np.matrix)
mean = np_covariant(np.mean)
std = np_covariant(np.std)
zeros_like = np_covariant(np.zeros_like)
ones_like = np_covariant(np.ones_like)
reshape = np_covariant(np.reshape)
percentile = np_covariant(np.percentile)
ravel = np_covariant(np.ravel)
empty_like = np_covariant(np.empty_like)
vstack = np_covariant(np.vstack)
transpose = np_covariant(np.transpose)
floor = np_covariant(np.floor)
ceil = np_covariant(np.ceil)

# Conversion factors
MWH_PER_THERM = 0.029307108333307068
MMBTU_PER_THERM = 0.1
MWH_PER_MMBTU = MWH_PER_THERM / MMBTU_PER_THERM
PPT_TO_POUND_PER_WHE = 1 / MWH_PER_THERM / 100
MWH_PER_GJ = 3.6
API2_GJ_PER_TONNE = 25.12
# HMRC Tonne Carbon / Tonne Coal - kg CO2e per tonne Coal (electricity generation) for 2013
HMRC_API2_CARBON_INTENSITY = 2252.7 / 1000

# Base Units
_DIMENSIONLESS = _BaseUnit("DIMENSIONLESS")
_MWH = _BaseUnit("MWH")
_BBL = _BaseUnit("BBL")
_KNOT = _BaseUnit("KNOT")
_DAY = _BaseUnit("DAY")
_TONNE = _BaseUnit("TONNE")
_EUR = _BaseUnit("EUR")
_GBP = _BaseUnit("GBP")
_USD = _BaseUnit("USD")

# Derived Units
_THERM = _DerivedUnit("THERM", MWH_PER_THERM, _MWH)
_KTHERM = _DerivedUnit("KTHERM", 1000 * MWH_PER_THERM, _MWH)
_MTHERM = _DerivedUnit("MTHERM", 1000000 * MWH_PER_THERM, _MWH)
_KWH = _DerivedUnit("KWH", 0.001, _MWH)
_MMBTU = _DerivedUnit("MMBTU", 10 * MWH_PER_THERM, _MWH)

_GJ_API2 = _DerivedUnit("GJ_API2", API2_GJ_PER_TONNE, _TONNE)
_MWH_API2 = _DerivedUnit("MWH_API2", MWH_PER_GJ * API2_GJ_PER_TONNE, _TONNE)

_MT_FO = _DerivedUnit("MT_FO", 6.35, _BBL)
_MT_GO = _DerivedUnit("MT_FO", 7.45, _BBL)

_HOUR = _DerivedUnit("HOUR", 1 / 24, _DAY)
_MINUTE = _DerivedUnit("MINUTE", 1 / 24 / 60, _DAY)
_YEAR = _DerivedUnit("YEAR", DAYS_PER_YEAR, _DAY)

_PENCE = _DerivedUnit("PENCE", 0.01, _GBP)

# Public Units
DIMENSIONLESS = Unit([], [])

PENCE = Unit([_PENCE], [1])
GBP = Unit([_GBP], [1])
USD = Unit([_USD], [1])
EUR = Unit([_EUR], [1])

MWH = Unit([_MWH], [1])
THERM = Unit([_THERM], [1])
KWH = Unit([_KWH], [1])
KTHERM = Unit([_KTHERM], [1])
MTHERM = Unit([_MTHERM], [1])
MMBTU = Unit([_MMBTU], [1])

GJ_API2 = Unit([_GJ_API2], [1])
TONNE = Unit([_TONNE], [1])

BBL = Unit([_BBL], [1])
MT_FO = Unit([_MT_FO], [1])
MT_GO = Unit([_MT_GO], [1])

DAY = Unit([_DAY], [1])
HOUR = Unit([_HOUR], [1])
MINUTE = Unit([_MINUTE], [1])
YEAR = Unit([_YEAR], [1])

MW = Quantity(1/24, MWH / DAY)

# HMRC conversion of carbon tax in gbp/tonne to gbp/kWh gas
# Gaseous fules, natural gas: kg C02e per kWh
HMRC_NBP_CARBON_INTENSITY = 0.18404 * TONNE / KWH
