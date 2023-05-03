from dataclasses import dataclass
from typing import Iterable


@dataclass
class ParamMarkedFunction:
    function: callable
    stub: 'ParamFunctionStub'
    params: Iterable


class ParamFunctionStub:
    def __init__(self, function, args):
        self.function: callable = function
        self.args: Iterable = args
        self.current_value = None

    def __call__(self, *args, **kwargs):
        return self.current_value

    def get_param_marked_function(self):
        return ParamMarkedFunction(self.function, self, self.args)


class IterationSetupStub:

    def __init__(self, function: callable):
        self._function = function

    def __call__(self, *args, **kwargs):
        self._function(*args, **kwargs)

    def exec(self):
        self._function()


class BenchRegistry:
    bench_marked_functions: list[callable] = []
    _param_function_stubs: list[ParamFunctionStub] = []
    _iteration_setup_stubs: list[IterationSetupStub] = []

    @classmethod
    def save_param_marked_function(cls, func: callable, args: Iterable) -> ParamFunctionStub:
        stub = ParamFunctionStub(func, args)
        cls._param_function_stubs.append(stub)
        return stub

    @classmethod
    def setup_param_marked_function(cls, func: callable, arg):
        for stub in cls._param_function_stubs:
            if stub.function == func:
                stub.current_value = arg
                return

        raise Exception(f"There is no {func} in {cls} registry")

    @classmethod
    def save_case_setup_function(cls, func: callable) -> IterationSetupStub:
        stub = IterationSetupStub(func)
        cls._iteration_setup_stubs.append(stub)
        return stub
