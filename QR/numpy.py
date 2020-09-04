import numpy as np

from QR.value_object import QRModule

# Defining QRModule as QRM here so that we can make it compatible with numpy ndarray.
QRM = np.dtype(QRModule)