import logging
from decimal import ROUND_CEILING, Decimal, getcontext
from pathlib import Path

import gemmi


def ccp4_words_to_dict(m: gemmi.Ccp4Map) -> dict:
    ctx = getcontext()
    ctx.rounding = ROUND_CEILING
    d = {}
    d["NC"], d["NR"], d["NS"] = m.header_i32(1), m.header_i32(2), m.header_i32(3)
    d["NCSTART"], d["NRSTART"], d["NSSTART"] = (
        m.header_i32(5),
        m.header_i32(6),
        m.header_i32(7),
    )
    d["xLength"] = round(Decimal(m.header_float(11)), 1)
    d["yLength"] = round(Decimal(m.header_float(12)), 1)
    d["zLength"] = round(Decimal(m.header_float(13)), 1)
    d["MAPC"], d["MAPR"], d["MAPS"] = (
        m.header_i32(17),
        m.header_i32(18),
        m.header_i32(19),
    )
    return d


def normalize_axis_order(map_object: gemmi.Ccp4Map):
    """
    Normalizes axis order to X, Y, Z (1, 2, 3)
    """
    # just reorders axis to X, Y, Z (https://gemmi.readthedocs.io/en/latest/grid.html#setup)
    map_object.setup(float("nan"), gemmi.MapSetup.ReorderOnly)
    ccp4_header = ccp4_words_to_dict(map_object)
    new_axis_order = ccp4_header["MAPC"], ccp4_header["MAPR"], ccp4_header["MAPS"]
    try:
        assert new_axis_order == (
            1,
            2,
            3,
        ), f"Axis order is {new_axis_order}, should be (1, 2, 3) or X, Y, Z"
    except AssertionError as e:
        logging.error(e, stack_info=True, exc_info=True)
    return map_object


if __name__ == "__main__":
    # read map
    INPUT_MAP_PATH = Path("preprocessor/temp/fake_ccp4_ZYX.map")
    OUTPUT_MAP_PATH = Path("preprocessor/temp/fake_ccp4_XYZ.map")
    map_object = gemmi.read_ccp4_map(str(INPUT_MAP_PATH.resolve()))
    # normalize
    normalized_map_object = normalize_axis_order(map_object=map_object)
    # write to file
    normalized_map_object.update_ccp4_header()
    OUTPUT_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    normalized_map_object.write_ccp4_map(str(OUTPUT_MAP_PATH.resolve()))
