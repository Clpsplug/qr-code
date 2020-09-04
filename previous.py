# This is the code to make a honest-to-truth Version 1, ECL: H QR code.
# Confirmed to run in Python 3.8.
# Coded by Collapsed Plug <hsp.tosh.5200113@gmail.com>

from __future__ import annotations  # Needed to mention class itself in class / member function definition

import csv

import numpy as np

from QR.numpy import QRM
from QR.value_object import QRModule
from binary_operations.conversion import convert_int_to_bool_array

if __name__ == '__main__':

    # ↓↓↓↓↓↓↓↓↓ This is the raw text

    text = "CLPSPLUG"

    # ↑↑↑↑↑↑↑↑↑ Edit this to get different QR.

    assert len(text) < 10, "The text is too long to be encoded! It needs to be at most 10 characters long."

    # We're making Type-1 QR, which is 21x21 image.
    # since the QR is black-and-white, we just make a boolean matrix.
    # In this code, True means black, False means white.
    module_size = 21
    # Each "quiet zone (the outer white part)" is 4 blocks wide.
    total_size = 25

    # Never mind the warning on fill_value, it works.
    buffer = np.full(shape=(module_size, module_size), fill_value=QRModule.null(), dtype=QRM)
    data_buffer = np.full(shape=(module_size, module_size), fill_value=QRModule.null(), dtype=QRM)

    # Step 1. Place the pattern for detecting the position.
    # The position consists of 7x7 black, 5x5 white, 3x3 black squares
    # layered onto each other, center-aligned.

    position_marker = np.zeros(shape=(7, 7), dtype=QRM)
    marker_back = np.full(shape=(7, 7), fill_value=QRModule.on(), dtype=QRM)
    marker_middle = np.full(shape=(5, 5), fill_value=QRModule.off(), dtype=QRM)
    marker_fore = np.full(shape=(3, 3), fill_value=QRModule.on(), dtype=QRM)

    position_marker[0:7, 0:7] = marker_back
    position_marker[1:6, 1:6] = marker_middle
    position_marker[2:5, 2:5] = marker_fore

    # We are only dealing with Alphanumerics this time, which is also noted in the QR.
    # We note this by passing '0b0010' as the data mode.
    data_mode = [False, False, True, False]

    # Then we need to specify the length of the text.
    # In alphanumeric mode, this is done within 9 bits.
    length = convert_int_to_bool_array(len(text), 9)

    # We are now ready to binarize the raw data.
    # What we need here is a special conversion chart for QR code,
    # which we'll declare using a string (and substr.)
    char_id_dict = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:"

    # Then we will
    # 1. take two characters out of the raw text
    # 2. convert both characters to ids using char_id_dict
    # 3. multiply the id for the FIRST character by 45
    # 4. then add the id fot the SECOND character.
    # This will end up with 11-bit binary.
    # IF raw text contains odd number of chars,
    # the remaining character is converted to ID and represented by 6-bit binary.

    raw_text_buffer = text

    encoded_data = data_mode + length
    while True:
        # char cutout
        char_pair = raw_text_buffer[0:2]
        raw_text_buffer = raw_text_buffer[2:]

        partial_data = []
        if 2 == len(char_pair):
            # If two chars can be obtained...
            first_id = char_id_dict.find(char_pair[0])
            second_id = char_id_dict.find(char_pair[1])
            total = first_id * 45 + second_id
            partial_data = convert_int_to_bool_array(total, 11)
        else:
            # If only one char is remaining...
            char_id = char_id_dict.find(char_pair[0])
            partial_data = convert_int_to_bool_array(char_id, 6)

        encoded_data = encoded_data + partial_data
        if 0 == len(raw_text_buffer):
            break

    # If the length of the raw text is less than 16, we need to add '0000'
    for _ in range(4):
        encoded_data.append(False)

    # We then try to separate the encoded data into 8-bit slices.
    # Converting this back to integer will give us the 'DATA CODEs'
    # with which we will need to calculate the error correction code.
    count = 0
    data_codes = []
    while True:
        slice = encoded_data[8 * count:8 * (count + 1)]
        print(slice)
        if 0 == len(slice):
            break
        if 8 != len(slice):
            # insufficient slice will be padded with False
            while 8 != len(slice):
                encoded_data.append(False)  # also append to encoded data
                slice.append(False)
        total = 0
        for i in range(8):
            total += pow(2, 7 - i) if slice[i] else 0
        data_codes.append(total)
        count += 1

    # If the number of DATA CODES is less than 9 (in this case,)
    # We need to add 0b11101100 and 0b00010001 alternatively
    # until we reach the 9 data code limit.
    count = 0
    while 9 > len(data_codes):
        if 0 == count % 2:
            encoded_data = encoded_data + convert_int_to_bool_array(0xec, 8)
            data_codes.append(0xec)
        else:
            encoded_data = encoded_data + convert_int_to_bool_array(0x11, 8)
            data_codes.append(0x11)
        count += 1

    # Now, if the things were more complicated, we would've had to slice the data codes
    # into RS blocks. But since Type-1-H QR code has RS block count of 1,
    # we can skip this part.

    # Onto the error code. Type-1-H QR code has the error correction word count of 17.
    # This decides what algorithm to use.
    # This is done with something called Galois Field of 2^8.
    # with the modulo of 100011101.
    # This means that whenever 8th bit is raised, it is replaced by 00011101.

    # For simplicity, we need a comparison table for the n and the regular integer,
    # which we can create here.

    error_correction_wc = 17


    # for each data code, we divide it by g(x), which is statically defined below AS EXPONENTS.
    # the first element is for x^17. last one for x^0 = 1.
    gx_exp = [0, 43, 139, 206, 78, 43, 239, 123, 206, 214, 147, 24, 99, 150, 39, 243, 163, 136]
    # As for the f(x), we need to shift so that the final element is at x^17 (highest dim of g(x)).
    # so we just shift the whole thing by 17 ZEROs.
    fx_int = data_codes + [0] * 17
    assert 26 == len(fx_int)  # 25 dimensions == 26 elements

    while True:
        code_exp = iof[fx_int[0]]
        # First we add the exponented numbers to all the coefficient of GX.
        # This effectively does g(x) * <highest dim of f(x)>
        # We're intentionally padding with -1, which is invalid. We mark these as nonexistent terms.
        # See iof[0] for reason.
        gx_times_fx = gx_exp + [-1] * (len(fx_int) - len(gx_exp))
        for i in range(len(gx_times_fx)):
            if -1 == gx_times_fx[i]:
                continue  # Nonexistent terms should appear in the end.
            gx_times_fx[i] = (gx_times_fx[i] + code_exp) % 255
        # whose results will be XOR'd with the starting data code array
        for i in range(len(gx_times_fx)):
            # encountering negative exponent means that term is supposed not to exist.
            if -1 != gx_times_fx[i]:
                fx_int[i] = nof[gx_times_fx[i]] ^ fx_int[i]
            else:
                fx_int[i] = 0

        if fx_int[0] != 0:
            print("Oops?")
        if fx_int[-1] != 0:
            fx_int.pop(0)
            print("Calculation reached the end, exiting!")
            break
        fx_int.pop(0)

    # After the calculation, fx_int is the error code we want. Append them to the existing data codes.
    data_codes = data_codes + fx_int

    # Data Placement

    # In QR code, 1 module (pixel) means 1 bit. We first binarise the data,
    # then place the bits where they supposed to be.

    # In this example, there are only one RS block. Multiple RS blocks mean we need to interleave the data,
    # but Type-1-H does not require that.

    # How do we place the data:
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

    # First, we reserve top corner 8x8 areas and bottom-left 8x8 corner area.
    buffer[0:8, 0:8] = np.full(shape=(8, 8), fill_value=QRModule.off(), dtype=QRM)
    buffer[13:21, 0:8] = np.full(shape=(8, 8), fill_value=QRModule.off(), dtype=QRM)
    buffer[0:8, 13:21] = np.full(shape=(8, 8), fill_value=QRModule.off(), dtype=QRM)

    # Next, we place the positioning marker.
    buffer[0:7, 0:7] = position_marker
    buffer[14:21, 0:7] = position_marker
    buffer[0:7, 14:21] = position_marker

    # Then the 'Timing patterns,' which is dotted lines that exists in such ways that:
    # 1. it lines up with the bottom line of top two position markers
    # 2. lines up with the right line of two leftmost position markers

    for i in range(8, 13):
        buffer[i, 6] = QRModule.from_condition(0 == i % 2)
        buffer[6, i] = QRModule.from_condition(0 == i % 2)

    buffer[13, 8] = QRModule.on()  # For some reason, there's a stray dot here...

    # We reserve the type info as all-white.

    for i in range(9):
        buffer[i, 8] = QRModule.off() if buffer[i, 8].is_null() else buffer[i, 8]
        buffer[8, i] = QRModule.off() if buffer[8, i].is_null() else buffer[8, i]

    for i in range(13, 21):
        buffer[i, 8] = QRModule.off() if buffer[i, 8].is_null() else buffer[i, 8]
        buffer[8, i] = QRModule.off() if buffer[8, i].is_null() else buffer[8, i]

    # Only then we can place the data safely.

    # Convert each code into binary and concat them into a very long binary data.

    binary_code = []
    for code in data_codes:
        binary = convert_int_to_bool_array(code, 8)
        binary_code = binary_code + binary

    r = 20
    c = 20
    code_index = 0
    is_going_up = True
    is_on_right = False

    while True:
        is_on_right = not is_on_right
        # Place the data here
        assert buffer[r, c].is_null()
        # For masking reason, data will be saved in different place
        data_buffer[r, c] = QRModule.from_condition(binary_code[code_index])
        # increment the index
        code_index = code_index + 1

        if code_index == len(binary_code):
            break

        # Are you on the right?
        if is_on_right:
            # Try going to left... is it vacant?
            if buffer[r, c - 1].is_null():
                c = c - 1  # then it's safe to put there
                continue
            else:
                # Then try going into current vertical directions until you hit vacancy.
                while True:
                    r = r + (-1 if is_going_up else 1)
                    if buffer[r, c].is_null():
                        break
                    assert 0 <= r < 21, "You're not supposed to go out of the buffer like this."
                continue
        else:
            # You're on the left
            # Check the neighbouring block in current direction.
            checking_row = r
            while True:
                checking_row = checking_row + (-1 if is_going_up else 1)
                # if you end up running out of buffer during this process.
                # just go left and flip the direction.
                if not (0 <= checking_row < 21):
                    # But be careful not to step on other data.
                    checking_column = c - 1
                    checking_row = r
                    while True:
                        assert 0 <= checking_column < 21, "You ran out of buffer in column direction"
                        # try to find vacancy in the left column.
                        if buffer[checking_row, checking_column].is_null():
                            break
                        checking_row = checking_row - 1
                        # If for some reason there are none, we need to check next column.
                        # We preserve is_on_right at this point.
                        if not (0 <= checking_row < 21):
                            checking_column = checking_column - 1
                            checking_row = r  # reset checking row to try again
                    r = checking_row
                    c = checking_column
                    is_going_up = not is_going_up
                    break
                # See the one to the right. is it vacant?
                if buffer[checking_row, c + 1].is_null():
                    # Right one is vacant!
                    r = checking_row
                    c = c + 1
                    break
                elif buffer[checking_row, c].is_null():
                    # Left one is vacant!
                    r = checking_row
                    break
                # Else, we need to continue going up or down.
            continue

    # Masking
    # Black or white modules clumping in one place is bad because it can throw readings off.
    # Masking helps to alleviate that. (note: the position marker, timing marker, type info are NOT masked)
    # There are 8 predefined masking pattern, which flips bits based on the coordinate of the module.
    # What we do here is that we apply mask first, then 'penalize' each results based on rules.
    # The pattern with the least penalty wins, and used as an output.

    # We'll just use mask pattern 3 (0b011). if (row + column) % 3 == 0, flip

    for r in range(21):
        for c in range(21):
            if 0 == (r + c) % 3:
                data_buffer[r, c].flip()

    # Type information
    # Type information is 15 bits long.
    # We're going to use error level H, which has the value of 2 (0b10).

    metadata = convert_int_to_bool_array(0b10, 2)

    # Then we append the mask number...
    metadata = metadata + convert_int_to_bool_array(0b011, 3)

    # and this 5-bit data is also error-coded by 10-bit code.
    meta_fx = list(map(lambda b: 1 if b else 0, metadata)) + [0] * 10
    meta_gx = [1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1]

    # Perform f(x) / g(x)
    while True:

        end_flag = False
        while 0 == meta_fx[0]:
            meta_fx.pop(0)
            if len(meta_fx) < len(meta_gx):
                end_flag = True
                break

        if end_flag:
            break

        for i in range(len(meta_gx)):
            meta_fx[i] = meta_fx[i] ^ meta_gx[i]

    # Error code is appended to metadata
    metadata = metadata + list(map(lambda i: True if i == 1 else False, meta_fx))

    # Then it is XOR'd with 0b101010000010010
    # 0b 0101 0100 0001 0010 == 0x5412
    meta_xor_array = convert_int_to_bool_array(0x5412, 15)
    for i in range(len(metadata)):
        metadata[i] = metadata[i] ^ meta_xor_array[i]

    # Those bits are mapped in VERY SPECIFIC PLACES.
    for i in range(6):
        buffer[8, i] = QRModule.from_condition(metadata[i])
        buffer[i, 8] = QRModule.from_condition(metadata[i])

    for i in range(7):
        buffer[8, 14 + i] = QRModule.from_condition(metadata[i + 8])
        buffer[-i, 8] = QRModule.from_condition(metadata[i])

    buffer[8, 7] = QRModule.from_condition(metadata[8])
    buffer[8, 8] = QRModule.from_condition(metadata[7])
    buffer[7, 8] = QRModule.from_condition(metadata[6])

    # Finally, merge the two buffers to get the QR code!

    for r in range(21):
        for c in range(21):
            if buffer[r, c].is_null():
                if data_buffer[r, c].is_null():
                    raise ValueError("Both buffers are null at {}, {}".format(r, c))
                buffer[r, c] = data_buffer[r, c]
            else:
                if not data_buffer[r, c].is_null():
                    raise ValueError("Module collision!")

    with open('output.csv', 'w') as fp:
        writer = csv.writer(fp)
        for i in range(21):
            writer.writerow(map(lambda m: m.get_as_char(), buffer[i, :]))
