from matplotlib import pyplot as plt
import pandas as pd

from preprocessor.src.tools.measure_compression_effect_on_storage.measure_compression_effect_on_storage import measure_compression_effect_on_storage


def plot_db_size_vs_db_name():
    db_dict = measure_compression_effect_on_storage()
    df = pd.DataFrame(db_dict, index=['DB'])
    df.plot(kind='bar')
    plt.ylabel('size in bytes')
    plt.show()

if __name__ == '__main__':
    plot_db_size_vs_db_name()