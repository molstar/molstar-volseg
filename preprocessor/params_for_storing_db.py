from numcodecs import Zstd, Zlib, GZip, BZ2, LZMA
import numpy as np


# Blosc compressor params:
# https://numcodecs.readthedocs.io/en/stable/blosc.html
# cname - compression algo
# clevel - compression lvl
# shuffle - kinda filter, but not that filter that is specified when creating zarr arr
# blocksize - if 0, automatically

COMPRESSORS = (
        None,
        Zstd(level=1),
        Zlib(level=1),
        GZip(level=1),
        BZ2(level=1),
        LZMA(preset=1)
        # Blosc(cname='blosclz', clevel=1, shuffle=Blosc.SHUFFLE, blocksize=0),
        # Blosc(cname='lz4', clevel=1, shuffle=Blosc.SHUFFLE, blocksize=0),
        # Blosc(cname='lz4hc', clevel=1, shuffle=Blosc.SHUFFLE, blocksize=0),
        # Blosc(cname='zlib', clevel=1, shuffle=Blosc.SHUFFLE, blocksize=0),
        # Blosc(cname='zstd', clevel=1, shuffle=Blosc.SHUFFLE, blocksize=0)
    )

CHUNKING_MODES = (
    # zarr determines => pass True in that function
        'auto',
        'false'
)