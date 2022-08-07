import numpy as np
from ciftools.src.binary.encoding.data_types import DataType, DataTypeEnum
from ciftools.src.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.src.binary.encoding.encodings import DeltaEncoding, EncodingEnun
from ciftools.src.binary.encoding.types import EncodedCIFData


class DeltaCIFEncoder(CIFEncoderBase):
    def encode(self, data: np.ndarray) -> EncodedCIFData:
        src_data_type: DataTypeEnum = DataType.from_dtype(data.dtype)

        if not src_data_type or src_data_type not in (DataTypeEnum.Int8, DataTypeEnum.Int16, DataTypeEnum.Int32):
            data = data.astype(dtype="i4")
            src_data_type = DataTypeEnum.Int32

        encoding: DeltaEncoding = {"kind": EncodingEnun.Delta, "srcType": src_data_type}

        data_length = len(data)

        if not data_length:
            encoding.origin = 0
            return EncodedCIFData(data=np.empty(0, dtype="i4"), encoding=[encoding])

        encoded_data = np.diff(data, prepend=data[0])
        encoding["origin"] = int(data[0])

        return EncodedCIFData(data=encoded_data, encoding=[encoding])


DELTA_CIF_ENCODER = DeltaCIFEncoder()
