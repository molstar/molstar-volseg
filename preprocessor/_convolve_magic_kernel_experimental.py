from typing import List
import numpy as np
from scipy import ndimage, signal

# TODO: generate kernel either myself or smart function
# TODO: apply on actual code (make comparison of outputs by copying old images
# and creating a separate func + conditional in (as it accepts 3D kernel, not 1D as the current func)
# 
def generate_kernel_3d_arr(pattern: List[int]) -> np.ndarray:
    '''
    Generates conv kernel based on pattern provided (e.g. [1,4,6,4,1]).
    https://stackoverflow.com/questions/71739757/generate-3d-numpy-array-based-on-provided-pattern/71742892#71742892
    '''
    pattern = pattern[0:3]
    x = np.array(pattern[-1]).reshape([1,1,1])
    for p in reversed(pattern[:-1]):
        x = np.pad(x, mode='constant', constant_values=p, pad_width=1)
    
    k = (1/x.sum()) * x
    # print(f'Kernel generated (further divided by sum): {x}')
    return k


if __name__ == '__main__':

    k = generate_kernel_3d_arr([1, 4, 6])

    a = np.arange(125).reshape(5,5,5).astype(np.float64)
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
