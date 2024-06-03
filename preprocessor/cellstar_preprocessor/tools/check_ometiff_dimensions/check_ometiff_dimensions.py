from pathlib import Path

from pyometiff import OMETIFFReader

pathes: list[Path] = [
    Path(
        "test-data/preprocessor/sample_volumes/custom/custom-hipsc_230741/hipsc_230741_volume.ome.tif"
    ),
    Path(
        "test-data/preprocessor/sample_segmentations/custom/custom-hipsc_230741/hipsc_230741_segmentation.ome.tif"
    ),
]

for p in pathes:
    print(f"Opening {p.name}")
    reader = OMETIFFReader(fpath=p)
    img_array, metadata, xml_metadata = reader.read()

    print(p.name)
    print("Dimension order: ", metadata["DimOrder BF Array"])
    print("Data array shape", img_array.shape)
