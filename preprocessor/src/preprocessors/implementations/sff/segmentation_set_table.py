import copy
from typing import Dict, Tuple, Set, Union

import numpy as np


class SegmentationSetTable:
    def __init__(self, lattice, value_to_segment_id_dict_for_specific_lattice_id):
        self.value_to_segment_id_dict = value_to_segment_id_dict_for_specific_lattice_id
        self.entries: Dict = self.__lattice_to_dict_of_sets(lattice)
        
    def get_serializable_repr(self) -> Dict:
        '''
        Converts sets in self.entries to lists, and returns the whole table as a dict
        '''
        d: Dict = copy.deepcopy(self.entries)
        for i in d:
            d[i] = list(d[i])

        return d
    
    def __lattice_to_dict_of_sets(self, lattice: np.ndarray) -> Dict:
        '''
        Converts original latice to dict of singletons.
        Each singleton should contain segment ID rather than value
         used to represent that segment in grid
        '''

        unique_values: list = np.unique(lattice).tolist()
        # value 0 is not assigned to any segment, it is just nothing
        d = {}
        for grid_value_of_segment in unique_values:
            if grid_value_of_segment == 0:
                d[grid_value_of_segment] = {0}
            else:
                d[grid_value_of_segment] = {self.value_to_segment_id_dict[grid_value_of_segment]}
            # here we need a way to access zarr data (segment_list)
            # and find segment id for each value (traverse dict backwards)
            # and set d[segment_value] = to the found segment id
        
        return d

    def get_categories(self, ids: Tuple) -> Tuple:
        '''
        Returns sets from the dict of sets (entries) based on provided IDs
        '''
        return tuple([self.entries[i] for i in ids])

    def __find_category(self, target_category: Set) -> Union[int, None]:
        '''
        Looks up a category (set) in entries dict, returns its id or None if not found
        '''
        for category_id, category in self.entries.items():
            if category == target_category:
                return category_id
        return None

    def __add_category(self, target_category: Set) -> int:
        '''
        Adds new category to entries and returns its id
        '''
        new_id: int = max(self.entries.keys()) + 1
        self.entries[new_id] = target_category
        return new_id

    def resolve_category(self, target_category: Set):
        '''
        Looks up a category (set) in entries dict, returns its id
        If not found, adds new category to entries and returns its id
        '''
        category_id = self.__find_category(target_category)
        if category_id != None:
            return category_id
        else:
            return self.__add_category(target_category)
