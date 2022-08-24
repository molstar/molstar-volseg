import threading
from timeit import default_timer as timer
import tracemalloc
# from memory_profiler import profile
import psutil

import time
import multiprocessing as mp
import numpy as np

# Methodology:
# exec(open(".\\custom_scripts\\run_amira_benchmarking.py").read())
# works and have access to hx_project variable
# it also runs the code below all methods
# DONT FORGET TO COPY RELEVANT FILE THERE

# put together benchmarking code for all methods that needs to be benchmarked
# Open an input file
# Paste code for benchmarking all methods

# @profile
def benchmark_non_local_means_filter():
    # here goes the method setup

    # hx_project.create('HxVolumeRenderingSettings')
    # hx_project.create('HxVolumeRender2')
    # settings = hx_project.get('Volume Rendering Settings')
    # volume_render = hx_project.get('Volume Rendering')
    # input_data = hx_project.get('EMD-1832.mrc')

    # settings.ports.data.connect(input_data)
    # settings.fire()
    # volume_render.ports.volumeRenderingSettings.connect(settings)
    # volume_render.fire()
    a = hx_project.get('Non-Local Means Filter')
    a.ports.doIt.was_hit = True
    a.fire()

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


