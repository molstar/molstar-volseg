import numpy as np

from ciftools.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.binary.encoding.data_types import DataType, DataTypeEnum
from ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.binary.encoding.impl.encoders.byte_array import ByteArrayCIFEncoder
from ciftools.binary.encoding.impl.encoders.delta import DeltaCIFEncoder
from ciftools.binary.encoding.impl.encoders.run_length import RunLengthCIFEncoder
from ciftools.binary.encoding.impl.encoders.integer_packing import IntegerPackingCIFEncoder
from ciftools.binary.encoding.impl.encoders.interval_quantization import IntervalQuantizationCIFEncoder


def bytearray_encoder(_) -> BinaryCIFEncoder:
    '''Applies encodings: byte-array'''
    return BinaryCIFEncoder([
        ByteArrayCIFEncoder(),
    ])


def delta_encoder(_) -> BinaryCIFEncoder:
    '''Applies encodings: delta, byte-array'''
    return BinaryCIFEncoder([
        DeltaCIFEncoder(), 
        ByteArrayCIFEncoder(),
    ])


def delta_rl_encoder(_) -> BinaryCIFEncoder:
    '''Applies encodings: delta, run-length, byte-array'''
    return BinaryCIFEncoder([
        DeltaCIFEncoder(), 
        RunLengthCIFEncoder(),
        ByteArrayCIFEncoder(),
    ])


def delta_intpack_encoder(_) -> BinaryCIFEncoder:
    '''Applies encodings: delta, integer-packing'''
    return BinaryCIFEncoder([
        DeltaCIFEncoder(), 
        IntegerPackingCIFEncoder(),
    ])


def coord_encoder(coords: np.ndarray) -> BinaryCIFEncoder:
    '''Encoder for coordinate data in meshes. Applies encodings: interval-quantization, delta, byte-array'''
    # num_steps, array_type = 2**32-1, DataTypeEnum.Uint32
    num_steps, array_type = 2**16-1, DataTypeEnum.Uint16  # ~0.01 voxel error - should be OK
    # num_steps, array_type = 2**8-1, DataTypeEnum.Uint8  # Too low quality

    return BinaryCIFEncoder([
        IntervalQuantizationCIFEncoder(coords.min(), coords.max(), num_steps, array_type=array_type),
        DeltaCIFEncoder(), 
        # IntegerPackingCIFEncoder(),
        ByteArrayCIFEncoder(),  # IntegerPackingCIFEncoder is a bit better but slow
    ])


def decide_encoder(ctx: np.ndarray, data_name: str) -> tuple[BinaryCIFEncoder, np.dtype]:
    '''Return an encoder appropriate for the given array and corresponding dtype'''
    data_type = DataType.from_dtype(ctx.dtype)
    typed_array = DataType.to_dtype(data_type)  # is this necessary?

    encoders: list[CIFEncoderBase] = []

    if data_type == DataTypeEnum.Float32 or data_type == DataTypeEnum.Float64:
        print(f"Encoder for {data_name} was chosen as IntervalQuantizationCIFEncoder for dataType = {str(data_type)}")  # using str() to format enum nicely
        data_min: int = ctx.min(initial=ctx[0])
        data_max: int = ctx.max(initial=ctx[0])
        interval_quantization = IntervalQuantizationCIFEncoder(data_min, data_max, 255, DataTypeEnum.Uint8)
        encoders.append(interval_quantization)
    else:
        print(f"Encoder for {data_name} was chosen as RunLengthCIFEncoder for dataType = {str(data_type)}")  # using str() to format enum nicely
        encoders.append(RunLengthCIFEncoder())
    
    encoders.append(ByteArrayCIFEncoder())

    return BinaryCIFEncoder(encoders), typed_array
