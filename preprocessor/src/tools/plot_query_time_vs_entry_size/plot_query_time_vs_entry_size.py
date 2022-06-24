

import argparse
from pathlib import Path
from pprint import pprint

import matplotlib.pyplot as plt
import pandas as pd
from preprocessor.src.tools.get_dir_size.get_dir_size import get_dir_size

from preprocessor.src.tools.parse_pytest_benchmark_results.parse_pytest_benchmark_results import parse_pytest_benchmark_results
from preprocessor.tests.test_benchmark_read_slice import BOX_CHOICES


BENCHMARKING_RESULTS_FILENAME = Path('.benchmarks/Windows-CPython-3.9-64bit/0001_benchmarking.json')

def parse_script_args():
    parser=argparse.ArgumentParser()
    parser.add_argument("--entry_id")
    args=parser.parse_args()
    return args

def _plot_single_entry_data(dframe_dict: dict):
    df = pd.DataFrame(dframe_dict)
    df['entry_size'] = round(df['entry_size'] / 10**6, 2)
    df['db_id_and_entry_size'] = df['db_id'].astype(str) + '\n' + df['entry_size'].astype(str) + ' MB'
    df = df.sort_values(by='entry_size')
    print(df)
    df.plot(x='db_id_and_entry_size', y=[str(x) for x in BOX_CHOICES], kind='bar', rot=0)
    plt.show()

if __name__ == '__main__':
    args = parse_script_args()
    if args.entry_id:
        print(f'plotting results for {args.entry_id}')
        global_dict = parse_pytest_benchmark_results(BENCHMARKING_RESULTS_FILENAME)
        dframe_dict = global_dict[args.entry_id]
        _plot_single_entry_data(dframe_dict)
    