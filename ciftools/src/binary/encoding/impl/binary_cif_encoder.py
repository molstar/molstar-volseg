from ciftools.src.binary.encoding.base.cif_encoder_base import CIFEncoderBase
from ciftools.src.binary.encoding.encodings import EncodingBase
from ciftools.src.binary.encoding.types import EncodedCIFData


class BinaryCIFEncoder:
    def __init__(self, encoders: list[CIFEncoderBase]):
        self.encoders: list[CIFEncoderBase] = encoders

    def encode_cif_data(self, data: any) -> EncodedCIFData:
        encodings: list[EncodingBase] = []

        for encoder in self.encoders:
            encoded = encoder.encode(data)
            added_encodings = encoded["encoding"]

            if not added_encodings or not len(added_encodings):
                raise ValueError("Encodings must be non-empty.")

            data = encoded["data"]
            encodings.extend(added_encodings)

        if not isinstance(data, bytes):
            raise ValueError(
                f"The encoding must result in bytes but it was {str(type(data))}. Fix your encoding chain."
            )

        return {"encoding": encodings, "data": data}

