import sys
from datetime import datetime
from typing import TextIO, Literal, Union


class Timing:
    '''Context manager which measures time of the block execution.
    @param  `name`  Name used when printing measured time
    @param  `file`  Output stream for printing measure time or 'stdout' (default) or 'stderr'
    @param  `mute`  Supress all printing (measured time can still be accessed by .time)
    '''
    def __init__(self, name: str = '', file: Union[TextIO, Literal['stdout', 'stderr']] = 'stdout', mute=False):
        self.name = name
        self.file = sys.stdout if file == 'stdout' else sys.stderr if file == 'stderr' else file
        self.mute = mute
        self.time = None
    def __enter__(self):
        self.t0 = datetime.now()
        return self
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.time = datetime.now() - self.t0
        if not self.mute:
            err_flag = '[Failed] ' if exc_type is not None else ''
            message = f'Timing:\t{self.time}\t{err_flag}{self.name}'
            print(message, file=self.file)
