import multiprocessing
from pathlib import Path
import shutil
from cellstar_preprocessor.model.input import InputKind
from cellstar_preprocessor.tools.downsize_tiff.downsize_tiff import downsize_tiff


def pre_downsample_data(input_paths: list[str], input_kinds: list[InputKind], pre_downsample_data_factor: int, working_folder: str):
    args: list[tuple[Path, Path, int]] = []
    # downsized_pathes: list[Path] = []
    for idx, i_path in enumerate(input_paths):
        # TODO: other types
        if input_kinds[idx] == InputKind.tiff_image_stack_dir:
            downsized_stack_folder_path = Path(working_folder) / 'temp_downsized' / str(Path(i_path).stem + '_downsized' + Path(i_path).suffix) 
            # downsized_pathes.append(downsized_stack_folder_path)
            input_paths[idx] = downsized_stack_folder_path
            
            if downsized_stack_folder_path.exists():
                shutil.rmtree(downsized_stack_folder_path)
            downsized_stack_folder_path.mkdir(parents=True)
            
            for input_tiff in Path(i_path).glob('*.ti*'):
                output_tiff = downsized_stack_folder_path / input_tiff.name
                args.append((input_tiff, output_tiff, pre_downsample_data_factor))
        
            with multiprocessing.Pool(multiprocessing.cpu_count()) as p:         
                p.starmap(downsize_tiff, args)
    
            p.join()
    
    # return downsized_pathes
    return input_paths
    