

import argparse
from pathlib import Path
from pprint import pprint

import matplotlib.pyplot as plt
import pandas as pd
from preprocessor.src.tools.get_dir_size.get_dir_size import get_dir_size

from preprocessor.src.tools.parse_pytest_benchmark_results.parse_pytest_benchmark_results import parse_pytest_benchmark_results
from preprocessor.tests.test_benchmark_read_slice import BOX_CHOICES


# BENCHMARKING_RESULTS_FILENAME = Path('.benchmarks/Windows-CPython-3.9-64bit/0004_quantized.json')
BENCHMARKING_RESULTS_FILENAME = Path('.benchmarks/Windows-CPython-3.9-64bit/0007_quantized_u1_u2.json')

def parse_script_args():
    parser=argparse.ArgumentParser()
    parser.add_argument("--entry_id")
    args=parser.parse_args()
    return args

def _plot_single_entry_data(dframe_dict: dict):
    df = pd.DataFrame(dframe_dict)
    df['entry_size'] = round(df['entry_size'] / 10**6, 2)
    # hack to remove db 8 to 12
    # df = df[~df['db_id'].str.contains(pat='[8-9]|1[0-2]', regex=True)]

    df['db_id_and_entry_size'] = df['db_id'].astype(str) + '\n' + df['entry_size'].astype(str) + ' MB'
    df = df.sort_values(by='entry_size')
    print(df)
    ax = df.plot(x='db_id_and_entry_size', y=[str(x) for x in BOX_CHOICES], kind='bar', rot=0)
    # just 0.1 and random_static_region - BIG vs SMALL
    # ax = df.plot(x='db_id_and_entry_size', y=['0.1', BIG SMALL 'random_static_region'], kind='bar', rot=0)

    for container in ax.containers:
        ax.bar_label(container, rotation=90)
    plt.show()

if __name__ == '__main__':
    args = parse_script_args()
    if args.entry_id:
        print(f'plotting results for {args.entry_id}')
        global_dict = parse_pytest_benchmark_results(BENCHMARKING_RESULTS_FILENAME)
        dframe_dict = global_dict[args.entry_id]
        _plot_single_entry_data(dframe_dict)
    