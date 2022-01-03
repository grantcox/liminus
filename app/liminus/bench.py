from contextlib import contextmanager
from dataclasses import dataclass
from timeit import default_timer as timer
from typing import Dict, List, Tuple


@dataclass
class Benchmark:
    start: float
    cumulative: float
    calls: int


timerdata: Dict[str, Benchmark] = {}


@contextmanager
def measure(mark: str = ''):
    start(mark)
    try:
        yield
    finally:
        stop(mark)


def measure_function(fn):
    def wrapper(*args, **kwargs):
        label = fn.__name__
        if len(args) and args[0] and hasattr(args[0], '__class__'):
            label = '{}.{}'.format(args[0].__class__.__name__, fn.__name__)
        start(label)
        try:
            result = fn(*args, **kwargs)
        finally:
            stop(label)
        return result
    return wrapper


def start(mark: str):
    if mark not in timerdata:
        timerdata[mark] = Benchmark(0, 0, 0)
    timerdata[mark].start = timer()


def stop(mark: str):
    if mark in timerdata:
        timerdata[mark].cumulative += timer() - timerdata[mark].start
        timerdata[mark].calls += 1


def results() -> List[Tuple[float, str, str]]:
    r = []
    for mark, details in timerdata.items():
        summary = f'{details.cumulative:.4f} for {details.calls:d} calls'
        r.append((details.cumulative, mark, summary))
    return sorted(r, reverse=True)


def pretty() -> str:
    r = results()
    max_label_width = max([len(mark) for cumulative, mark, summary in r])
    return '\n'.join([
        '%s: %s' % (mark.rjust(max_label_width), summary)
        for cumulative, mark, summary in r])
