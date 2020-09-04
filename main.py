import csv

from QR.objects import QRMatrix, TimingPattern, PositionMarker, MiniPositionMarker, FormatInfo, place_data, \
    create_8bit_data_code

if __name__ == '__main__':
    qr_matrix = QRMatrix(version=5)
    timing = TimingPattern(version=5)
    qr_matrix.overwrite_with(timing)

    qr_matrix.place(PositionMarker.create_marker_at(PositionMarker.UPPER_LEFT), 0, 0)
    qr_matrix.place(PositionMarker.create_marker_at(PositionMarker.UPPER_RIGHT), 0, -8)
    qr_matrix.place(PositionMarker.create_marker_at(PositionMarker.LOWER_LEFT), -8, 0)

    qr_matrix.place(MiniPositionMarker.create(), -9, -9)

    format_info = FormatInfo(version=5, error_level=FormatInfo.ERROR_QUALITY, mask_pattern=3)

    qr_matrix.merge(format_info)

    raw_text = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz"

    encoded_text = create_8bit_data_code(raw_text=raw_text, data_code_capacity=62)

    data_matrix = place_data(base=qr_matrix, raw_data_code=encoded_text,
                             rs_block_info=[(15, 2), (16, 2)], error_code_word_count=72,
                             mask_id=3)

    qr_matrix.merge(data_matrix)

    with open('output.csv', 'w') as fp:
        writer = csv.writer(fp)
        for i in range(qr_matrix.length):
            writer.writerow(map(lambda m: m.get_as_char(), qr_matrix.value[i, :]))
