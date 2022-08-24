import threading
import time
from timeit import default_timer as timer
import psutil

import multiprocessing as mp
import numpy as np

def display_cpu():
    global cpu_percent_list
    global running
    running = True
    amira3Dprocess = psutil.Process(pid=45552)
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

def monitor(target):
    worker_process = mp.Process(target=target)
    worker_process.start()
    p = psutil.Process(worker_process.pid)

    # log cpu usage of `worker_process` every 10 ms
    cpu_percents = []
    while worker_process.is_alive():
        cpu_percents.append(p.cpu_percent())
        time.sleep(0.01)

    worker_process.join()
    return cpu_percents

def benchmark_non_local_means_filter():
    a = hx_project.get('Non-Local Means Filter')
    a.ports.doIt.was_hit = True
    a.fire()