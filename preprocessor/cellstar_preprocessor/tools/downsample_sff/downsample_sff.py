

from pathlib import Path
from cellstar_db.models import PrimaryDescriptor
from sfftkrw.schema.adapter_v0_8_0_dev1 import SFFSegmentation
from cellstar_preprocessor.model.sff import SFFWrapper

def downsample_sff(i: Path, o: Path, factor: int):
    return
    w = SFFWrapper(i)
    d = w.data_model
    pd = d.primary_descriptor
    match pd:
        case PrimaryDescriptor.three_d_volume:
            raise NotImplementedError()
        case PrimaryDescriptor.mesh_list:
            # convert to stl
            w.sfftk_reader.ex
            downsample_stl(Path(inputs[idx].path), downsized_input_path.with_suffix('.stl'), rate)
            # downsample stl
            # convert back to sff
            # 
        case _:
            raise NotImplementedError
    
    # do downsampling
     
    obj = 
    # write to hff
    result = SFFSegmentation.from_json(obj)