from typing import Union

import msgpack
import numpy as np
from ciftools.src.cif_format.base import CIFFileBase
from ciftools.src.cif_format.binary.file import BinaryCIFFile


class BinaryCifParser:
    @staticmethod
    def __checkVersions(min_ver: list[int], current_ver: list[int]):
        for i in range(2):
            if min_ver[i] > current_ver[i]:
                return False

        return True

    @staticmethod
    def parse(data: Union[np.ndarray, bytes, list]) -> CIFFileBase:
        # min_version = [0, 3]

        try:
            array = bytes(data)

            unpacked = msgpack.loads(array)
            # TODO: check min version
            # if not __checkVersions(min_version, unpacked.version.match(/(\d)\.(\d)\.\d/).slice(1))) {
            #    return ParserResult.error<CIFTools.File>(`Unsupported format version. Current ${unpacked.version}, required ${minVersion.join('.')}.`);
            # }
            file = BinaryCIFFile(unpacked)
            return file

        except Exception:
            raise
