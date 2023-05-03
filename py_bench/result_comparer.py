from typing import Callable, TypeVar

import numpy

from py_bench.common import CaseResultsComparison

TRes = TypeVar('TRes')
Comparer = Callable[[TRes, TRes], bool]

INITIAL_COMPARER_MAP = {
    numpy.ndarray: numpy.allclose
}


class ResultComparer:

    def __init__(self, comparer_map: dict[type, Comparer] = None):
        self._comparer_map = (comparer_map or {}) | INITIAL_COMPARER_MAP

    def compare_results(self, results: dict[str, TRes]) -> CaseResultsComparison:
        result_wrappers = tuple(self._map_to_wrappers(results))
        unique_wrapper_list = list(set(result_wrappers))
        results_indexes = (unique_wrapper_list.index(el) for el in result_wrappers)

        func_res_map: dict[str, tuple[TRes, int]] = {
            func: (res, idx)
            for ((func, res), idx) in zip(results.items(), results_indexes)
        }

        return CaseResultsComparison(func_res_map)

    def _map_to_wrappers(self, results: dict[str, TRes]):
        for method, res in results.items():
            yield ResultComparerWrapper(method, res, self._comparer_map.get(type(res)))


class ResultComparerWrapper:

    def __init__(self, method, value, custom_comparer: Comparer = None):
        self._method = method
        self.value = value
        self._comparer: Comparer = custom_comparer

    def __eq__(self, other: 'ResultComparerWrapper'):
        if self._comparer:
            return self._comparer(self.value, other.value)
        return self.value == other.value

    def __hash__(self):
        return 0
