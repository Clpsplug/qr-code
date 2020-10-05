from QR.objects import FormatInfo

if __name__ == '__main__':
    sequence = input("Type in the first five modules of the type info without delimiters. Black = 1, White = 0")

    if 5 != len(sequence):
        print("You must type in the module values without delimiters e.g. 01001")
        exit(1)

    modules = []
    for char in sequence:
        if char == "0":
            modules.append(False)
        elif char == "1":
            modules.append(True)
        else:
            print("Invalid char {}".format(char))
            exit(1)

    xor = [True, False, True, False, True]

    restored = []
    for i in range(5):
        restored.append(modules[i] ^ xor[i])

    error_type = 2 * (1 if restored[0] else 0) + 1 * (1 if restored[1] else 0)
    mask_type = 4 * (1 if restored[2] else 0) + 2 * (1 if restored[3] else 0) + 1 * (1 if restored[4] else 0)

    print("Error type: {}, Mask ID: {}".format(FormatInfo.get_name_from_error_type(error_type), mask_type))
