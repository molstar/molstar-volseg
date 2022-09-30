import numpy as np

from ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder  # type: ignore
from ciftools.binary.encoding.impl.encoders.byte_array import ByteArrayCIFEncoder  # type: ignore
from ciftools.binary.encoding.impl.encoders.delta import DeltaCIFEncoder  # type: ignore
from ciftools.binary.encoding.impl.encoders.run_length import RunLengthCIFEncoder  # type: ignore
from ciftools.binary.encoding.impl.encoders.integer_packing import IntegerPackingCIFEncoder  # type: ignore
from ciftools.binary.encoding.impl.encoders.interval_quantization import IntervalQuantizationCIFEncoder  # type: ignore
from ciftools.binary.encoding.data_types import DataTypeEnum  # type: ignore


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
    '''Encoder for coordinate data. Applies encodings: interval-quantization, delta, byte-array'''
    # num_steps, array_type = 2**32-1, DataTypeEnum.Uint32
    num_steps, array_type = 2**16-1, DataTypeEnum.Uint16  # ~0.01 voxel error - should be OK
    # num_steps, array_type = 2**8-1, DataTypeEnum.Uint8  # Too low quality

    return BinaryCIFEncoder([
        IntervalQuantizationCIFEncoder(coords.min(), coords.max(), num_steps, array_type=array_type),
        DeltaCIFEncoder(), 
        # IntegerPackingCIFEncoder(),
        ByteArrayCIFEncoder(),  # IntegerPackingCIFEncoder is a bit better but slow
    ])
