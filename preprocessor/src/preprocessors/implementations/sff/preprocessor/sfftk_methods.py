def __open_hdf5_as_segmentation_object(self, file_path: Path) -> SFFSegmentation:
    return SFFSegmentation.from_file(str(file_path.resolve()))
