import numpy as np
from ciftools.src.binary.encoding.data_types import DataType, DataTypeEnum
from ciftools.src.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.src.binary.encoding.encodings import EncodingEnun, IntervalQuantizationEncoding
from ciftools.src.binary.encoding.types import EncodedCIFData


class IntervalQuantizationCIFEncoder(CIFEncoderBase):
    def __init__(self, arg_min: int, arg_max: int, num_steps: int, array_type: DataTypeEnum = DataTypeEnum.Uint32):
        self._min = arg_min
        self._max = arg_max
        self._num_steps = num_steps
        self._array_type = array_type

    def encode(self, data: np.ndarray, *args, **kwargs) -> EncodedCIFData:
        src_data_type: DataTypeEnum = DataType.from_dtype(data.dtype)

        # TODO: determine min/max from data if not set?
        if self._max < self._min:
            t = self._min
            self._min = self._max
            self._max = t

        encoding: IntervalQuantizationEncoding = {
            "min": float(self._min),
            "max": float(self._max),
            "numSteps": self._num_steps,
            "srcType": src_data_type,
            "kind": EncodingEnun.IntervalQuantization,
        }

        dtype = DataType.to_dtype(self._array_type)

        if not len(data):
            return EncodedCIFData(data=np.empty(0, dtype=dtype), encoding=[encoding])

        delta = (self._max - self._min) / (self._num_steps - 1)

        quantized = np.clip(data, self._min, self._max)
        np.subtract(quantized, self._min, out=quantized)
        np.divide(quantized, delta, out=quantized)
        np.round(quantized, 0, out=quantized)

        encoded_data = np.array(quantized, dtype=dtype)
       
        return EncodedCIFData(data=encoded_data, encoding=[encoding])
