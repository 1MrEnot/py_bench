from dataclasses import dataclass, field
from datetime import timedelta
from time import perf_counter_ns, get_clock_info
from typing import Optional
import gc

from py_bench.loader import Loader
from py_bench.math_utils import MeasurementStatistics
from py_bench.common import BenchmarkContext, BenchmarkExecutionResult, TRes

TimeInNs = int

PERF_COUNTER_RESOLUTION = get_clock_info('perf_counter').resolution
MIN_INVOCATION_COUNT = 1
MAX_INVOCATION_COUNT = 1024*1024
INVOCATION_COUNT_MULTIPLY_BORDER = 16


@dataclass
class AccuracySettings:
    iteration_count: Optional[int] = None
    """How many iterations must be executed. Overrides min and max iteration count"""

    invocation_count: Optional[int] = None
    """How many method invocations per iteration must be executed. Overrides iteration time"""

    min_iteration_time: timedelta = field(default=timedelta(seconds=0.25))
    """How much time should one iteration at least take"""

    target_iteration_time: Optional[timedelta] = None
    """How much time should one iteration approximately take"""

    warmup_count: int = 1
    """How many iterations must be executed before any measurements"""

    subtract_overhead: bool = True

    min_iteration_count: int = 15
    max_iteration_count: int = 100
    max_relative_error: float = 0.02

    @staticmethod
    def default():
        return AccuracySettings()

    @staticmethod
    def fast():
        return AccuracySettings(min_iteration_time=timedelta(seconds=0.1), max_relative_error=0.2, min_iteration_count=5)

    @staticmethod
    def instant():
        return AccuracySettings(iteration_count=1, invocation_count=1, warmup_count=0, subtract_overhead=False)


class BenchmarkExecutor:

    def __init__(self, settings: AccuracySettings = None):
        self._settings = settings or AccuracySettings.default()

    def run_benchmark(self, ctx: BenchmarkContext) -> BenchmarkExecutionResult:
        self._warmup(ctx)
        invocation_count = self._find_perfect_invocation_count(ctx)
        ctx.log_started(invocation_count)
        workload_results = self._run_workload(invocation_count, ctx)
        measurements_stats = MeasurementStatistics.from_measurements(workload_results.times)

        return BenchmarkExecutionResult(
            workload_results.function_call_result,
            int(measurements_stats.mean),
            int(measurements_stats.median),
            int(measurements_stats.std_dev),
            int(measurements_stats.std_err),
        )

    def _warmup(self, ctx: BenchmarkContext):
        for _ in range(self._settings.warmup_count):
            ctx.call_method()

    def _find_perfect_invocation_count(self, ctx: BenchmarkContext) -> int:
        if self._settings.invocation_count:
            return self._settings.invocation_count

        if self._settings.target_iteration_time:
            return self._find_perfect_invocation_target(ctx)

        return self._find_perfect_invocation_auto(ctx)

    def _find_perfect_invocation_auto(self, ctx: BenchmarkContext) -> int:
        invocation_count = 1
        min_iter_time_ns = self._settings.min_iteration_time.microseconds * 1000

        while True:
            iteration_time = self._run_iteration(invocation_count, ctx)
            operation_error = 2 * PERF_COUNTER_RESOLUTION / invocation_count
            operation_max_err = iteration_time / invocation_count * self._settings.max_relative_error

            done = operation_error < operation_max_err and iteration_time >= min_iter_time_ns
            if done or invocation_count > MAX_INVOCATION_COUNT:
                return invocation_count

            if invocation_count < INVOCATION_COUNT_MULTIPLY_BORDER:
                invocation_count += 1
            else:
                invocation_count *= 2

    def _find_perfect_invocation_target(self, ctx: BenchmarkContext) -> int:
        invocation_count = 1
        target_iter_time_ns = self._settings.min_iteration_time.microseconds * 1000
        down_count = 0    # iter count, where newCount < oldCount

        while True:
            iteration_time = self._run_iteration(invocation_count, ctx)
            new_invocation_count = invocation_count * target_iter_time_ns / iteration_time

            if new_invocation_count < invocation_count:
                down_count += 1

            if abs(new_invocation_count < invocation_count) <= 1 or down_count >= 3:
                return invocation_count

    def _run_workload(self, invocation_count: int, ctx: BenchmarkContext) -> 'WorkloadResult':
        iteration_overhead = self._get_overhead_for_invocation_count(invocation_count)

        if self._settings.iteration_count:
            return self._run_workload_specific(invocation_count, iteration_overhead, ctx)

        return self._run_workload_auto(invocation_count, iteration_overhead, ctx)

    def _run_workload_specific(self, invocation_count: int,
                               iteration_overhead: TimeInNs, ctx: BenchmarkContext) -> 'WorkloadResult':
        workload_result = WorkloadResult()
        iter_count = self._settings.iteration_count

        with Loader(ctx.method_name, iter_count) as loader:
            for i in range(iter_count):
                iteration_result = self._run_iteration_corrected(iteration_overhead, invocation_count, ctx)
                workload_result.add_iteration_result(iteration_result)
                loader.set_stage(i + 1)

        return workload_result

    def _run_workload_auto(self, invocation_count: int,
                           iteration_overhead: TimeInNs, ctx: BenchmarkContext) -> 'WorkloadResult':
        workload_result = WorkloadResult()
        iteration_idx = 0
        prev_stage = 0

        with Loader(ctx.method_name) as loader:
            while True:
                iteration_idx += 1

                iteration_res = self._run_iteration_corrected(iteration_overhead, invocation_count, ctx)
                workload_result.add_iteration_result(iteration_res)

                stats = MeasurementStatistics.from_measurements(workload_result.times)
                margin = stats.confidence_interval.margin
                max_err = stats.mean * self._settings.max_relative_error

                conv_stage = max_err / margin
                max_iter_stage = iteration_idx / self._settings.max_iteration_count
                min_iter_stage = iteration_idx / self._settings.min_iteration_count
                cur_stage = max(prev_stage, max_iter_stage, min(conv_stage, min_iter_stage))
                loader.set_stage(cur_stage)
                prev_stage = cur_stage

                if iteration_idx >= self._settings.min_iteration_count and margin < max_err:
                    break

                if iteration_idx >= self._settings.max_iteration_count:
                    break

        return workload_result

    @classmethod
    def _run_iteration_corrected(cls, overhead: int, invocation_count: int, ctx: BenchmarkContext) -> 'IterationResult':
        gc.collect()
        start = perf_counter_ns()

        res = None
        for _ in range(invocation_count):
            res = ctx.call_method()

        time_in_ns = int((perf_counter_ns() - start - overhead) / invocation_count)
        return IterationResult(res, time_in_ns)

    @classmethod
    def _run_iteration(cls, invocation_count: int, ctx: BenchmarkContext) -> TimeInNs:
        start = perf_counter_ns()
        for _ in range(invocation_count):
            ctx.call_method()
        return perf_counter_ns() - start

    def _get_overhead_for_invocation_count(self, invocation_count: int) -> TimeInNs:
        if not self._settings.subtract_overhead:
            return 0

        start = perf_counter_ns()
        for _ in range(invocation_count):
            empty_function(self)
        stop = perf_counter_ns()
        return stop - start


@dataclass
class IterationResult:
    function_call_result: TRes
    time: TimeInNs

@dataclass
class WorkloadResult:
    function_call_result: TRes = None
    times: list[TimeInNs] = field(default_factory=list)

    def add_iteration_result(self, iteration_result: IterationResult):
        self.function_call_result = iteration_result.function_call_result
        self.times.append(iteration_result.time)

def empty_function(*args):
    return args
