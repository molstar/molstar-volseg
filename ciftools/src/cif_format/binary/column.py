from typing import Union

import numpy as np
from ciftools.src.cif_format import value_presence
from ciftools.src.cif_format.base import CIFColumnBase


class BinaryCIFColumn(CIFColumnBase):
    def __getitem__(self, idx: int) -> Union[str, float, int, None]:
        if self._value_kinds and self._value_kinds[idx]:
            return None
        return self._values[idx]

    def __len__(self):
        return self.row_count

    @property
    def values(self):
        """
        A numpy array of numbers or a list of strings.
        """
        return self._values

    @property
    def value_kinds(self):
        """
        value_kinds represent the presence or absence of particular "CIF value".
        - If the mask is not set, every value is present:
            - 0 = Value is present
            - 1 = . = value not specified
            - 2 = ? = value unknown
        """
        return self._value_kinds

    def __init__(
        self,
        name: str,
        values: Union[np.ndarray, list[str]],
        value_kinds: Union[np.ndarray, None],
    ):
        self.name = name
        self._values = values
        self._value_kinds = value_kinds
        self.row_count = len(values)

    def is_defined(self) -> bool:
        pass

    def get_string(self, row: int) -> str:
        pass

    def get_integer(self, row: int) -> int:
        pass

    def get_float(self, row: int) -> float:
        pass

    def get_value_presence(self, row: int) -> value_presence:
        pass

    def are_values_equal(self, row_a: int, row_b: int) -> bool:
        pass

    def string_equals(self, row: int, value: str) -> bool:
        pass
