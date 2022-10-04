import numpy as np
from ciftools.binary import encoder
from ciftools.binary.data_types import DataType, DataTypeEnum
from ciftools.binary.encoder import BinaryCIFEncoder


def bytearray_encoder(_) -> BinaryCIFEncoder:
    """Applies encodings: byte-array"""
    return encoder.BYTE_ARRAY


_DELTA_ENCODER = encoder.ComposeEncoders(encoder.DELTA, encoder.BYTE_ARRAY)


def delta_encoder(_) -> BinaryCIFEncoder:
    """Applies encodings: delta, byte-array"""
    return _DELTA_ENCODER


_DELTA_RLE_ENCODER = encoder.ComposeEncoders(encoder.DELTA, encoder.RUN_LENGTH, encoder.BYTE_ARRAY)


def delta_rl_encoder(_) -> BinaryCIFEncoder:
    """Applies encodings: delta, run-length, byte-array"""
    return _DELTA_RLE_ENCODER


_DELTA_PACK_ENCODER = encoder.ComposeEncoders(encoder.DELTA, encoder.INTEGER_PACKING)


def delta_intpack_encoder(_) -> BinaryCIFEncoder:
    """Applies encodings: delta, integer-packing"""
    return _DELTA_PACK_ENCODER


def coord_encoder(coords: np.ndarray) -> BinaryCIFEncoder:
    """Encoder for coordinate data in meshes. Applies encodings: interval-quantization, delta, byte-array"""
    # num_steps, array_type = 2**32-1, DataTypeEnum.Uint32
    num_steps, array_type = 2**16 - 1, DataTypeEnum.Uint16  # ~0.01 voxel error - should be OK
    # num_steps, array_type = 2**8-1, DataTypeEnum.Uint8  # Too low quality

    return BinaryCIFEncoder(
        [
            encoder.IntervalQuantization(coords.min(), coords.max(), num_steps, array_type=array_type),
            encoder.DELTA,
            # encoder.INTEGER_PACKING,  # TODO: test this one out
            encoder.BYTE_ARRAY,
        ]
    )


def decide_encoder(ctx: np.ndarray, data_name: str) -> tuple[BinaryCIFEncoder, np.dtype]:
    """Return an encoder appropriate for the given array and corresponding dtype"""
    data_type = DataType.from_dtype(ctx.dtype)
    typed_array = DataType.to_dtype(data_type)  # is this necessary?

    encoders: list[BinaryCIFEncoder] = []

    if data_type == DataTypeEnum.Float32 or data_type == DataTypeEnum.Float64:
        print(
            f"Encoder for {data_name} was chosen as IntervalQuantizationCIFEncoder for dataType = {str(data_type)}"
        )  # using str() to format enum nicely
        data_min: int = ctx.min(initial=ctx[0])
        data_max: int = ctx.max(initial=ctx[0])
        interval_quantization = encoder.IntervalQuantization(data_min, data_max, 255, DataTypeEnum.Uint8)
        encoders.append(interval_quantization)
    else:
        print(
            f"Encoder for {data_name} was chosen as RunLengthCIFEncoder for dataType = {str(data_type)}"
        )  # using str() to format enum nicely
        encoders.append(encoder.RUN_LENGTH)

    encoders.append(encoder.BYTE_ARRAY)

    return encoder.ComposeEncoders(*encoders), typed_array
