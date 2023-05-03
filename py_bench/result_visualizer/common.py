from dataclasses import dataclass
from typing import Optional

from py_bench.common import CaseResultsComparison


@dataclass
class BenchResultViewModel:
    bench_obj_name: str
    results_compared: bool
    multiple_methods: bool
    argument_names: tuple[str]
    run_groups: tuple['RunGroup']


@dataclass
class RunGroup:
    runs: tuple['RunResult']
    arguments: tuple[object]
    results_comparison: Optional[CaseResultsComparison]


@dataclass
class RunResult:
    method: str
    median: int
    std_dev: int
    ratio: int
    equality_group: int
