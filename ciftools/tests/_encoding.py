import unittest
from pathlib import Path

import numpy as np
from ciftools.src.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from ciftools.src.binary.encoding.impl.encoders.delta import DELTA_CIF_ENCODER
from ciftools.src.binary.encoding.impl.encoders.fixed_point import FixedPointCIFEncoder
from ciftools.src.binary.encoding.impl.encoders.integer_packing import INTEGER_PACKING_CIF_ENCODER
from ciftools.src.binary.writer import BinaryCIFWriter
from ciftools.src.cif_format.binary.file import BinaryCIFFile
from ciftools.src.writer.base import CategoryDesc, CategoryWriter, CategoryWriterProvider, FieldDesc, OutputStream
from ciftools.src.writer.fields import number_field, string_field


class TestMetadata:
    lattices_ids: np.ndarray


class TestVolumeData:
    metadata: TestMetadata
    volume: any
    lattices: dict[int, np.ndarray]
    annotation: any


def prepare_test_data(size: int, num_lattices=2) -> TestVolumeData:
    data = TestVolumeData()
    data.lattices = dict()
    data.metadata = TestMetadata()
    data.metadata.lattices_ids = list(range(num_lattices))
    for i in data.metadata.lattices_ids:
        data.lattices[i] = np.arange(size) + i

    data.volume = np.array([0.123 + 0.1 * i for i in range(size)])
    data.annotation = [f"Annotation {i}" for i in range(size)]

    return data


class TestCategoryDesc(CategoryDesc):
    def __init__(self, name: str, fields: list[FieldDesc]):
        self.name = name
        self.fields = fields


class TestCategoryWriter(CategoryWriter):
    def __init__(self, data: TestVolumeData, count: int, category_desc: TestCategoryDesc):
        self.data = data
        self.count = count
        self.desc = category_desc


class TestCategoryWriterProvider_LatticeIds(CategoryWriterProvider):
    length: int

    def __init__(self, length: int):
        self.length = length

    def category_writer(self, ctx: TestVolumeData) -> CategoryWriter:
        field_desc: list[FieldDesc] = [
            number_field(
                name="id",
                dtype="i4",
                encoder=lambda _: BinaryCIFEncoder([INTEGER_PACKING_CIF_ENCODER]),
                value=lambda data, i: data.metadata.lattices_ids[i],
            )
        ]
        return TestCategoryWriter(ctx, self.length, TestCategoryDesc("lattice_ids", field_desc))


class TestCategoryWriterProvider_Volume(CategoryWriterProvider):
    length: int

    def __init__(self, length: int):
        self.length = length

    def category_writer(self, ctx: TestVolumeData) -> CategoryWriter:
        lattice_encoding = BinaryCIFEncoder([
            FixedPointCIFEncoder(1000), DELTA_CIF_ENCODER, INTEGER_PACKING_CIF_ENCODER
        ])

        def lattice_value_getter(lid: int):
            return lambda data, i: data.lattices[lid][i]

        fields = [
            number_field(
                name=f"lattice_{lid}",
                dtype="i4",
                encoder=lambda _: lattice_encoding,
                value=lattice_value_getter(lid),
            )
            for lid in ctx.metadata.lattices_ids
        ]
        fields.append(
            number_field(
                name=f"volume",
                dtype="f4",
                # TODO: use interval quantization
                encoder=lambda _: BinaryCIFEncoder([
                    FixedPointCIFEncoder(1000),
                    DELTA_CIF_ENCODER,
                    INTEGER_PACKING_CIF_ENCODER]
                ),
                value=lambda data, i: data.volume[i],
            )
        )
        fields.append(string_field(name="annotation", value=lambda data, i: data.annotation[i]))

        return TestCategoryWriter(ctx, self.length, TestCategoryDesc("volume", fields))


class TestOutputStream(OutputStream):
    encoded_output = None

    def write_string(self, data: str) -> bool:
        self.encoded_output = data
        return True

    def write_binary(self, data: np.ndarray) -> bool:
        self.encoded_output = data
        return True


class TestEncodings_Encoding(unittest.TestCase):
    def test(self):

        # test
        test_data = prepare_test_data(5, 3)
        # print("Original data: " + str(test_data.__dict__))

        writer = BinaryCIFWriter("my_encoder")

        # write lattice ids
        category_writer_provider = TestCategoryWriterProvider_LatticeIds(len(test_data.metadata.lattices_ids))
        writer.start_data_block("lattice_ids")
        writer.write_category(category_writer_provider, [test_data])

        # write lattices and volume
        category_writer_provider = TestCategoryWriterProvider_Volume(len(test_data.volume))
        writer.start_data_block("volume_data")
        writer.write_category(category_writer_provider, [test_data])

        # encode and flush
        writer.encode()
        output_stream = TestOutputStream()
        writer.flush(output_stream)

        encoded = output_stream.encoded_output
        (Path(__file__).parent / "lattices.bcif").write_bytes(encoded)

        # load encoded lattice ids
        parsed = BinaryCIFFile.loads(encoded, lazy=False)

        print("Decoded:")
        print("DataBlocks: " + str(len(parsed.data_blocks)))

        lattice_ids = (
            parsed.data_block("lattice_ids".upper()).get_category("lattice_ids").get_column("id").__dict__["_values"]
        )
        print("LatticeIds: " + str(lattice_ids))
        compare = np.array_equal(test_data.metadata.lattices_ids, lattice_ids)
        self.assertTrue(compare, "LatticeIds did not match original data")

        # load encoded data
        volume_and_lattices = parsed.data_block("volume_data".upper()).get_category("volume")

        print("Lattices: " + str(volume_and_lattices.column_names()))
        volume = volume_and_lattices.get_column("volume").__dict__["_values"]
        print("Volume (parsed): " + str(volume))
        print("Volume (input): " + str(test_data.volume))
        compare = np.allclose(test_data.volume, volume, atol=1e-3)
        self.assertTrue(compare, "Volume did not match original data")

        for lattice_id in lattice_ids:
            print("Lattice: " + str(lattice_id))
            lattice_value = volume_and_lattices.get_column("lattice_" + str(lattice_id)).__dict__["_values"]
            print("LatticeValue (parsed): " + str(lattice_value))
            print("LatticeValue (input): " + str(test_data.lattices[lattice_id]))
            compare = np.array_equal(test_data.lattices[lattice_id], lattice_value)
            self.assertTrue(compare, str("Lattice id " + str(lattice_id) + " did not match original data"))
