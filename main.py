import csv

from QR.objects import QRMatrix, TimingPattern, PositionMarker, MiniPositionMarker, FormatInfo, place_data, \
    create_8bit_data_code, create_alphanumeric_data_code

if __name__ == '__main__':
    qr_matrix = QRMatrix(version=2)
    timing = TimingPattern(version=2)
    qr_matrix.overwrite_with(timing)

    qr_matrix.place(PositionMarker.create_marker_at(PositionMarker.UPPER_LEFT), 0, 0)
    qr_matrix.place(PositionMarker.create_marker_at(PositionMarker.UPPER_RIGHT), 0, -8)
    qr_matrix.place(PositionMarker.create_marker_at(PositionMarker.LOWER_LEFT), -8, 0)

    qr_matrix.place(MiniPositionMarker.create(), -9, -9)

    format_info = FormatInfo(version=2, error_level=FormatInfo.ERROR_LOW, mask_pattern=7)

    qr_matrix.merge(format_info)

    raw_text = "http://srv.prof-morii.net/~lab"

    encoded_text = create_8bit_data_code(raw_text=raw_text, data_code_capacity=34)

    #encoded_text = create_alphanumeric_data_code(raw_text=raw_text, text_capacity=47, data_code_capacity=34)

    data_matrix = place_data(base=qr_matrix, raw_data_code=encoded_text,
                             rs_block_info=[(34, 1)], error_code_word_count=10,
                             mask_id=3)

    with open('output-base.csv', 'w') as fp:
        writer = csv.writer(fp)
        for i in range(qr_matrix.length):
            writer.writerow(map(lambda m: m.get_as_char(), qr_matrix.value[i, :]))

    with open('output-data.csv', 'w') as fp:
        writer = csv.writer(fp)
        for i in range(qr_matrix.length):
            writer.writerow(map(lambda m: m.get_as_char(), data_matrix.value[i, :]))

    qr_matrix.merge(data_matrix)

    with open('output.csv', 'w') as fp:
        writer = csv.writer(fp)
        for i in range(qr_matrix.length):
            writer.writerow(map(lambda m: m.get_as_char(), qr_matrix.value[i, :]))
