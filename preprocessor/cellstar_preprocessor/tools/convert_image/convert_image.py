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
    dir = Path('C:/Users/chere/OneDrive - MUNI/Figures/PNG')
    outdir = Path('C:/Users/chere/OneDrive - MUNI/Figures/JPEG')
    for p in dir.glob("*.png"):
        convert_image(p, outdir / (p.stem + '.jpeg'))