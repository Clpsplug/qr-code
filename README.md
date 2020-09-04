# WARNING: NOT FOR PRODUCTION USE AT ALL

***Do NOT use this repository in hopes to generating QR codes for productions***, this is untested and buggy af!

# qr-code

Me trying to understand how generating QR code works,
in search for making ["Fake QR codes" that can hold multiple data](https://ieeexplore.ieee.org/abstract/document/8594762/).

# usage

1. run main.py and get `output.csv`
2. using a spreadsheet program such as Excel, conditional format each cell so that:
  * cells with 'B' are painted black
  * cells with 'W' are painted white, while painting the letter white.
3. Try reading the QR with a device of your preference e.g. your smartphone camera.

As of writing this README, this code will create a csv file (`output.csv`) that depicts a QR code with the following properties:

|info|data|
|:--|:--|
|encoded data|`abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz`|
|version|5|
|error correcting strength|Q (`0b11`)|
|mode|ascii|
|mask pattern|3 (`0b011`)|

(information above is subject to change very frequently as the development continues)

# Acknowledgements

Huge thanks for [this page (Japanese only)](http://www.swetake.com/qrcode/qr1.html) for step-by-step generation tutorial.


# TODO

* Automatic mask decision
  * Mask ID has to be decided by actually applying masks and analyzing them with a certain cost function.
* Hold as much constant data as possible
  * version specs (data code word count, error correcting code word count, RS block length & count)
  * divider in GF(2^8) (P(x) = x^8 + x^4 + x^3 + x^2 + 1) for error correcting code generation.
* Automatic version decision


# Known issues

* ***Extremely* buggy.**
* There are versions that do NOT work.
  * Version 2, error correcting strength L QR codes has wrong error correction data.
