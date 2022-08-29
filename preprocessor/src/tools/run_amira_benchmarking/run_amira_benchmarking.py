import threading
from timeit import default_timer as timer
import tracemalloc
# from memory_profiler import profile
import psutil

import time
import multiprocessing as mp
import numpy as np

INPUT_DATA = None

# Methodology:
# exec(open("C:\\Users\\chere\\Work\\cellstar-volume-server\\preprocessor\\src\\tools\\run_amira_benchmarking\\run_amira_benchmarking.py").read())
# works and have access to hx_project variable
# it also runs the code below all methods
# DONT FORGET TO COPY RELEVANT FILE THERE

# put together benchmarking code for all methods that needs to be benchmarked
# Open an input file
# Paste code for benchmarking all methods


# def compute_isosurface_threshold():
#     input_data = hx_project.get('EMD-1832.mrc')
#     arr = input_data.get_array()
#     mean = arr.mean()
#     std = arr.std()
#     iso_threshold = mean + 2 * std
#     return iso_threshold

def benchmark_isosurface():
    hx_project.create('HxIsosurface')
    isosurface = hx_project.get('Isosurface')
    input_data = hx_project.get('EMD-1832.mrc')
    arr = input_data.get_array()
    mean = arr.mean()
    std = arr.std()
    iso_threshold = mean + 2 * std

    isosurface.ports.data.connect(input_data)
    isosurface.ports.doIt.was_hit = True
    isosurface.fire()
    isosurface.ports.threshold.value = iso_threshold
    isosurface.ports.doIt.was_hit = True
    isosurface.fire()

def benchmark_volume_rendering():
    hx_project.create('HxVolumeRenderingSettings')
    hx_project.create('HxVolumeRender2')
    settings = hx_project.get('Volume Rendering Settings')
    volume_render = hx_project.get('Volume Rendering')
    input_data = hx_project.get(INPUT_DATA)

    settings.ports.data.connect(input_data)
    settings.fire()
    volume_render.ports.volumeRenderingSettings.connect(settings)
    volume_render.fire()

def benchmark_method_2():
    pass

def run_measurements(benchmark_method):
    # TODO: measurements code
    start = timer()
    benchmark_method()
    # TODO: measurements code
    stop = timer()
    print(f'Duration: {stop - start}')

# run_measurements(benchmark_non_local_means_filter)

# def main_wrapper():
#     # amira3Dprocess = psutil.Process(pid=35576)
#     # if methods list is short, just run_measurements multiple time
#     for method in METHODS_LIST:
#         run_measurements(method, amira3Dprocess)


