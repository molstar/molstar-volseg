import numpy as np
from scipy import ndimage, signal

# TODO: generate kernel either myself or smart function
# TODO: apply on actual code (make comparison of outputs by copying old images
# and creating a separate func + conditional in (as it accepts 3D kernel, not 1D as the current func)
# 

k = np.array([
    [1, 1, 1, 1, 1],
    [1, 4, 4, 4, 1],
    [1, 4, 6, 4, 1],
    [1, 4, 4, 4, 1],
    [1, 1, 1, 1, 1]
])

k = np.arange(125).reshape(5,5,5)

# k = np.array(
#     [
#         [
#             [1]
#         ],
#         [

#         ],
#         [

#         ]   
#     ]
# )

k = (1/k.sum()) * k

a = np.arange(125).reshape(5,5,5).astype(np.float)
# a = np.random.normal(0, 10, (5, 5, 5))#.astype(np.int)

c_ndimage = ndimage.convolve(a, k, mode='constant', cval=0.0)
c_convolve = signal.convolve(a, k, mode='same', method='fft')
print(a)
print(c_ndimage[::2, ::2])
print(c_convolve[::2, ::2])

# TODO: try 3d kernel