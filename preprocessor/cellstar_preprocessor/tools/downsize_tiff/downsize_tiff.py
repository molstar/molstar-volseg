from pathlib import Path

from PIL import Image
from PIL import Image

# def downsize_tiff(p: Path, output: Path, factor: int):
#     original_image = pyvips.Image.new_from_file(str(p.resolve()))
#     new_w = int(original_image.width / factor)
#     new_h = int(original_image.height / factor)
#     t = pyvips.Image.thumbnail(str(p.resolve()), new_w, height=new_h)

#     # Save with LZW compression
#     t.tiffsave(str(output.resolve()), tile=True, compression="lzw")
#     return output


# NOTE: MAY WORK
# def downsize_tiff(p: Path, output: Path, factor: int):

#     filename = str(p.resolve())

#     with tifffile.Timer():
#         stack = tifffile.imread(filename)[:, ::4, ::4].copy()

#     with tifffile.Timer():
#         with tifffile.TiffFile(filename) as tif:
#             page = tif.pages[0]
#             shape = len(tif.pages), page.imagelength // 4, page.imagewidth // 4
#             stack = numpy.empty(shape, page.dtype)
#             for i, page in enumerate(tif.pages):
#                 # stack[i] = page.asarray(out='memmap')[::4, ::4]
#                 # better use interpolation instead:
#                 stack[i] = cv2.resize(
#                     page.asarray(),
#                     dsize=(shape[2], shape[1]),
#                     interpolation=cv2.INTER_LINEAR,
#                 )
                
#         tifffile.imwrite(stack)


def downsize_tiff(p: Path, output: Path, factor: int):
    # "Processes the image"
    
    image = Image.open(str(p.resolve()))
    x = int(image.width / factor)
    y = int(image.height / factor)

    # proc_image = process_image(image)
    # proc
    # _image.save('outfile.tiff')
    
    image.resize((x, y), Image.ANTIALIAS) # or whatever you are doing to the image
    image.save(str(output.resolve()))

    # image = Image.open('infile.tiff')
    # proc_image = process_image(image)
    # proc_image.save('outfile.tiff')