import unittest

import msgpack
import requests
from ciftools.src.cif_format.binary.file import BinaryCIFFile
from ciftools.src.cif_format.value_presence import ValuePresenceEnum


class TestEncodings_Decoding(unittest.TestCase):
    def test(self):
        # TODO: set assert expectations

        print("mmCIF test")
        data = requests.get("https://models.rcsb.org/1tqn.bcif").content
        parsed = BinaryCIFFile.loads(data, lazy=False)

        atom_site = parsed["1TQN"].atom_site
        entity = parsed[0]["entity"]
        label_comp_id = atom_site.label_comp_id
        cartn_x = atom_site["Cartn_x"]

        print("id" in entity)  # test if field is present in category
        print("atom_site" in parsed[0])  # test if category is present data block
        print(entity.field_names)
        print(atom_site.rowCount)
        print(label_comp_id[0])
        print(label_comp_id.values[-1])
        print(len(label_comp_id.values))
        print(len(label_comp_id))
        print(cartn_x.values[0:10])
        print(atom_site["label_alt_id"].value_kinds[0] == ValuePresenceEnum.NotSpecified)
        # print([[f"_{c.name}.{f}" for f in c.field_names] for c in parsed[0].categories.values()])

        print("Volume Data test")
        data = requests.get(
            "https://ds.litemol.org/x-ray/1tqn/box/-22.367,-33.367,-21.634/-7.106,-10.042,-0.937?detail=1"
        ).content
        parsed = BinaryCIFFile.loads(msgpack.loads(data))

        print([b.header for b in parsed.data_blocks])
        print(parsed[1].categories().keys())
        print(parsed["FO-FC"].categories().keys())
        print(parsed[1]["volume_data_3d_info"].field_names)
        print(parsed[1]["volume_data_3d"].rowCount)
        print(parsed[1]["volume_data_3d"]["values"].values[0:10])
