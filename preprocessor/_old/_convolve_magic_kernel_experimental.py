import numpy as np
from scipy import ndimage, signal

from preprocessor.src.preprocessors.implementations.sff.preprocessor.downsampling.downsampling import \
    generate_kernel_3d_arr

if __name__ == '__main__':

    k = generate_kernel_3d_arr([1, 4, 6])

    a = np.arange(125).reshape(shape=(5, 5, 5)).astype(np.float64)
    # a = np.random.normal(0, 10, (5, 5, 5))#.astype(np.int)

    print('ORIGINAL ARR')
    print(a)
    for mode in ['same', 'valid', 'full']:
        c_convolve = signal.convolve(a, k, mode=mode, method='fft')
        print(f'signal.convolve_{mode}')
        print(c_convolve[::2, ::2])

    c_convolve_same = signal.convolve(a, k, mode='same', method='fft')
    c_ndimage = ndimage.convolve(a, k, mode='constant', cval=0.0)

    # TODO: use numpy.isclose(a, b, rtol=1e-05, atol=1e-08, equal_nan=False)
    if np.array_equal(c_convolve_same, c_ndimage):
        print('ndimage and convolve_same are equal')
    else:
        print('NOT EQUAL')
        print(c_convolve_same)
        print(c_ndimage)
        diff = np.subtract(c_convolve_same, c_ndimage)
        max_diff = diff.max()
        min_diff = diff.min()
        print(f'max_diff {max_diff}')
        print(f'min_diff {min_diff}')
        # np_all = (c_convolve_same == c_ndimage).all()
        # print(np_all)

    print('ndimage.convolve')
    print(c_ndimage[::2, ::2])
