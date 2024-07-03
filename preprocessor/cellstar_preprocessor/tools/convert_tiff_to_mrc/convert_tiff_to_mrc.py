import subprocess
from pathlib import Path
from typing import Literal

from PIL import Image

Image.MAX_IMAGE_PIXELS = None


def _convert_tiff_32_to_16_bit(tiff_path_32_bit: Path, tiff_path_16_bit: Path):
    f32 = Image.open(str(tiff_path_32_bit.resolve()))
    f32.convert("I;16").save(str(tiff_path_16_bit.resolve()))


# Prerequisite - imod
def _get_tiff_pathes(tiff_dir: Path):
    tiff: list[Path] = sorted(list(tiff_dir.glob("*.tiff")))
    tif: list[Path] = sorted(list(tiff_dir.glob("*.tif")))
    p = tiff + tif
    return p


def convert_tiff_to_mrc(
    tiff_pathes: list[Path],
    mrc_path: Path,
    data_type: Literal[1, 0] | None,
    pixel_spacing: list[float, float, float] | None,
):
    # NOTE: tif2mrc version
    # tif2mrc -B 0 -p 200 tif mrc
    # voxel_size
    # -B 0 => unsigned
    # set_up_lst = ["source", "/etc/profile.d/IMOD-linux.sh"]
    # subprocess.Popen(set_up_lst)
    folder_for_16_bit = Path(tiff_pathes[0].parent / "16_bit")
    if folder_for_16_bit.exists():
        folder_for_16_bit.rmdir()

    folder_for_16_bit.mkdir()

    pairs_of_pathes = [
        (p, (folder_for_16_bit / f'{p.stem}_16bit{"".join(p.suffixes)}'))
        for p in tiff_pathes
    ]

    print(f"Pairs of pathes: {pairs_of_pathes}")
    # TODO: starmap/map from multiprocessing?
    for pair in pairs_of_pathes:
        tiff_32_bit_path, tiff_16_bit_path = pair
        _convert_tiff_32_to_16_bit(tiff_32_bit_path, tiff_16_bit_path)

    tiff_pathes_str = [str(pair[1].resolve()) for pair in pairs_of_pathes]

    print(f"Converting tiffs: {tiff_pathes_str}")

    base_args = ["tif2mrc"]

    if data_type:
        base_args = base_args + ["-B", str(data_type)]

    if pixel_spacing:
        pixel_spacing_str: str = ",".join(pixel_spacing)
        base_args = base_args + ["-p", pixel_spacing_str]
    else:
        base_args = base_args = ["-P"]

    lst: list[str] = base_args + tiff_pathes_str + [str(mrc_path.resolve())]
    print(f"Command: {lst}")
    subprocess.Popen(lst)

    # reader = OMETIFFReader(fpath=tiff_path)
    # img_array_np, metadata, xml_metadata = reader.read()
    # img_array = da.from_array(img_array_np)
    # del img_array_np
    # gc.collect()

    # # write data to mrcfile
    # with mrcfile.mmap(
    #     str(mrc_path.resolve()), "w+"
    # ) as mrc_original:
    #     mrc_original.set_data(img_array)

    # return img_array, metadata, xml_metadata


# TODO: remove
if __name__ == "__main__":
    # should be
    # 32 BIT FLOAT
    # Pixel spacing:(8 Å, 8 Å, 8 Å)
    tiff_pathes = _get_tiff_pathes(
        Path(
            "/mnt/data_backup_ceph/datasets_from_alessio/empiar-12017/WT_fed_6461_mitochondria_instance_segmentation"
        )
    )
    convert_tiff_to_mrc(
        tiff_pathes,
        Path(
            "/mnt/data_backup_ceph/datasets_from_alessio/empiar-12017/WT_fed_6461_mitochondria_instance_segmentation/volume.mrc"
        ),
        # 1,
        [8.0, 8.0, 8.0],
    )
