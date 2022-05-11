from preprocessor.src.tools.magic_kernel_downsampling_3d.magic_kernel_downsampling_3d import MagicKernel3dDownsampler


def testing():
    magic_kernel = MagicKernel3dDownsampler()

    radius = 2
    max_dims = (10, 12, 14)

    lst_of_coords = [
        (0, 0, 0),
        (10, 12, 14),
        (0, 12, 0),
        (10, 0, 0)
    ]

    for coords in lst_of_coords:
        r = magic_kernel.get_voxel_coords_at_radius(coords, radius, max_dims)
        print(r)
        print(len(r))

    lst_of_max_coords = [
        (4, 5, 4),
        (10, 12, 14),
        (2, 11, 2),
        (10, 4, 8)
    ]

    for coords in lst_of_max_coords:
        result = magic_kernel.extract_target_voxels_coords(coords)
        print(f'For {coords} there are {len(result)} target voxels')
        print()


def testing_with_dummy_arr():
    SHAPE = (10, 12, 14)
    KERNEL = (1, 4, 6, 4, 1)
    magic_kernel = MagicKernel3dDownsampler()

    arr = magic_kernel.generate_dummy_arr(SHAPE)
    downsampled_arr = magic_kernel.downsample_using_magic_kernel(arr, KERNEL)
    print(f'ORIGINAL ARR, SHAPE {arr.shape}')
    print(arr)
    print(f'DOWNSAMPLED ARR, SHAPE {downsampled_arr.shape}')
    print(downsampled_arr)


if __name__ == '__main__':
    # __testing()
    testing_with_dummy_arr()
