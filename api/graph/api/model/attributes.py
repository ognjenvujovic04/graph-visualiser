"""
Defines attribute types and attribute value abstraction used in the graph data model.

Attributes represent typed values that can be attached to nodes or edges in the graph.
The AttributeValue class ensures that values conform to the declared attribute type
and provides comparison operations used by filtering and search mechanisms in the
platform.
"""

from datetime import datetime

class AttributeType:
    """
    Defines supported attribute data types.

    These constants represent the allowed primitive types that can be used
    for attribute values inside the graph model. They are used by the
    AttributeValue class to validate stored values.
    """

    INT = "int"
    FLOAT = "float"
    STR = "str"
    DATE = "date"


class AttributeValue(object):
    """
    Represents a typed attribute value used in the graph model.

    Each attribute value has an explicit type defined by AttributeType
    and a corresponding value that must match that type. This abstraction
    ensures type safety when storing attribute data and provides comparison
    operations that can be used by filtering or querying mechanisms in the
    platform.

    Args:
        attr_type: The type of the attribute value (one of AttributeType constants).
        value: The value of the attribute, which must match the specified type.
    """

    def __init__(self, attr_type: str, value):
        """
        Initializes a new AttributeValue instance.

        Args:
            attr_type: Attribute type defined in AttributeType.
            value: Value that must conform to the provided attribute type.
        """
        self.__type = None
        self.__value = None

        self.type = attr_type
        self.value = value

    @property
    def type(self):
        """
        Returns the type of the attribute.

        Returns:
            str: One of the types defined in AttributeType.
        """
        return self.__type

    @type.setter
    def type(self, value: str):
        """
        Sets the attribute type.

        Args:
            value: One of the allowed AttributeType constants.

        Raises:
            TypeError: If the provided type is not supported.
        """
        if value in (AttributeType.INT,
                     AttributeType.FLOAT,
                     AttributeType.STR,
                     AttributeType.DATE):
            self.__type = value
        else:
            raise TypeError("Invalid attribute type")

    @property
    def value(self):
        """
        Returns the stored attribute value.

        Returns:
            Any: The value corresponding to the attribute type.
        """
        return self.__value

    @value.setter
    def value(self, val):
        """
        Sets the attribute value while validating its type.

        The value must match the type specified by the `type` property.

        Args:
            val: Value to be assigned.

        Raises:
            TypeError: If the value does not match the declared attribute type.
        """
        if self.__type == AttributeType.INT:
            if isinstance(val, int):
                self.__value = val
            else:
                raise TypeError("Value must be int")

        elif self.__type == AttributeType.FLOAT:
            if isinstance(val, float):
                self.__value = val
            else:
                raise TypeError("Value must be float")

        elif self.__type == AttributeType.STR:
            if isinstance(val, str):
                self.__value = val
            else:
                raise TypeError("Value must be str")

        elif self.__type == AttributeType.DATE:
            if isinstance(val, datetime):
                self.__value = val
            else:
                raise TypeError("Value must be datetime")


    def equals(self, other):
        """
        Checks whether two attribute values are equal.

        Args:
            other: Another AttributeValue instance.

        Returns:
            bool: True if the values are equal.

        Raises:
            TypeError: If the other object is not AttributeValue or
                       if the attribute types differ.
        """
        self.__check_type_match(other)
        return self.value == other.value

    def greater_than(self, other):
        """
        Checks whether this attribute value is greater than another.

        Ordering comparison is supported only for numeric and date types.

        Args:
            other: Another AttributeValue instance.

        Returns:
            bool: True if this value is greater than the other.

        Raises:
            TypeError: If the types do not match or if ordering comparison
                       is not supported for the attribute type.
        """
        self.__check_comparable(other)
        return self.value > other.value

    def less_than(self, other):
        """
        Checks whether this attribute value is less than another.

        Ordering comparison is supported only for numeric and date types.

        Args:
            other: Another AttributeValue instance.

        Returns:
            bool: True if this value is less than the other.

        Raises:
            TypeError: If the types do not match or if ordering comparison
                       is not supported for the attribute type.
        """
        self.__check_comparable(other)
        return self.value < other.value

    def __check_type_match(self, other):
        """
        Ensures that the compared object is a compatible AttributeValue.

        Args:
            other: Object being compared.

        Raises:
            TypeError: If the object is not AttributeValue or if types differ.
        """
        if not isinstance(other, AttributeValue):
            raise TypeError("Comparison must be with AttributeValue")
        if self.type != other.type:
            raise TypeError("Cannot compare different attribute types")

    def __check_comparable(self, other):
        """
        Ensures that the attribute type supports ordering comparisons.

        Args:
            other: Another AttributeValue instance.

        Raises:
            TypeError: If ordering comparison is not supported for the type.
        """
        self.__check_type_match(other)
        if self.type not in (AttributeType.INT,
                             AttributeType.FLOAT,
                             AttributeType.DATE):
            raise TypeError("This type does not support ordering comparison")

    def __str__(self):
        """
        Returns a string representation of the attribute value.

        Returns:
            str: Formatted string containing the type and value.
        """
        return f"{self.type}:{self.value}"