"""Small PySide6 image-buffer helpers with no optional QtAddons dependency."""

from __future__ import annotations

import numpy as np

from core.qt_binding import configure_pyside6

configure_pyside6()

from PySide6.QtGui import QImage


def qimage_rgba_array(image: QImage) -> np.ndarray:
    """Return a read-only ``height x width x 4`` view of a Qt image.

    Qt may pad scan lines, so the view is cropped using ``bytesPerLine()``
    before it is reshaped into pixels.
    """

    ptr = image.constBits()
    rows = np.frombuffer(
        ptr,
        dtype=np.uint8,
        count=image.sizeInBytes(),
    ).reshape((image.height(), image.bytesPerLine()))
    return rows[:, : image.width() * 4].reshape(
        (image.height(), image.width(), 4)
    )


__all__ = ["qimage_rgba_array"]
