from pathlib import Path
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

def convert_image(inp: Path, out: Path):
    im = Image.open(str(inp.resolve()))
    
    # print(im.info['dpi'], 'INPUT DPI')
    rgb_im = im.convert('RGB')
    rgb_im.save(str(out.resolve()), dpi=(300, 300))
    
    # print(rgb_im.info['dpi'], 'OUTPUT DPI')
    print(1)
    
if __name__ == '__main__':
    dir = Path('preprocessor/cellstar_preprocessor/tools/png_to_tiff/figures')
    for p in dir.glob("*.png"):
        convert_image(p, p.with_suffix('.jpeg'))