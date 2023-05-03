# PyBench
PyBench is [BenchmarkDotNet](https://github.com/dotnet/BenchmarkDotNet)-inspired benchmark library for python,
aimed to make python code optimisation much easier and safer

## Features
- Benchmark parametrisation
- Automatic perfect execution and iteration count calculation
- Benchmark methods call result comparison
- Function call overhead awareness
- Highly customisable benchmark execution and result formatting


## Example
There's the simplest example of PyBench usage 

```python
from py_bench import param, benchmark, BenchRunner

class PowBench:

    @param(2, 3)
    def base(self): pass

    @param(10, 100)
    def exponent(self): pass

    @benchmark
    def pow(self): 
        return self.base() ** self.exponent()

    @benchmark
    def loop_pow(self):
        res = 1
        base = self.base()

        for _ in range(self.exponent()):
            res *= base

        return res


if __name__ == '__main__':
    BenchRunner.run(PowBench())
```

This example writes markdown-formatted table to console:
```
PowBench
|   Method | base | exponent |    Median |   StdDev | Ratio | EqGroup |
|----------|------|----------|-----------|----------|-------|---------|
| loop_pow |    2 |       10 | 531.00 ns |  8.00 ns |  1.35 |       0 |
|      pow |    2 |       10 | 392.00 ns |  6.00 ns |  1.00 |       0 |
|          |      |          |           |          |       |         |
| loop_pow |    2 |      100 |   3.65 µs | 81.00 ns |  7.19 |       0 |
|      pow |    2 |      100 | 507.00 ns | 15.00 ns |  1.00 |       0 |
|          |      |          |           |          |       |         |
| loop_pow |    3 |       10 | 564.00 ns | 13.00 ns |  1.42 |       0 |
|      pow |    3 |       10 | 398.00 ns |  8.00 ns |  1.00 |       0 |
|          |      |          |           |          |       |         |
| loop_pow |    3 |      100 |   3.86 µs | 32.00 ns |  7.83 |       0 |
|      pow |    3 |      100 | 493.00 ns |  3.00 ns |  1.00 |       0 |
```

Also, you can see current benchmark execution status with time spent and approximate state 
in console:
```
loop_pow      ------------- DONE -------------- 100% • 00:04
pow           ------------- DONE -------------- 100% • 00:07
loop_pow      ------------- DONE -------------- 100% • 00:03
pow           ------------- DONE -------------- 100% • 00:06
loop_pow      ███████████████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  47% • 00:02
```

### Equality groups
Speeding code up is good, but it's very important to keep results the same.
PyBench compares benchmarks call execution results and group by 'EqualityGroups'.
There is class with incorrect function implementation and corresponding execution result. 
```python
class PowBench:
    base = 2
    exponent = 10

    @benchmark
    def pow(self):
        return self.base ** self.exponent

    @benchmark
    def incorrect_pow(self):
        return self.base * self.exponent

    @benchmark
    def loop_pow(self):
        res = 1
        base = self.base

        for _ in range(self.exponent):
            res *= base

        return res
```

Pay attention to `EqGroup` column.
```
|        Method |    Median |  StdDev | Ratio | EqGroup |
|---------------|-----------|---------|-------|---------|
| incorrect_pow |  66.00 ns | 0.00 ns |  1.00 |       0 |
|      loop_pow | 374.00 ns | 3.00 ns |  5.67 |       1 |
|           pow | 243.00 ns | 2.00 ns |  3.68 |       1 |
```

### Accuracy settings
Sometimes default with accuracy settings benchmark execution takes too much time, or 
we would like to execute benchmarks as fast as possible, just to make sure, that results are equal.
You can tune benchmark execution time, using accuracy settings with
preferred execution or iteration time, warmup execution count, and much more.

Invocation is single function call, no matter how fast it is.\
Iteration is one or more invocations.\
Per each iteration average invocation time is taken into account.

```python
from py_bench import AccuracySettings
from datetime import timedelta

AccuracySettings.default()    # has warmup, overhead calculation, finds perfect invocation count 
AccuracySettings.fast()       # the same, but much faster
AccuracySettings.instant()    # execute twice

# warms up with 3 invocations,
# finds function invocation count, so it approximately be equal to 2 second,
# and executes 15 iterations with found invocation count each
# without overhead calculation
AccuracySettings(
    warmup_count=3,
    target_iteration_time=timedelta(seconds=2),    
    iteration_count=15,
    subtract_overhead=False,
)
```

### Call result visualisation
You can visualise call results as you wish, by inheriting base `BenchmarkCallResultVisualizer`.

There's built-in `NumpyArrayConsoleVisualizer`,
that prints to console absolute and relative difference between numpy arrays:
```python
from py_bench import benchmark, BenchRunner, NumpyArrayConsoleVisualizer
import numpy as np

class NpPowBench:
    base = np.linspace(0, 1)
    exponent = 10
    
    @benchmark
    def pow(self): 
        return self.base ** self.exponent

    @benchmark
    def incorrect_pow(self):
        return self.base * self.exponent


if __name__ == '__main__':
    BenchRunner.run(NpPowBench(), bench_call_visualiser=NumpyArrayConsoleVisualizer())
```
Console output:
```
PowBench
|        Method |  Median |   StdDev | Ratio | EqGroup |
|---------------|---------|----------|-------|---------|
| incorrect_pow | 1.08 µs | 29.00 ns |  1.00 |       0 |
|           pow | 2.19 µs | 26.00 ns |  2.04 |       1 |

Case difference: 
0-1: abs_delta = 9.00, rel_delta = -12132626656.36 %
```


### Third-party
This library contains algorithms uses terminology from [BenchmarkDotNet](https://github.com/dotnet/BenchmarkDotNet).
Check it out, if you want to write benchmarks on .NET!
