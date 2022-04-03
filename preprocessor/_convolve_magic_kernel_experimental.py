import numpy as np
from scipy import ndimage
k = np.array([
    [1, 1, 1, 1, 1],
    [1, 4, 4, 4, 1],
    [1, 4, 6, 4, 1],
    [1, 4, 4, 4, 1],
    [1, 1, 1, 1, 1]
])

a = np.arange(25).reshape(5,5)
# TODO: Divide each by 16 after conv!
c = ndimage.convolve(a, k, mode='constant', cval=0.0)
print(c)

# TODO: try 3d kernel