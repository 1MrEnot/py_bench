from itertools import chain
from typing import Callable, Iterable

from py_bench.result_visualizer.common import BenchResultViewModel, RunGroup
from py_bench.utils import rjust_fit_string


Table = list[tuple[str]]


class ResultFormatter:

    def format_result(self, view_model: BenchResultViewModel) -> str:
        pass


class MdResultFormatter(ResultFormatter):

    TIME_PREFIXES = ('ns', 'µs', 'ms', 's')
    DEFAULT_FLOAT_FORMAT = "%0.2f"
    BORDER = '|'
    NEW_LINE = '\r\n'

    def __init__(self, min_col_width=3, max_col_width=20, argument_mappers=None):
        self._min_col_width: int = min_col_width
        self._max_col_width: int = max_col_width
        self._argument_mappers: dict[str, callable] = argument_mappers or {}
        self._float_format = self.DEFAULT_FLOAT_FORMAT

    def format_result(self, view_model: BenchResultViewModel) -> str:
        # method | arg1 | arg2 | median | std_dev | equal?
        table = self._build_table(view_model)
        return f"{self.NEW_LINE}{view_model.bench_obj_name}{self.NEW_LINE}{table}{self.NEW_LINE}"

    @classmethod
    def _build_header(cls, bench_viewmodel: BenchResultViewModel) -> tuple[str]:
        res = ["Method"]
        res.extend(bench_viewmodel.argument_names)
        res.append("Median")
        res.append("StdDev")

        if bench_viewmodel.multiple_methods:
            res.append("Ratio")
            if bench_viewmodel.results_compared:
                res.append("EqGroup")

        return tuple(res)

    def _build_table(self, view_model: BenchResultViewModel) -> str:
        header = self._build_header(view_model)
        result_table = self._build_table_from_view_model(view_model)

        min_table_sizes = self._calc_min_column_sizes([header] + result_table)
        column_sizes = tuple(map(self._normalize_col_size, min_table_sizes))

        aligned_header = self.BORDER.join(self._align_row(header, column_sizes))
        header_splitter = self.BORDER.join(self._align_row([''] * len(header), column_sizes, '-'))
        joined_header = (aligned_header, header_splitter)

        aligned_table = (self._align_row(row, column_sizes) for row in result_table)
        joined_rows = map(self.BORDER.join, aligned_table)
        bordered_lines = map(self._add_borders, chain(joined_header, joined_rows))

        return self.NEW_LINE.join(bordered_lines)

    def _add_borders(self, line: str) -> str:
        return f"{self.BORDER}{line}{self.BORDER}"

    def _build_table_from_view_model(self, view_model: BenchResultViewModel) -> Table:
        split_groups = len(view_model.argument_names) >= 1
        mapper: Callable[[RunGroup, BenchResultViewModel], Table] = \
            self._map_group_to_list_with_split if split_groups else self._map_group_to_list_without_split

        result_table: Table = []
        for run_group in view_model.run_groups:
            result_table.extend(mapper(run_group, view_model))

        if split_groups:
            result_table = result_table[:-1]

        return result_table

    def _map_group_to_list_with_split(self, run_group: RunGroup, view_model: BenchResultViewModel) -> Table:
        res = self._map_group_to_list_without_split(run_group, view_model)
        res.append(tuple([''] * len(res[0])))
        return res

    def _map_group_to_list_without_split(self, run_group: RunGroup, view_model: BenchResultViewModel) -> Table:
        res = []

        for run in run_group.runs:
            row_list = [run.method]
            for arg_mapper, arg in zip(map(self._argument_mapper, view_model.argument_names), run_group.arguments):
                row_list.append(arg_mapper(arg))

            row_list.append(self._time_to_string(run.median))
            row_list.append(self._time_to_string(run.std_dev))

            if view_model.results_compared:
                row_list.append(self._float_format % run.ratio)
                if view_model.results_compared:
                    row_list.append(run.equality_group)

            res.append(tuple(str(el) for el in row_list))

        return res

    def _time_to_string(self, time: float) -> str:
        time, prefix = self._convert_time(time)
        return (self._float_format % time) + " " + prefix

    def _argument_mapper(self, argument_name: str) -> callable:
        return self._argument_mappers.get(argument_name, str)

    def _normalize_col_size(self, size):
        return min(max(size, self._min_col_width), self._max_col_width)

    @classmethod
    def _align_row(cls, row, sizes, fill_char=' ') -> Iterable[str]:
        return (f"{fill_char}{rjust_fit_string(el, size, fill_char)}{fill_char}" for el, size in zip(row, sizes))

    @classmethod
    def _calc_min_column_sizes(cls, table: Table) -> tuple[int]:
        if not table:
            return tuple()

        row_wise_sizes = tuple(map(lambda row: tuple(map(len, row)), table))
        res = row_wise_sizes[0]

        for row_sizes in row_wise_sizes[1:]:
            res = tuple(map(lambda pair: max(*pair), zip(res, row_sizes)))

        return res

    @classmethod
    def _convert_time(cls, time_in_ns) -> (float, str):
        time = time_in_ns
        prefix = ""

        for prefix in cls.TIME_PREFIXES:
            if time < 1000:
                return time, prefix

            time /= 1000

        return time, prefix
