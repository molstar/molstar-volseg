import tifffile as tiff

# Source: https://github.com/arjunrajlaboratory/combine-ome-tiff/blob/main/combine_ome_tiff/combine_ome_tiff.py
def combine_ome_tiff(input_file, output_file):
    with tiff.TiffFile(input_file) as input_tiff:
        image_data = input_tiff.asarray()

    with tiff.TiffWriter(output_file) as output_tiff:
        output_tiff.write(image_data)

    # print(f"File '{output_file}' has been created.")