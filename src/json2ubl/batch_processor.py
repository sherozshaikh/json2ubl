"""Parallel batch processing for JSON to UBL conversion."""

import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List

from .config import get_logger

logger = get_logger(__name__)


class BatchProcessor:
    """Process documents in parallel using thread pool."""

    def __init__(self, max_workers: int = None):
        """
        Initialize batch processor.

        Args:
            max_workers: Number of threads (None = auto-detect CPU cores, min 8)
        """
        if max_workers is None:
            cpu_count = multiprocessing.cpu_count()
            self.max_workers = max(8, cpu_count)
        else:
            self.max_workers = max(1, max_workers)

        logger.debug(f"BatchProcessor initialized with {self.max_workers} workers")

    def process(
        self,
        items: List[Any],
        worker_fn: Callable[[Any], Dict[str, Any]],
        ordered: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Process items in parallel.

        Args:
            items: List of items to process
            worker_fn: Function to apply to each item
            ordered: If True, maintain input order in results

        Returns:
            List of results
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(worker_fn, item): i for i, item in enumerate(items)}

            for future in as_completed(futures):
                idx = futures[future]
                try:
                    result = future.result()
                    if ordered:
                        results.append((idx, result))
                    else:
                        results.append(result)
                except Exception as e:
                    logger.error(f"Worker failed for item {idx}: {e}")
                    if ordered:
                        results.append((idx, {"error": str(e)}))
                    else:
                        results.append({"error": str(e)})

        # Sort by original index if ordered
        if ordered:
            results.sort(key=lambda x: x[0])
            return [r[1] for r in results]

        return results
