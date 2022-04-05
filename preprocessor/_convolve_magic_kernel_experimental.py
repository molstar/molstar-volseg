import numpy as np
from scipy import ndimage, signal

# TODO: generate kernel either myself or smart function
# TODO: apply on actual code (make comparison of outputs by copying old images
# and creating a separate func + conditional in (as it accepts 3D kernel, not 1D as the current func)
# 
def _generate_kernel_3d_arr(pattern: list) -> np.ndarray:
    '''
    Generates conv kernel based on pattern provided as a half of equivalent symmetric 1D kernel
    E.g., to generate kernel for 3d using [1,4,6,4,1] kernel, input should be [1,4,6] since it is symmetric
    https://stackoverflow.com/questions/71739757/generate-3d-numpy-array-based-on-provided-pattern/71742892#71742892
    '''
    x = np.array(pattern[-1]).reshape([1,1,1])
    for p in reversed(pattern[:-1]):
        x = np.pad(x, mode='constant', constant_values=p, pad_width=1)
    
    k = (1/x.sum()) * x
    print(f'Kernel generated (further divided by sum): {x}')
    return k

k = _generate_kernel_3d_arr([1, 4, 6])

a = np.arange(125).reshape(5,5,5).astype(np.float64)
# a = np.random.normal(0, 10, (5, 5, 5))#.astype(np.int)

c_ndimage = ndimage.convolve(a, k, mode='constant', cval=0.0)
c_convolve = signal.convolve(a, k, mode='same', method='fft')
print(a)
print(c_ndimage[::2, ::2])
print(c_convolve[::2, ::2])
