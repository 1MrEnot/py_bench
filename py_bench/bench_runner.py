import inspect
import itertools
from dataclasses import dataclass
from typing import Iterable, Optional

from py_bench.bench_registry.bench_regisrty import BenchRegistry, ParamMarkedFunction, ParamFunctionStub, \
    IterationSetupStub
from py_bench.benchmark_call_result_visualizer import BenchmarkCallResultVisualizer
from py_bench.benchmark_executor import BenchmarkExecutor, AccuracySettings
from py_bench.common import BenchObjExecutionResult, ParameterCase, CaseBenchmarkExecutionResult, BenchmarkContext, \
    CaseResultsComparison, TObj, BenchMethod
from py_bench.result_comparer import ResultComparer
from py_bench.result_visualizer import ResultFormatter, ResultPrinter
from py_bench._dynamic_benchmark import DynamicBenchmarkSetup, _create_dynamic_benchmark_instance


@dataclass
class BenchObjExecutionInfo:
    bench_object: TObj
    methods_to_bench: tuple[BenchMethod, ...]
    params_methods: tuple[ParamMarkedFunction]
    iteration_setup_methods: tuple[IterationSetupStub]

    @property
    def bench_class_name(self):
        return self.bench_object.__class__.__name__


class BenchRunner:

    @classmethod
    def run(cls, bench_obj: TObj,
            accuracy_settings: AccuracySettings = None,
            benchmark_executor: BenchmarkExecutor = None,
            result_comparer: ResultComparer = None,
            result_formatter: ResultFormatter = None,
            bench_call_visualiser: BenchmarkCallResultVisualizer = None) -> Optional[BenchObjExecutionResult]:

        bench_info = cls._analyze_bench(bench_obj)
        if not bench_info.methods_to_bench:
            print(f"No benchmark methods found in {bench_info.bench_class_name}!"
                  f" Add 'benchmark' decorator to benchmarking methods")
            return None
        else:
            print(f"{len(bench_info.methods_to_bench)} benchmark methods found in {bench_info.bench_class_name}")

        # run all found benchmarks
        executor = benchmark_executor or BenchmarkExecutor(accuracy_settings)
        bench_case_results = cls._execute_bench(bench_info, executor)

        # compare all case results
        comparer = result_comparer or ResultComparer()
        comparison_result = cls._compare_results(bench_case_results, comparer)

        # show result table
        ResultPrinter.print(bench_case_results, comparison_result, result_formatter)

        if bench_call_visualiser:
            bench_call_visualiser.visualize(comparison_result)

        return bench_case_results

    @classmethod
    def run_functions(cls, setup: DynamicBenchmarkSetup,
                      accuracy_settings: AccuracySettings = None,
                      benchmark_executor: BenchmarkExecutor = None,
                      result_comparer: ResultComparer = None,
                      result_formatter: ResultFormatter = None,
                      bench_call_visualiser: BenchmarkCallResultVisualizer = None) -> Optional[BenchObjExecutionResult]:

        return cls.run(
            _create_dynamic_benchmark_instance(setup),
            accuracy_settings, benchmark_executor, result_comparer, result_formatter, bench_call_visualiser
        )

    @classmethod
    def _analyze_bench(cls, bench_obj: TObj) -> BenchObjExecutionInfo:
        methods_to_bench: list[BenchMethod] = []
        params_methods: list[ParamMarkedFunction] = []
        iteration_setup_methods: list[IterationSetupStub] = []

        for method_name, method in inspect.getmembers(type(bench_obj)):
            for method_to_bench in BenchRegistry.bench_marked_functions:
                if method_to_bench == method:
                    methods_to_bench.append(method)

            if isinstance(method, ParamFunctionStub):
                params_methods.append(method.get_param_marked_function())

            if isinstance(method, IterationSetupStub):
                iteration_setup_methods.append(method)

        return BenchObjExecutionInfo(
            bench_obj,
            tuple(methods_to_bench),
            tuple(params_methods),
            tuple(iteration_setup_methods)
        )

    @classmethod
    def _execute_bench(cls, bench_exec_info: BenchObjExecutionInfo,
                       benchmark_executor: BenchmarkExecutor) -> BenchObjExecutionResult:
        bench_results: list[CaseBenchmarkExecutionResult] = []

        if bench_exec_info.params_methods:
            for param_case in cls._get_parameter_cases(bench_exec_info):
                cls._setup_parameters_case(param_case)
                cls._exec_iteration_setup(bench_exec_info)
                bench_results.append(cls._run_all_bench_methods(bench_exec_info, benchmark_executor, param_case))

        else:
            bench_results.append(cls._run_all_bench_methods(bench_exec_info, benchmark_executor))

        return BenchObjExecutionResult(bench_exec_info.bench_object, tuple(bench_results))

    @classmethod
    def _compare_results(cls, bench_obj_exec_results: BenchObjExecutionResult,
                         comparer: ResultComparer) -> list[tuple[dict[str, object], CaseResultsComparison]]:
        res = []

        for case_result in bench_obj_exec_results.bench_case_results:
            method_result_map = {method: res.function_result for method, res in case_result.bench_results.items()}
            comparison_results = comparer.compare_results(method_result_map)
            res.append((case_result.parameter_case, comparison_results))

        return res

    @classmethod
    def _get_parameter_cases(cls, bench_exec_info: BenchObjExecutionInfo) -> Iterable[tuple[ParameterCase]]:
        return itertools.product(*_get_function_argument_pairs(bench_exec_info))

    @classmethod
    def _setup_parameters_case(cls, param_cases: Iterable[ParameterCase]):
        for case in param_cases:
            BenchRegistry.setup_param_marked_function(case.method, case.arg)

    @classmethod
    def _exec_iteration_setup(cls, bench_exec_info: BenchObjExecutionInfo):
        for setup_method in bench_exec_info.iteration_setup_methods:
            setup_method(bench_exec_info.bench_object)

    @classmethod
    def _run_all_bench_methods(cls, bench_exec_info: BenchObjExecutionInfo, benchmark_executor: BenchmarkExecutor,
                               params: tuple[ParameterCase] = None) -> CaseBenchmarkExecutionResult:
        benchmark_results = {}

        parameter_cases_dict = {}
        if params:
            parameter_cases_dict = {param_case.name: param_case.arg for param_case in params}

        for bench_method in bench_exec_info.methods_to_bench:
            ctx = BenchmarkContext(bench_exec_info.bench_object, bench_method, parameter_cases_dict)
            exec_result = benchmark_executor.run_benchmark(ctx)
            benchmark_results[ctx.method_name] = exec_result

        return CaseBenchmarkExecutionResult(parameter_cases_dict, benchmark_results)


def _get_function_argument_pairs(bench_exec_info: BenchObjExecutionInfo) -> Iterable[tuple[ParameterCase]]:
    for param_method in bench_exec_info.params_methods:
        yield tuple(map(
            lambda arg: ParameterCase(param_method.function.__name__, param_method.function, arg),
            param_method.params
        ))
