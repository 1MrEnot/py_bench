from py_bench import benchmark


class DynamicBenchmarkSetup:
    def __init__(self, functions: tuple, *args, **kwargs):
        self.functions = functions
        self.args = args
        self.kwargs = kwargs


def _create_dynamic_benchmark_instance(setup: DynamicBenchmarkSetup):

    functions_dict = {
        function.__name__: create_function(function, function.__name__, setup.args, setup.kwargs)
        for function in setup.functions
    }

    dynamic_bench_type = type(
        "DynamicBenchmark",
        (object,),
        functions_dict
    )

    return dynamic_bench_type()

def create_function(func, name, args, kwargs):
    @benchmark
    def f(self):
        return func(*args, **kwargs)

    f.__name__ = name
    return f
