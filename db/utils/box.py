from typing import Tuple

import numpy as np


def normalize_box(
    box: Tuple[Tuple[int, int, int], Tuple[int, int, int]]
) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
    """Normalizes box so that first point is less than 2nd with respect to X, Y, Z"""
    p1 = box[0]
    p2 = box[1]

    new_p1 = tuple(np.minimum(p1, p2))
    new_p2 = tuple(np.maximum(p1, p2))

    return (new_p1, new_p2)
