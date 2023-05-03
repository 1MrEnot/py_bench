from dataclasses import dataclass
from typing import Iterable
import numpy as np
from itertools import pairwise

from py_bench.common import CaseResultsComparison

ParamCaseComparisonPair = tuple[dict[str, object], CaseResultsComparison]


@dataclass
class ParametersCase:
    parameters: dict[str, object]
    equality_groups: dict[int, 'CaseEqualityGroup']


@dataclass
class CaseEqualityGroup:
    method_names: tuple[str, ...]
    value: object


class BenchmarkCallResultVisualizer:

    def visualize(self, comparison_results: list[ParamCaseComparisonPair]):
        parameter_cases = tuple(map(self._map_comparison_result_to_case_visualisation, comparison_results))
        self._visualise_results_for_case(parameter_cases, self._get_different_only_cases(parameter_cases))

    @classmethod
    def _map_comparison_result_to_case_visualisation(
            cls, case_result_pair: ParamCaseComparisonPair) -> ParametersCase:
        parameters, comparison = case_result_pair
        return ParametersCase(
            parameters,
            {
                k: CaseEqualityGroup(methods, value)
                for k, (methods, value) in comparison.functions_with_results_by_group.items()
            }
        )

    @classmethod
    def _get_different_only_cases(cls, cases: tuple[ParametersCase]) -> tuple[ParametersCase]:
        return tuple(cls._different_only_cases_iter(cases))

    @classmethod
    def _different_only_cases_iter(cls, cases: tuple[ParametersCase]) -> Iterable[ParametersCase]:
        for case in cases:
            if len(case.equality_groups) > 1:
                yield case

    def _visualise_results_for_case(self, all_parameter_cases: tuple[ParametersCase],
                                    different_only_cases: tuple[ParametersCase]):
        pass


class NumpyArrayConsoleVisualizer(BenchmarkCallResultVisualizer):

    def _visualise_results_for_case(self, all_parameter_cases: tuple[ParametersCase],
                                    different_only_cases: tuple[ParametersCase]):
        case_message = tuple(map(self._get_case_message, different_only_cases))
        if case_message:
            print("Case differences: ")
            print('\n'.join(case_message))
        else:
            print("No difference found")

    @classmethod
    def _get_case_message(cls, case: ParametersCase):
        pairs = pairwise(case.equality_groups.items())
        messages = tuple(map(lambda p: cls._get_pair_comparison_message(*p), pairs))
        if any(messages):
            rows = messages
            if case.parameters:
                rows = [str(case.parameters), *messages]
            return '\n'.join(rows)
        return None

    @classmethod
    def _get_pair_comparison_message(cls, pair0: tuple[int, CaseEqualityGroup], pair1: tuple[int, CaseEqualityGroup]):
        (idx0, res0_eq_group) = pair0
        res0 = res0_eq_group.value

        (idx1, res1_eq_group) = pair1
        res1 = res1_eq_group.value

        msg = cls._get_comparison_message(res0, res1)
        if msg:
            return f'{idx0}-{idx1}: {msg}'

        return None

    @classmethod
    def _get_comparison_message(cls, res0, res1) -> str | None:
        if np.array_equal(res0, res1):
            return None

        if res0.shape != res1.shape:
            return f"Different shapes: {res0.shape}-{res1.shape}"

        res0[np.isclose(res0, 0)] = 0.1
        res1[np.isclose(res1, 0)] = 0.1
        r_delta = res0 / res1
        r_delta = np.where(r_delta < 1, 1 / r_delta, r_delta)
        a_delta = abs(res0 - res1)
        return f"abs_delta = {a_delta.max():.2f}, rel_delta = {(1 - r_delta.max()) * 100:.2f} %"
