import numpy as np
from ciftools.src.binary.encoding.data_types import DataType, DataTypeEnum
from ciftools.src.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.src.binary.encoding.encodings import EncodingEnun, RunLengthEncoding
from ciftools.src.binary.encoding.types import EncodedCIFData


class RunLengthCIFEncoder(CIFEncoderBase):
    def encode(self, data: np.ndarray) -> EncodedCIFData:
        src_data_type: DataTypeEnum = DataType.from_dtype(data.dtype)

        if not src_data_type:
            data = data.astype(dtype="i4")
            src_data_type = DataTypeEnum.Int32

        encoding: RunLengthEncoding = {"srcType": src_data_type, "kind": EncodingEnun.RunLength, "srcSize": len(data)}

        if not len(data):
            return EncodedCIFData(data=np.empty(0, dtype="i4"), encoding=[encoding])

        # adapted from https://stackoverflow.com/a/32681075
        y = data[1:] != data[:-1]  # pairwise unequal (string safe)
        pivots = np.append(np.where(y), len(data) - 1)  # must include last element posi
        run_lengths = np.diff(np.append(-1, pivots)).astype("i4")  # run lengths

        encoded_data = np.ravel([data[pivots].astype("i4"), run_lengths], "F")

        return EncodedCIFData(data=encoded_data, encoding=[encoding])


RUN_LENGTH_CIF_ENCODER = RunLengthCIFEncoder()
