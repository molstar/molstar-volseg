import multiprocessing
from pathlib import Path
import shutil
from cellstar_preprocessor.flows.constants import DOWNSAMPLING_KERNEL
from cellstar_preprocessor.flows.volume.helper_methods import generate_kernel_3d_arr
from cellstar_preprocessor.model.input import InputKind
from cellstar_preprocessor.tools.downsample_map.downsample_map import downsample_map
from cellstar_preprocessor.tools.downsize_tiff.downsize_tiff import downsize_tiff

TEMP_DOWNSIZED_FOLDER_NAME_STR = 'temp_downsized'

def pre_downsample_data(input_paths: list[str], input_kinds: list[InputKind], pre_downsample_data_factor: int, working_folder: str):
    args: list[tuple[Path, Path, int]] = []
    # downsized_pathes: list[Path] = []
    for idx, i_path in enumerate(input_paths):
        # TODO: other types
        downsized_input_path = Path(working_folder) / TEMP_DOWNSIZED_FOLDER_NAME_STR / str(Path(i_path).stem + '_downsized' + Path(i_path).suffix)
        if input_kinds[idx] == InputKind.tiff_image_stack_dir:
            # downsized_pathes.append(downsized_stack_folder_path)
            input_paths[idx] = downsized_input_path
            
            if downsized_input_path.exists():
                shutil.rmtree(downsized_input_path)
            downsized_input_path.mkdir(parents=True)
            
            for input_tiff in Path(i_path).glob('*.ti*'):
                output_tiff = downsized_input_path / input_tiff.name
                args.append((input_tiff, output_tiff, pre_downsample_data_factor))
        
            with multiprocessing.Pool(multiprocessing.cpu_count()) as p:         
                p.starmap(downsize_tiff, args)
    
            p.join()
        elif input_kinds[idx] == InputKind.map:
            kernel = generate_kernel_3d_arr(list(DOWNSAMPLING_KERNEL))
            downsample_map(Path(i_path), downsized_input_path, pre_downsample_data_factor, kernel)
            input_paths[idx] = downsized_input_path
            
    # return downsized_pathes
    return input_paths
    