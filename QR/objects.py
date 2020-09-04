"""
QR 'Objects' (set of modules)
"""
from __future__ import annotations  # Needed to mention class itself in class / member function definition

import copy
from typing import List

import numpy as np

from QR.calculations import bch_15_5_division, i_galois_division, i_pad_codes, GaloisDividerDictionary, MaskPattern
from QR.numpy import QRM
from QR.value_object import QRModule
from binary_operations.conversion import convert_int_to_bool_array


class QRMatrix:
    """
    QR Matrix.
    """

    def __init__(self, version: int):
        """
        Creates an empty QR matrix.
        Version 1 ~ 40 are possible, and an increase in version means 4 more modules
        along the sides, starting from 21 modules at version 1.
        But for simplicity, we only allow up to version 6 (mini position marker is the pain in the a**)
        :param version:  1 ~ 6
        :return: 2-D np.ndarray of QRModule at specified size.
        """
        if not (1 <= version <= 6):
            raise ValueError("Version out of range. It should be between 1 and 40.")

        self.version = version
        self.length = 17 + version * 4
        self.value = np.full(shape=(self.length, self.length), fill_value=QRModule.null(), dtype=QRM)

    def merge(self, other: QRMatrix, allow_empties: bool = True):
        """
        Merges two QRMatrices. This method mutates _this_ QRMatrix.
        :param other:
        :param allow_empties: Default True. False to check for holes in merge result.
        :return: nothing, but mutates _this_ QRMatrix.
        """
        if self.length != other.length:
            raise ValueError("Matrix size mismatch! This: {}, Other: {}".format(self.length, other.length))
        for r in range(self.length):
            for c in range(self.length):
                if self.value[r, c].is_null():
                    if (not allow_empties) and other.value[r, c].is_null():
                        raise ValueError("Both buffers are null at {}, {} when you didn't allow it.".format(r, c))
                    self.value[r, c] = other.value[r, c]
                else:
                    if not other.value[r, c].is_null():
                        raise ValueError("Module collision.")

    def overwrite_with(self, other: QRMatrix):
        """
        Overwrites THIS QRMatrix with other QRMatrix..
        :param other:
        :return:
        """
        if self.length != other.length:
            raise ValueError("Matrix size mismatch! This: {}, Other: {}".format(self.length, other.length))

        for r in range(self.length):
            for c in range(self.length):
                # Unless the other module is null, overwrite with other.
                self.value[r, c] = self.value[r, c] if other.value[r, c].is_null() else other.value[r, c]

    def place(self, object: np.ndarray, row: int, column: int):
        """
        Places other 2-d ndarray onto this QRMatrix, OVERWRITING WHAT WAS THERE.
        :param column:
        :param object:
        :return:
        """

        if 2 != object.ndim:
            raise ValueError("object to place NOT 2-D.")

        size = object.shape

        if row < 0:
            row += self.length
        if column < 0:
            column += self.length

        self.value[row: row + size[0], column:column + size[1]] = object


class PositionMarker:
    """
    A static collection of position markers.
    """

    UPPER_LEFT = 0
    UPPER_RIGHT = 1
    LOWER_LEFT = 2

    @staticmethod
    def get_marker_body() -> np.ndarray:
        position_marker = np.full(shape=(7, 7), fill_value=QRModule.null(), dtype=QRM)
        marker_back = np.full(shape=(7, 7), fill_value=QRModule.on(), dtype=QRM)
        marker_middle = np.full(shape=(5, 5), fill_value=QRModule.off(), dtype=QRM)
        marker_fore = np.full(shape=(3, 3), fill_value=QRModule.on(), dtype=QRM)

        position_marker[0:7, 0:7] = marker_back
        position_marker[1:6, 1:6] = marker_middle
        position_marker[2:5, 2:5] = marker_fore

        return position_marker

    @staticmethod
    def create_marker_at(position: int) -> np.ndarray:
        result = np.full(shape=(8, 8), fill_value=QRModule.off(), dtype=QRM)
        if PositionMarker.UPPER_LEFT == position:
            result[0:7, 0:7] = PositionMarker.get_marker_body()
        elif PositionMarker.UPPER_RIGHT == position:
            result[0:7, 1:8] = PositionMarker.get_marker_body()
        elif PositionMarker.LOWER_LEFT == position:
            result[1:8, 0:7] = PositionMarker.get_marker_body()
        else:
            raise ValueError("position out of range")

        return result


class MiniPositionMarker:
    """
    Mini-sized position marker that needs to be present in QR codes version > 1.
    For 2 <= version <= 6, it's placed at [-9:-4, -9:-4].
    """

    @staticmethod
    def create() -> np.ndarray:
        mini_position_marker = np.full(shape=(5, 5), fill_value=QRModule.null(), dtype=QRM)
        outer = np.full(shape=(5, 5), fill_value=QRModule.on(), dtype=QRM)
        inner = np.full(shape=(3, 3), fill_value=QRModule.off(), dtype=QRM)
        center = np.full(shape=(1, 1), fill_value=QRModule.on(), dtype=QRM)
        mini_position_marker[0:5, 0:5] = outer
        mini_position_marker[1:4, 1:4] = inner
        mini_position_marker[2:3, 2:3] = center
        return mini_position_marker


class TimingPattern(QRMatrix):
    """
    Timing pattern. This is a fixed pattern
    """

    def __init__(self, version: int):
        super().__init__(version)
        # This code writes timing pattern where it's not supposed to,
        # but we'll overwrite afterwards
        for r in range(self.length):
            self.value[r, 6] = QRModule.from_condition(0 == r % 2)
        for c in range(self.length):
            self.value[6, c] = QRModule.from_condition(0 == c % 2)

        # and also THIS RANDOM STRAY BLACK MODULE HERE.
        self.value[-8, 8] = QRModule.on()


class FormatInfo(QRMatrix):
    """
    Format information.
    """

    ERROR_LOW = 1
    ERROR_MEDIUM = 0
    ERROR_QUALITY = 3
    ERROR_HIGH = 2

    def __init__(self, version: int, error_level: int, mask_pattern: int):
        """
        Creates Format-info-filled QRMatrix.

        :param version:
        :param error_level:
        :param mask_pattern:
        """
        super(FormatInfo, self).__init__(version)

        type_info = convert_int_to_bool_array(error_level, 2)
        type_info = type_info + convert_int_to_bool_array(mask_pattern, 3)

        error_code_list = bch_15_5_division(type_info)
        type_info = type_info + list(map(lambda i: True if i == 1 else False, error_code_list))

        type_info_xor_array = convert_int_to_bool_array(0x5412, 15)
        for i in range(len(type_info)):
            type_info[i] = type_info[i] ^ type_info_xor_array[i]

        # Those bits are mapped in VERY SPECIFIC PLACES.
        for i in range(6):
            # Below upper left position marker
            self.value[8, i] = QRModule.from_condition(type_info[i])
            # Left of the upper left position marker
            self.value[i, 8] = QRModule.from_condition(type_info[14 - i])

        for i in range(7):
            # Below the upper right position marker
            self.value[8, -i - 1] = QRModule.from_condition(type_info[14 - i])
            # Right of the lower left position marker
            self.value[-i - 1, 8] = QRModule.from_condition(type_info[i])

        self.value[8, -8] = QRModule.from_condition(type_info[7])

        self.value[7, 8] = QRModule.from_condition(type_info[8])
        self.value[8, 8] = QRModule.from_condition(type_info[7])
        self.value[8, 7] = QRModule.from_condition(type_info[6])


def create_8bit_data_code(raw_text: str, data_code_capacity: int) -> List:
    length = len(raw_text)
    header = convert_int_to_bool_array(0x4, 4)
    header += convert_int_to_bool_array(length, 8)
    text_ascii_bytes = []
    for char in raw_text:
        text_ascii_bytes += convert_int_to_bool_array(ord(char), 8)
    text_ascii_bytes += convert_int_to_bool_array(0, 4)

    total_bits = header + text_ascii_bytes

    count = 0
    data_codes = []
    while True:
        slice = total_bits[8 * count:8 * (count + 1)]
        if 0 == len(slice):
            break
        total = 0
        for i in range(8):
            total += pow(2, 7 - i) if slice[i] else 0
        data_codes.append(total)
        count += 1

    count = 0
    while data_code_capacity > len(data_codes):
        if 0 == count % 2:
            # encoded_data = encoded_data + convert_int_to_bool_array(0xec, 8)
            data_codes.append(0xec)
        else:
            # encoded_data = encoded_data + convert_int_to_bool_array(0x11, 8)
            data_codes.append(0x11)
        count += 1

    return data_codes


def place_data(base: QRMatrix, raw_data_code: List, rs_block_info: List, error_code_word_count: int,
               mask_id: int) -> QRMatrix:
    """
    Places data on QRMatrix, and RETURNS DATA PART ONLY.
    :param mask_id:
    :param error_code_word_count:
    :param base: Base QRMatrix, THIS HAS TO HAVE ALL THE NECESSARY MODULES READY!!
    :param raw_data_code: RAW DATA, DO NOT INCLUDE ERROR CORRECTING CODES!
    :param rs_block_info: List of Tuple of (RS block data code count, number of that RS blocks.)
    :return:
    """

    data_code = copy.deepcopy(raw_data_code)

    rs_blocks = []

    # split the data code according to the RS block information.
    current_index = 0
    for info in rs_block_info:
        word_count = info[0]
        repeat_count = info[1]
        for _ in range(repeat_count):
            rs_blocks.append(data_code[current_index:current_index + word_count])
            current_index = current_index + word_count

    # For each data code, calculate the error codes.
    gx_word_count = int(error_code_word_count / len(rs_blocks))
    rs_block_error_codes = []
    for rs_block in rs_blocks:
        i_fx = copy.deepcopy(rs_block)
        i_fx = i_pad_codes(i_fx, gx_word_count)
        rs_block_error_codes.append(i_galois_division(i_fx, GaloisDividerDictionary.get_divider_for(gx_word_count)))

    binary_code = []
    # First, interleave all the rs_blocks.
    code_index = 0
    while True:
        continue_count = 0
        for block_id in range(len(rs_blocks)):
            if code_index >= len(rs_blocks[block_id]):
                # earlier RS blocks may run out of data code at the end. in such case, carry on.
                continue_count += 1
                continue
            binary = convert_int_to_bool_array(rs_blocks[block_id][code_index], 8)
            binary_code += binary
        if continue_count == len(rs_blocks):
            break
        code_index += 1

    error_area_start_index = len(binary_code)

    # Then, we interleave all the rs_block_error_codes.
    code_index = 0
    while True:
        continue_count = 0
        for block_id in range(len(rs_block_error_codes)):
            if code_index >= len(rs_block_error_codes[block_id]):
                continue_count += 1
                continue
            binary = convert_int_to_bool_array(rs_block_error_codes[block_id][code_index], 8)
            binary_code += binary
        if continue_count == len(rs_block_error_codes):
            break
        code_index += 1

    data_buffer = QRMatrix(version=base.version)

    # How we place the data:
    # we start from bottom right. Then we decide which vertical direction to 'go when the situation requires first.'
    # (you can pick from up and down. We'll go UP this time)
    # After placing a bit in bottom right corner, we look at the two columns
    # (the one that you put the data + the one to the left.)
    # If you are currently on the right:
    #   Try going LEFT. BUT if the fixed pattern is already sitting there,
    #   You need to go whichever vertical direction you're going.
    #   If this is the first one it's probably UP in this case
    # If you are currently on the left:
    #   Look at the block to the current vertical direction.
    #   If the block is vacant...
    #       Go in that direction. If the right neighbour is vacant, place there. if not, place it here.
    #   If the block is taken...
    #       Try looking at the next neighbour in the current vertical direction. Do the same.
    #       If you ran out of the space...
    #           Give up going in the direction, go LEFT and place the bit there.
    #           This ALSO causes the VERTICAL DIRECTION to FLIP!

    # we have created `buffer` all the way up.
    # FIRST INDEX IS DOWN, SECOND INDEX IS RIGHT.

    r = base.length - 1
    c = base.length - 1
    code_index = 0
    is_going_up = True
    is_on_right = True

    while True:
        if code_index == error_area_start_index:
            print("Error area is starting from row-wise {}, column-wise {}. We're going {} at this point".format(r, c,
                                                                                                                 "up" if is_going_up else "down"))
        # Place the data here
        assert base.value[r, c].is_null()
        # For masking reason, data will be saved in different place
        data_buffer.value[r, c] = QRModule.from_condition(binary_code[code_index])
        # increment the index
        code_index = code_index + 1

        if code_index == len(binary_code):
            break

        # Are you on the right?
        if is_on_right:
            # Try going to left... is it vacant?
            if base.value[r, c - 1].is_null():
                c = c - 1  # then it's safe to put there
                is_on_right = False
                continue
            else:
                # Then try going into current vertical directions until you hit vacancy.
                while True:
                    r = r + (-1 if is_going_up else 1)
                    if base.value[r, c].is_null():
                        break
                    assert 0 <= r < base.length, "You're not supposed to go out of the buffer like this."
                continue
        else:
            # You're on the left
            # Check the neighbouring block in current direction.
            checking_row = r
            while True:
                checking_row = checking_row + (-1 if is_going_up else 1)
                # if you end up running out of buffer during this process.
                # just go left and flip the direction. You're considered to be on right after this.
                if not (0 <= checking_row < base.length):
                    # But be careful not to step on other data.
                    checking_column = c - 1
                    checking_row = r
                    while True:
                        assert 0 <= checking_column < base.length, "You ran out of buffer in column direction"
                        # try to find vacancy in the next left column.
                        if base.value[checking_row, checking_column].is_null():
                            break
                        checking_row = checking_row - 1
                        # If for some reason there are none, we need to check next column.
                        # We preserve is_on_right at this point.
                        if not (0 <= checking_row < base.length):
                            checking_column = checking_column - 1
                            checking_row = r  # reset checking row to try again
                    r = checking_row
                    c = checking_column
                    is_going_up = not is_going_up
                    is_on_right = True
                    break
                # See the one to the right. is it vacant?
                if base.value[checking_row, c + 1].is_null():
                    # Right one is vacant!
                    r = checking_row
                    c = c + 1
                    is_on_right = True
                    break
                elif base.value[checking_row, c].is_null():
                    # Left one is vacant!
                    r = checking_row
                    is_on_right = False
                    break
                # Else, we need to continue going up or down.
            continue

    # return data_buffer
    for r in range(base.length):
        for c in range(base.length):
            # Some modules may not be used (e.g. Ver.5-Q, Binary mode.)
            # 'True vacancy,' which is occupied by neither data nor metadata,
            # seems to be treated as ON module - but we don't know for sure.
            if base.value[r, c].is_null() and data_buffer.value[r, c].is_null():
                data_buffer.value[r, c] = QRModule.on()
            if MaskPattern.calculate(r, c, mask_id):
                data_buffer.value[r, c].flip()

    return data_buffer
