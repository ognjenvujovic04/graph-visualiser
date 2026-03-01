from datetime import datetime

# String constants for different types
class AttributeType:
    INT = "int"
    FLOAT = "float"
    STR = "str"
    DATE = "date"


class AttributeValue(object):

    def __init__(self, attr_type: str, value):
        self.__type = None
        self.__value = None

        self.type = attr_type
        self.value = value

    @property
    def type(self):
        return self.__type

    @type.setter
    def type(self, value: str):
        if value in (AttributeType.INT,
                     AttributeType.FLOAT,
                     AttributeType.STR,
                     AttributeType.DATE):
            self.__type = value
        else:
            raise TypeError("Invalid attribute type")

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, val):
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
        self.__check_type_match(other)
        return self.value == other.value

    def greater_than(self, other):
        self.__check_comparable(other)
        return self.value > other.value

    def less_than(self, other):
        self.__check_comparable(other)
        return self.value < other.value

    def __check_type_match(self, other):
        if not isinstance(other, AttributeValue):
            raise TypeError("Comparison must be with AttributeValue")
        if self.type != other.type:
            raise TypeError("Cannot compare different attribute types")

    def __check_comparable(self, other):
        self.__check_type_match(other)
        if self.type not in (AttributeType.INT,
                             AttributeType.FLOAT,
                             AttributeType.DATE):
            raise TypeError("This type does not support ordering comparison")

    def __str__(self):
        return f"{self.type}:{self.value}"