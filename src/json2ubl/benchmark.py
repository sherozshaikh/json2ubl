import time
from dataclasses import asdict, dataclass
from typing import Any, Callable, Dict


@dataclass
class BenchmarkResult:
    """Benchmark result data."""

    name: str
    total_time_ms: float
    item_count: int
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    throughput: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Benchmark:
    """Simple benchmarking utility."""

    @staticmethod
    def run(
        name: str,
        func: Callable,
        *args,
        **kwargs,
    ) -> BenchmarkResult:
        """Run benchmark on function."""
        start = time.time()
        _ = func(*args, **kwargs)
        elapsed_ms = (time.time() - start) * 1000

        item_count = kwargs.get("item_count", 1)
        avg_time = elapsed_ms / item_count if item_count > 0 else 0

        benchmark_result = BenchmarkResult(
            name=name,
            total_time_ms=round(elapsed_ms, 2),
            item_count=item_count,
            avg_time_ms=round(avg_time, 2),
            min_time_ms=0.0,
            max_time_ms=round(elapsed_ms, 2),
            throughput=(round(item_count / (elapsed_ms / 1000), 2) if elapsed_ms > 0 else 0),
        )

        return benchmark_result

    @staticmethod
    def run_multiple(
        name: str,
        func: Callable,
        iterations: int = 3,
        *args,
        **kwargs,
    ) -> BenchmarkResult:
        """Run benchmark multiple times for stats."""
        times = []

        for _ in range(iterations):
            start = time.time()
            func(*args, **kwargs)
            elapsed_ms = (time.time() - start) * 1000
            times.append(elapsed_ms)

        item_count = kwargs.get("item_count", 1)
        total_time = sum(times)
        avg_time = total_time / len(times)

        benchmark_result = BenchmarkResult(
            name=name,
            total_time_ms=round(total_time, 2),
            item_count=item_count * iterations,
            avg_time_ms=round(avg_time, 2),
            min_time_ms=round(min(times), 2),
            max_time_ms=round(max(times), 2),
            throughput=round((item_count * iterations) / (total_time / 1000), 2),
        )

        return benchmark_result
