from __future__ import annotations  # Needed to mention class itself in class / member function definition


class QRModule(object):
    """
    A "Pixel" in regular QR codes.
    For processing convenience, we also introduce the 'NULL' value.
    The NULL value should not appear in the final product.
    """

    null_value = -1
    off_value = 0
    on_value = 1

    def __init__(self, value):
        """
        Constructor
        :param value: -1, 0, or 1
        """
        if value not in [self.null_value, self.off_value, self.on_value]:
            raise ValueError("Cannot take other than 0, 1, 2!")
        self.value = value

    def is_null(self) -> bool:
        """
        Returns true if this module is null (not assigned.)

        :return: bool True if not assigned.
        """
        return self.null_value == self.value

    def is_black(self) -> bool:
        """
        Returns true if this module is black (bit == 1.)

        :return: bool True if this module has raised bit
        """
        return self.on_value == self.value

    def flip(self):
        """
        Flips the bit of this module. Will do nothing if this module is not assigned (null.)
        """
        if self.on_value == self.value:
            self.value = self.off_value
        elif self.off_value == self.value:
            self.value = self.on_value

    def get_as_char(self):
        if self.on_value == self.value:
            return 'B'
        elif self.off_value == self.value:
            return 'W'
        else:
            return 'N'

    @staticmethod
    def on() -> QRModule:
        """
        Gets a module with its bit raised

        :return: QRModule, Black module
        """
        return QRModule(QRModule.on_value)

    @staticmethod
    def off() -> QRModule:
        """
        Gets a module with its bit not raised

        :return: QRModule, White module
        """
        return QRModule(QRModule.off_value)

    @staticmethod
    def null() -> QRModule:
        """
        Gets an unassigned module

        :return: QRModule, bit unassigned
        """
        return QRModule(QRModule.null_value)

    @staticmethod
    def from_condition(condition: bool) -> QRModule:
        """
        Creates QRModule from the condition given.
        Will NOT return null module.

        :param condition: bool, condition. Can be an expression.
        :return: QRModule, if condition is True, returns on(). else, off().
        """
        return QRModule.on() if condition else QRModule.off()

    def __xor__(self, other: QRModule):
        if self.null_value == self.value or self.null_value == other.value:
            raise ValueError("Tried to compare with NULL!")
        return self.value != other.value

    def __str__(self):
        if self.null_value == self.value:
            return "NULL"
        elif self.off_value == self.value:
            return "WHITE"
        elif self.on_value == self.value:
            return "BLACK"
        else:
            raise ValueError("Invalid value")

    def __repr__(self):
        return self.__str__()
