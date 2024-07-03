
from pathlib import Path
import pyvips

def downsize_tiff(p: Path, output: Path, factor: int):
    original_image = pyvips.Image.new_from_file(str(p.resolve()))
    new_w = int(original_image.width / factor)
    new_h = int(original_image.height / factor)
    t = pyvips.Image.thumbnail(str(p.resolve()), new_w, height=new_h)

    # Save with LZW compression
    t.tiffsave(str(output.resolve()), tile=True, compression='lzw')
    return output