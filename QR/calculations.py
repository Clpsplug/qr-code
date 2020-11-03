"""
Calculations needed for constructing QR codes.

Special rule in this file:
Hungarian notations is practiced here if galois field calculation is involved.
e_ means exponential notation (alpha^x), and i_ means plain-old integer notation (n).
"""
import copy
from typing import List
import numpy as np

gf_s = 0x1d
gf_n = 1

i_from_e = np.zeros(shape=256, dtype=int)  # is the exponent (index) to integer (value) conversion
e_from_i = np.zeros(shape=256, dtype=int)  # is the integer (index) to exponent (value) conversion

for i in range(255):
    i_from_e[i] = gf_n % 256
    e_from_i[gf_n] = i

    gf_n = gf_n << 1
    gf_n = ((gf_n >> 8) * gf_s) ^ (gf_n & 0xff)
e_from_i[0] = -1  # integer 0 cannot be mapped anywhere. So, if -1 is encountered, mark as invalid.
i_from_e[255] = gf_n % 256


def i_galois_division(i_fx_input: List, e_gx: List) -> List:
    """
    Performs GF(2^8) division.

    :param i_fx_input:
    :param e_gx:
    :return: 
    """

    # REQUIRED deepcopy to cut the reference.
    i_fx = copy.deepcopy(i_fx_input)

    print(' '.join("{0}".format(n) for n in i_fx))
    i_gx = []
    for e in e_gx:
        i_gx.append(i_from_e[e])
    print(' '.join("{0}".format(n) for n in i_gx))

    while True:
        e_code = e_from_i[i_fx[0]]
        # First we add the exponented numbers to all the coefficient of GX.
        # This effectively does g(x) * <highest dim of f(x)>
        # We're intentionally padding with -1, which is invalid. We mark these as nonexistent terms.
        # See iof[0] for reason.
        e_gx_times_fx = e_gx + [-1] * (len(i_fx) - len(e_gx))
        for j in range(len(e_gx_times_fx)):
            if -1 == e_gx_times_fx[j]:
                continue  # Nonexistent terms should appear in the end.
            e_gx_times_fx[j] = (e_gx_times_fx[j] + e_code) % 255
        # whose results will be XOR'd with the starting data code array
        for j in range(len(e_gx_times_fx)):
            # encountering negative exponent means that term is supposed not to exist.
            if -1 != e_gx_times_fx[j]:
                i_fx[j] = i_from_e[e_gx_times_fx[j]] ^ i_fx[j]
            else:
                i_fx[j] = 0

        if i_fx[0] != 0:
            print("Oops? This may indicate a calculation failure.")
        if i_fx[-1] != 0:
            i_fx.pop(0)
            print("Calculation reached the end, exiting!")
            break
        i_fx.pop(0)

    return i_fx


def i_pad_codes(input_array: List, max_dim_of_gx: int) -> List:
    # REQUIRED deepcopy to cut the reference.
    result = copy.deepcopy(input_array)
    return result + [0] * max_dim_of_gx


def bch_15_5_division(fx_input: List) -> List:
    # REQUIRED deepcopy to cut the reference.
    fx = copy.deepcopy(fx_input)

    fx = i_pad_codes(fx, 10)

    # this is a constant
    gx = [1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1]

    # Perform f(x) / g(x)
    while True:

        end_flag = False
        while 0 == fx[0]:
            fx.pop(0)
            if len(fx) < len(gx):
                end_flag = True
                break

        if end_flag:
            break

        for i in range(len(gx)):
            fx[i] = fx[i] ^ gx[i]

    return fx


class MaskPattern:
    data = {
        0: lambda r, c: 0 == (r + c) % 2,
        1: lambda r, c: 0 == r % 2,
        2: lambda r, c: 0 == c % 3,
        3: lambda r, c: 0 == (r + c) % 3,
        4: lambda r, c: 0 == ((r // 2) + (c // 3)) % 2,
        5: lambda r, c: 0 == ((r * c) % 2) + ((r * c) % 3),
        6: lambda r, c: 0 == (((r * c) % 2) + ((r * c) % 3)) % 2,
        7: lambda r, c: 0 == (((r * c) % 3 + ((r + c) % 2)) % 2)
    }

    @staticmethod
    def calculate(r, c, pattern_id: int) -> bool:
        return MaskPattern.data[pattern_id](r, c)


class GaloisDividerDictionary:
    data = {
        7: [0, 87, 229, 146, 149, 238, 102, 21],
        10: [0, 251, 67, 46, 61, 118, 70, 64, 94, 32, 45],
        13: [0, 74, 152, 176, 100, 86, 100, 106, 104, 130, 218, 206, 140, 78],
        16: [0, 120, 104, 107, 109, 102, 161, 76, 3, 91, 191, 147, 169, 182, 194, 225, 120],
        17: [0, 43, 139, 206, 78, 43, 239, 123, 206, 214, 147, 24, 99, 150, 39, 243, 163, 136],
        18: [0, 215, 234, 158, 94, 184, 97, 118, 170, 79, 187, 152, 148, 252, 179, 5, 98, 96, 153],
        22: [0, 210, 171, 247, 242, 93, 230, 14, 109, 221, 53, 200, 74, 8, 172, 98, 80, 219, 134, 160, 105, 165, 231],
        28: [0, 168, 223, 200, 104, 224, 234, 108, 180, 110, 190, 195, 147, 205, 27, 232, 201, 21, 43, 245, 87, 42, 195,
             212, 119, 242, 37, 9, 123],
    }

    @staticmethod
    def get_divider_for(error_word_count: int) -> List:
        return GaloisDividerDictionary.data[error_word_count]
