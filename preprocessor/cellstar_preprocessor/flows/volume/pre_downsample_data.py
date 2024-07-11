import multiprocessing
import shutil
from pathlib import Path

from cellstar_db.models import AssetKind, RawInput
from cellstar_preprocessor.flows.constants import DOWNSAMPLING_KERNEL
from cellstar_preprocessor.flows.volume.helper_methods import generate_kernel_3d_arr
from cellstar_preprocessor.tools.downsample_map.downsample_map import downsample_map
from cellstar_preprocessor.tools.downsample_stl.downsample_stl import downsample_stl
# from cellstar_preprocessor.tools.downsize_tiff.downsize_tiff import downsize_tiff
from cellstar_preprocessor.tools.wrl_to_stl.wrl_to_stl import wrl_to_stl
# from cellstar_preprocessor.tools.downsize_tiff.downsize_tiff import downsize_tiff

# from cellstar_preprocessor.model.input import InputKind
# from cellstar_preprocessor.tools.downsample_map.downsample_map import downsample_map
# from cellstar_preprocessor.tools.downsize_tiff.downsize_tiff import downsize_tiff

TEMP_DOWNSIZED_FOLDER_NAME_STR = "temp_downsized"


def pre_downsample_data(
    inputs: list[RawInput], working_folder: str
):
    downsize_args: list[tuple[Path, Path, int]] = []
    # downsized_pathes: list[Path] = []
    for idx, i in enumerate(inputs):
        factor = inputs[idx].parameters.pre_downsampling_factor
        # TODO: other types
        temp_downsized_folder_path = (
            Path(working_folder) / TEMP_DOWNSIZED_FOLDER_NAME_STR
        )
        if not temp_downsized_folder_path.exists():
            temp_downsized_folder_path.mkdir(parents=True)

        downsized_input_path = temp_downsized_folder_path / str(
            Path(inputs[idx].path).stem + "_downsized" + Path(inputs[idx].path).suffix
        )
        if inputs[idx].kind in {
            AssetKind.tiff_image_stack_dir,
            AssetKind.tiff_segmentation_stack_dir,
        }:
            # downsized_pathes.append(downsized_stack_folder_path)
            inputs[idx].path = downsized_input_path

            if downsized_input_path.exists():
                shutil.rmtree(downsized_input_path)
            downsized_input_path.mkdir(parents=True)

            for input_tiff in Path(inputs[idx].path).glob("*.ti*"):
                output_tiff = downsized_input_path / input_tiff.name
                downsize_args.append(
                    (input_tiff, output_tiff, factor)
                )

            # with multiprocessing.Pool(multiprocessing.cpu_count()) as p:
            #     p.starmap(downsize_tiff, downsize_args)

            # p.join()

        elif inputs[idx].kind == AssetKind.map:
            kernel = generate_kernel_3d_arr(list(DOWNSAMPLING_KERNEL))
            downsample_map(
                Path(inputs[idx].path),
                downsized_input_path,
                factor,
                kernel,
            )
            inputs[idx].path = downsized_input_path

        elif inputs[idx].kind == AssetKind.stl:
            # elif k == InputKind.wrl:
            stl_path = wrl_to_stl(Path(inputs[idx].path), downsized_input_path.parent / 'stl.stl')
            
            # get_stl
            # pre downsample
            # return stl
            # if inputs[idx].path.suffix == ".stl":
            rate = 1 / factor
            downsample_stl(stl_path, downsized_input_path.with_suffix('.stl'), rate)
            inputs[idx].path = downsized_input_path.with_suffix('.stl')
            inputs[idx].kind = AssetKind.stl

    # return downsized_pathes
    # TODO: check if they were changed indeed
    return inputs
