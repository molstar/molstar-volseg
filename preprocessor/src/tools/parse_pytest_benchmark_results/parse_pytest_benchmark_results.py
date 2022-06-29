

import json
from pathlib import Path
from preprocessor.src.tools.get_dir_size.get_dir_size import get_dir_size

from preprocessor.tests.test_benchmark_read_slice import BOX_CHOICES, DB_PATHS, KEYS

def parse_pytest_benchmark_results(filepath: Path) -> dict:
    read_json = {}
    with open(filepath.resolve()) as json_file:
        read_json = json.load(json_file)

    global_dict = {}
    for entry_id in KEYS:
        global_dict[entry_id] = {}
        dframe_dict = global_dict[entry_id]
        benchmarks_list: list = read_json['benchmarks']
        single_entry_list = list(filter(lambda b: (b['params']['key'] == entry_id), benchmarks_list))

        # create dict structure
        dframe_dict['entry_size'] = []
        dframe_dict['db_id'] = []
        for box_choice in BOX_CHOICES:
            dframe_dict[str(box_choice)] = []

        for db_id in DB_PATHS:
            dframe_dict['db_id'].append(db_id)
            # db_1// etc.
            single_db_list = list(filter(lambda b: (b['params']['db_path'] == db_id), single_entry_list))
            for box_choice in BOX_CHOICES:
                single_box_choice_item = list(filter(lambda b: (b['params']['box_choice'] == box_choice), single_db_list))
                assert len(single_box_choice_item) == 1
                single_box_choice_item = single_box_choice_item[0]
                mean_val = single_box_choice_item['stats']['mean']
                # not append, create list for that key first as value
                dframe_dict[str(box_choice)].append(mean_val)
            entry_size = get_dir_size(Path(f'{db_id}/emdb/{entry_id}'))
            dframe_dict['entry_size'].append(entry_size)

    return global_dict
