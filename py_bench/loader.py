from math import floor, ceil
from shutil import get_terminal_size
from threading import Thread
from time import sleep, time

from py_bench.utils import ljust_fit_string


TimeInSec = float


class Loader:
    DONE_BAR = '█'
    TODO_BAR = '▒'
    BULLET = '•'

    DONE_TEXT = ' DONE '
    DONE_FILLER = '-'

    PREFIX_WIDTH = 13
    BAR_WIDTH = 33
    # total = prefix(13) + bar(33) + percent(4) + bullet(10) + timer(5) + space*4

#   |FooFunc      ██████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  17% • 00:17|
#   |FooFunc      ------------- DONE -------------- 100% • 02:24|

    def __init__(self, prefix, max_value=1, fps=10):
        self._prefix = ljust_fit_string(prefix, self.PREFIX_WIDTH)

        self._current = 0
        self._max = max_value

        self._timeout = 1 / fps
        self._thread = Thread(target=self._animate, daemon=True)
        self._start_time: float = 0
        self._done = False

    def set_stage(self, stage):
        self._current = stage

    def _animate(self):
        while not self._done:
            print(f"\r{self.desc}", flush=True, end="")
            sleep(self._timeout)

    @property
    def stage(self) -> float:
        return min(self._current / self._max, 1)

    @property
    def desc(self):
        percentage = f"{(self.stage * 100):3.0f}%"
        elapsed = int(time() - self._start_time)
        timer = f"{elapsed // 60 :02d}:{elapsed % 60 :02d}"
        return " ".join([self._prefix, self.bar, percentage, self.BULLET, timer])

    @property
    def bar(self):
        if not self._done:
            done_bar_count = int(self.BAR_WIDTH * self.stage)
            return (self.DONE_BAR * done_bar_count).ljust(self.BAR_WIDTH, self.TODO_BAR)

        missing = self.BAR_WIDTH - len(self.DONE_TEXT)
        left = floor(missing / 2)
        right = ceil(missing / 2)
        filler = self.DONE_FILLER
        return f"{filler * left}{self.DONE_TEXT}{filler * right}"

    def start(self):
        self._start_time = time()
        self._thread.start()
        return self

    def stop(self):
        self._done = True
        cols = get_terminal_size((80, 20)).columns
        print("\r" + " " * cols, end="", flush=True)
        print(f"\r{self.desc}", flush=True)

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_value, tb):
        self.stop()
