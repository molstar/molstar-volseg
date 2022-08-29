
# e.g. emd-1832 or emd_1832
import re
import urllib.request

LIST_OF_ENTRY_IDS = []

def prepare_input_for_preprocessor(entry_ids: list):
    for entry_id in entry_ids:
        db = re.split('-|_', entry_id)[0]
        id = re.split('-|_', entry_id)[-1]

        emdb_folder_name = db.upper() + '-' + id
        emdb_map_file_name = db.lower() + '_' + id + '.map.gz'
        if db == 'emd':
            urllib.request.urlretrieve(
                f'https://ftp.ebi.ac.uk/pub/databases/emdb/structures/{emdb_folder_name}/map/{emdb_map_file_name}',
                emdb_map_file_name)
        elif db == 'empiar':
            pass