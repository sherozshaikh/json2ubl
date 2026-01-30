"""Example usage of benchmark utilities."""

import json
from pathlib import Path

from json2ubl import json_dict_to_ubl_xml
from json2ubl.benchmark import Benchmark


def benchmark_invoice_conversion():
    """Benchmark invoice conversion performance."""
    # Load test invoice
    test_file = Path(__file__).parent.parent.parent / "test_files" / "invoice.json"
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return

    with open(test_file, "r") as f:
        documents = json.load(f)

    # Single run benchmark
    def convert():
        return json_dict_to_ubl_xml(documents)

    result = Benchmark.run(
        name="Single Invoice Conversion",
        func=convert,
        item_count=len(documents) if isinstance(documents, list) else 1,
    )

    print(f"Benchmark: {result.name}")
    print(f"  Total time: {result.total_time_ms}ms")
    print(f"  Items: {result.item_count}")
    print(f"  Avg time/item: {result.avg_time_ms}ms")
    print(f"  Throughput: {result.throughput} items/sec")

    return result


def benchmark_batch_invoices():
    """Benchmark batch invoice processing."""
    test_file = Path(__file__).parent.parent.parent / "test_files" / "batch_invoices.json"
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return

    with open(test_file, "r") as f:
        documents = json.load(f)

    def convert():
        return json_dict_to_ubl_xml(documents)

    # Multiple runs for better stats
    result = Benchmark.run_multiple(
        name="Batch Invoices (2 docs)",
        func=convert,
        iterations=3,
        item_count=len(documents),
    )

    print(f"\nBenchmark: {result.name}")
    print(f"  Total time: {result.total_time_ms}ms")
    print(f"  Items processed: {result.item_count}")
    print(f"  Avg time/item: {result.avg_time_ms}ms")
    print(f"  Min time: {result.min_time_ms}ms")
    print(f"  Max time: {result.max_time_ms}ms")
    print(f"  Throughput: {result.throughput} items/sec")

    return result


if __name__ == "__main__":
    print("=" * 60)
    print("json2ubl Performance Benchmarks")
    print("=" * 60)

    benchmark_invoice_conversion()
    benchmark_batch_invoices()

    print("\n" + "=" * 60)
