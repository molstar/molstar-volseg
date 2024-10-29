from pathlib import Path
# try:
#     import brotlicffi as brotli
# except ImportError:
import brotli

def brotli_bytes_to_file(data: bytes, o: Path):
    compressed = brotli.compress(data)
    # compressed bytestring
    # should write to file
    with open(o, 'w') as f:
        f.write(compressed)
        
    return o
        
def brotli_bytes_from_file(i: Path):
    with open(i, 'r') as f:
        data = f.read()
        decompressed = brotli.decompress(data)
    
    return decompressed
    