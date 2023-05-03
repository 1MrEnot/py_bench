from dataclasses import dataclass
from typing import TypeVar, Callable


DifferenceDescr = dict[str, object]
ParameterCase = dict[str, object]


TObj = TypeVar('TObj')
TRes = TypeVar('TRes')
BenchMethod = Callable[[TObj], TRes]


class BenchmarkContext:

    def __init__(self, bench_object: TObj,
                 function: Callable[[TObj], TRes], current_parameters: dict[str, object] = None):
        self._bench_object: TObj = bench_object
        self._method: Callable[[TObj], TRes] = function
        self._current_parameters = current_parameters

    def call_method(self) -> TRes:
        return self._method(self._bench_object)

    def log_started(self, invocation_count: int):
        msg = f"{self.method_name} benchmark started with {self._param_part} {invocation_count} invocations/iter"
        # print(msg)

    @property
    def method_name(self) -> str:
        return self._method.__name__

    @property
    def _param_part(self) -> str:
        if self._current_parameters:
            return f"{self._current_parameters} and"
        return ""


@dataclass
class ParameterCase:
    name: str
    method: callable
    arg: object


@dataclass
class CaseResultsComparison:
    _function_result_map: dict[str, tuple[object, int]]

    def get_equality_group_by_method(self, method: str) -> int:
        return self._function_result_map[method][1]

    @property
    def functions_with_results_by_group(self) -> dict[int, tuple[tuple[str, ...], object]]:
        res = {}

        for function, (result, idx) in self._function_result_map.items():
            if idx in res:
                res[idx][0].append(function)
            else:
                pair = ([function], result)
                res[idx] = pair

        return {k: (tuple(v[0]), v[1]) for k, v in res.items()}


@dataclass
class BenchObjExecutionResult:
    bench_obj: object
    bench_case_results: tuple['CaseBenchmarkExecutionResult']


@dataclass
class CaseBenchmarkExecutionResult:
    parameter_case: ParameterCase
    bench_results: dict[str, 'BenchmarkExecutionResult']


@dataclass
class BenchmarkExecutionResult:
    function_result: object
    mean: int
    median: int
    std_dev: int
    std_err: int
