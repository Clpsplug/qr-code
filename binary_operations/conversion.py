from typing import List


def convert_int_to_bool_array(number: int, bits: int) -> List:
    """
    Converts an integer into binary expression and returns it as an array
    Can specify the number of bits.

    :param number: an integer you wish to convert
    :param bits: number of bits you need
    :return: array
    """
    result = [bool(number & (1 << n)) for n in range(bits)]
    result.reverse()  # required reversing
    return result

