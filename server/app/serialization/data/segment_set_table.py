from dataclasses import dataclass
from typing import Union


@dataclass
class SegmentSetTable(object):
    set_id: list[int]
    segment_id: list[int]
    size: int

    @staticmethod
    def from_dict(set_dict: dict[Union[int, str], list[int]]):
        '''Create `SegmentSetTable` from dict where keys are set ids, values are lists of segments ids.'''
        set_ids = [] 
        segment_ids = []
        for k in set_dict.keys():
            for v in set_dict[k]:
                set_ids.append(int(k))
                segment_ids.append(v)
        return SegmentSetTable(set_ids, segment_ids, len(set_ids))
