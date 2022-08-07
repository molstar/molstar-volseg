import abc
from typing import Optional

import numpy as np
from ciftools.src.cif_format.value_presence import ValuePresenceEnum


class CIFColumnBase(abc.ABC):
    @abc.abstractmethod
    def is_defined(self) -> bool:
        pass

    @abc.abstractmethod
    def get_string(self, row: int) -> Optional[str]:
        pass

    @abc.abstractmethod
    def get_integer(self, row: int) -> int:
        pass

    @abc.abstractmethod
    def get_float(self, row: int) -> float:
        pass

    @abc.abstractmethod
    def get_value_presence(self, row: int) -> ValuePresenceEnum:
        pass

    @abc.abstractmethod
    def are_values_equal(self, row_a: int, row_b: int) -> bool:
        pass

    @abc.abstractmethod
    def string_equals(self, row: int, value: str) -> bool:
        pass


class CIFCategoryBase(abc.ABC):
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    def row_count(self) -> int:
        pass

    @abc.abstractmethod
    def column_count(self) -> int:
        pass

    @abc.abstractmethod
    def column_names(self) -> list[str]:
        pass

    @abc.abstractmethod
    def get_column(self, name: str) -> CIFColumnBase:
        pass

    # Category Helpers

    # Extracts a  matrix from a category from a specified row_index.
    #
    # _category.matrix[1][1]: v11
    # ....
    # ....
    # _category.matrix[rows][cols]: vRowsCols
    #

    @staticmethod
    def get_matrix(self, field: str, rows: int, cols: int, row_index: int) -> np.ndarray:
        matrix = np.empty((rows, cols), float)
        for i in range(1, rows + 1):
            row = np.empty(cols)
            for j in range(1, cols + 1):
                row[j - 1] = self.get_column(field + "[" + str(i) + "][" + str(j) + "]").get_float(row_index)

            matrix[i - 1] = row

        return matrix

    # Extracts a vector from a category from a specified row_index.
    #
    # _category.matrix[1][1]: v11
    # ....
    # ....
    # _category.matrix[rows][cols]: vRowsCols
    #

    @staticmethod
    def get_vector(self, field: str, rows: int, cols: int, row_index: int) -> np.ndarray:
        vector = np.empty(rows, float)
        for i in range(1, rows + 1):
            vector[i - 1] = self.get_column(field + "[" + str(i) + "]").get_float(row_index)

        return vector


class CIFDataBlockBase(abc.ABC):
    @abc.abstractmethod
    def header(self) -> str:
        pass

    @abc.abstractmethod
    def categories(self) -> dict[str, CIFCategoryBase]:
        pass

    @abc.abstractmethod
    def get_category(self, name: str) -> CIFCategoryBase:
        pass

    @abc.abstractmethod
    def additional_data(self) -> dict:
        pass


class CIFFileBase(abc.ABC):
    @abc.abstractmethod
    def data_blocks(self) -> list[CIFDataBlockBase]:
        pass
