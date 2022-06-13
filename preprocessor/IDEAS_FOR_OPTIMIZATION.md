1. Compressor/filter for zarr arrs - maybe such that will allow faster reading, not smaller filesizes
2. Iteration over dicts: for key, value in .items() is faster than
```
for key in dict:
```
3. Check where same zarr arrs are loaded into memory ([...]) many times