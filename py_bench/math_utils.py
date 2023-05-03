from dataclasses import dataclass
from scipy.stats import t as t_student


class ConfidenceInterval:
    def __init__(self, mean, std_err, n, confidence_level=0.99):
        self.mean = mean
        self.std_err = std_err
        self.n = n
        self.level = confidence_level
        self.margin = float("nan") if n <= 2 else std_err * _get_z_value(n, confidence_level)

    @property
    def lower(self):
        return self.mean - self.margin

    @property
    def upper(self):
        return self.mean + self.margin


@dataclass
class MeasurementStatistics:
    mean: float
    median: float
    std_dev: float
    std_err: float
    confidence_interval: ConfidenceInterval

    @staticmethod
    def from_measurements(x: list) -> 'MeasurementStatistics':
        x_sorted = sorted(x)

        s = sum(x)
        n = len(x)
        mean = s / n
        median = _median(x)

        variance = _variance(x_sorted)
        std_dev = variance ** 0.5
        std_err = std_dev / (n ** 0.5)
        conf_interval = ConfidenceInterval(mean, std_err, n)
        return MeasurementStatistics(mean, median, std_dev, std_err, conf_interval)

def _get_z_value(n, level):
    return t_student.ppf((1 + level) / 2, n - 1)

def _median(sorted_x: list) -> float:
    n = len(sorted_x)
    return sorted_x[n//2]

def _variance(sorted_x: list) -> float:
    n = len(sorted_x)
    avg = sum(sorted_x) / n
    return sum(((x - avg) * (x + avg) for x in sorted_x)) / n
