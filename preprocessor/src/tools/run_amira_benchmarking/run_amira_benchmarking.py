import threading
from timeit import default_timer as timer
import tracemalloc
# from memory_profiler import profile
import psutil

# Methodology:
# put together benchmarking code for all methods that needs to be benchmarked
# Open an input file
# Paste code for benchmarking all methods

def display_cpu():
    global cpu_percent_list
    global running
    running = True
    amira3Dprocess = psutil.Process(pid=35576)
    # start loop
    while running:
        cpu_percent_list.append(amira3Dprocess.cpu_percent(interval=1))
        # print(amira3Dprocess.cpu_percent(interval=1))

def start_measurements():
    global t
    # create thread and start it
    t = threading.Thread(target=display_cpu)
    t.start()

def stop_measurements():
    global running
    global t
    # use `running` to stop loop in thread so thread will end
    running = False
    # wait for thread's end
    t.join()


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
    global cpu_percent_list
    cpu_percent_list = []
    # TODO: measurements code
    start = timer()
    start_measurements()
    benchmark_method()
    # TODO: measurements code
    stop = timer()
    stop_measurements()
    print(cpu_percent_list)
    print(f'Duration: {stop - start}')
    
# 
def main_wrapper():
    # amira3Dprocess = psutil.Process(pid=35576)
    # if methods list is short, just run_measurements multiple time
    for method in METHODS_LIST:
        run_measurements(method, amira3Dprocess)


