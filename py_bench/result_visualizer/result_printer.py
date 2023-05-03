from py_bench.common import CaseResultsComparison, BenchObjExecutionResult, CaseBenchmarkExecutionResult
from py_bench.result_visualizer.common import RunGroup, BenchResultViewModel, RunResult
from py_bench.result_visualizer.result_formatter import ResultFormatter, MdResultFormatter

CaseComparisonPair = tuple[dict[str, object], CaseResultsComparison]


class ResultPrinter:

    @classmethod
    def print(cls, result: BenchObjExecutionResult,
              comparison_result: list[CaseComparisonPair],
              result_formatter: 'ResultFormatter' = None) -> None:
        view_model = cls._map_result(result, comparison_result)

        formatter = result_formatter or MdResultFormatter()
        res_str = formatter.format_result(view_model)
        print(res_str)

    @classmethod
    def _map_result(cls, result: BenchObjExecutionResult,
                    comparison_result: list[CaseComparisonPair]) -> BenchResultViewModel:
        if not result.bench_case_results:
            return BenchResultViewModel("", False, False, tuple(), tuple())

        argument_names = tuple(result.bench_case_results[0].parameter_case.keys())

        multiple_methods = True
        row_groups: list[RunGroup] = []
        for r in result.bench_case_results:
            multiple_methods &= len(r.bench_results) > 1
            cmp_res = next(res[1] for res in comparison_result if res[0] == r.parameter_case)
            row_groups.append(cls._build_row_from_result(r, argument_names, cmp_res))

        return BenchResultViewModel(
            type(result.bench_obj).__name__,
            bool(comparison_result),
            multiple_methods,
            argument_names,
            tuple(row_groups)
        )

    @classmethod
    def _build_row_from_result(cls, case_result: CaseBenchmarkExecutionResult,
                               argument_names: tuple[str, ...],
                               comparison_result: CaseResultsComparison) -> RunGroup:

        rows = []
        baseline_bench_time = min(map(lambda x: x.median, case_result.bench_results.values()))
        for method_name, bench_result in case_result.bench_results.items():
            equality_group = comparison_result.get_equality_group_by_method(method_name)

            row = RunResult(
                method_name,
                bench_result.median,
                bench_result.std_dev,
                bench_result.median / baseline_bench_time,
                equality_group,
            )
            rows.append(row)

        arguments = tuple(map(lambda arg: case_result.parameter_case[arg], argument_names))

        return RunGroup(tuple(sorted(rows, key=lambda x: x.method)), arguments, comparison_result)
