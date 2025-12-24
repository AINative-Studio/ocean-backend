#!/usr/bin/env python3
"""
Ocean Backend Performance Benchmark

Benchmarks critical operations to validate performance targets:
- Page CRUD: <50ms p95
- Block CRUD: <100ms p95
- Search: <200ms p95
- List operations: <100ms p95

Usage:
    python scripts/benchmark.py
    python scripts/benchmark.py --iterations 100
    python scripts/benchmark.py --verbose
"""

import asyncio
import sys
import time
import statistics
from typing import List, Dict, Tuple
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ocean_service import OceanService
from app.config import settings


class PerformanceBenchmark:
    """Benchmark Ocean backend critical operations."""

    def __init__(self, iterations: int = 50, verbose: bool = False):
        """
        Initialize benchmark.

        Args:
            iterations: Number of times to run each operation
            verbose: Print detailed timing for each iteration
        """
        self.iterations = iterations
        self.verbose = verbose
        self.service = OceanService(
            api_url=settings.ZERODB_API_URL,
            api_key=settings.ZERODB_API_KEY,
            project_id=settings.ZERODB_PROJECT_ID
        )
        # Test org and user IDs
        self.org_id = "benchmark_org"
        self.user_id = "benchmark_user"

    async def time_operation(
        self,
        operation_name: str,
        operation_func,
        *args,
        **kwargs
    ) -> Tuple[List[float], any]:
        """
        Time an operation multiple times and return statistics.

        Args:
            operation_name: Name of operation for logging
            operation_func: Async function to benchmark
            *args, **kwargs: Arguments to pass to operation

        Returns:
            Tuple of (timing_list, last_result)
        """
        timings = []
        last_result = None

        for i in range(self.iterations):
            start = time.perf_counter()
            try:
                result = await operation_func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                timings.append(duration_ms)
                last_result = result

                if self.verbose:
                    print(f"  [{i+1}/{self.iterations}] {operation_name}: {duration_ms:.2f}ms")

            except Exception as e:
                print(f"  ERROR on iteration {i+1}: {e}")
                continue

        return timings, last_result

    def calculate_stats(self, timings: List[float]) -> Dict[str, float]:
        """
        Calculate statistics from timing list.

        Args:
            timings: List of timing measurements in milliseconds

        Returns:
            Dictionary with mean, median, p95, p99, min, max
        """
        if not timings:
            return {
                "mean": 0,
                "median": 0,
                "p95": 0,
                "p99": 0,
                "min": 0,
                "max": 0,
                "count": 0
            }

        sorted_timings = sorted(timings)
        return {
            "mean": statistics.mean(timings),
            "median": statistics.median(timings),
            "p95": sorted_timings[int(len(sorted_timings) * 0.95)],
            "p99": sorted_timings[int(len(sorted_timings) * 0.99)],
            "min": min(timings),
            "max": max(timings),
            "count": len(timings)
        }

    def print_stats(self, operation_name: str, stats: Dict[str, float], target_p95: float):
        """
        Print formatted statistics with pass/fail status.

        Args:
            operation_name: Name of operation
            stats: Statistics dictionary
            target_p95: Target p95 latency in milliseconds
        """
        passed = stats["p95"] <= target_p95
        status = "✓ PASS" if passed else "✗ FAIL"
        status_color = "\033[92m" if passed else "\033[91m"
        reset_color = "\033[0m"

        print(f"\n{operation_name}:")
        print(f"  Mean:   {stats['mean']:.2f}ms")
        print(f"  Median: {stats['median']:.2f}ms")
        print(f"  P95:    {stats['p95']:.2f}ms (target: <{target_p95}ms) {status_color}{status}{reset_color}")
        print(f"  P99:    {stats['p99']:.2f}ms")
        print(f"  Min:    {stats['min']:.2f}ms")
        print(f"  Max:    {stats['max']:.2f}ms")
        print(f"  Count:  {stats['count']} iterations")

    async def benchmark_page_create(self) -> Dict[str, float]:
        """Benchmark page creation."""
        print("\n[1/6] Benchmarking page creation...")

        async def create_page():
            return await self.service.create_page(
                org_id=self.org_id,
                user_id=self.user_id,
                page_data={
                    "title": f"Benchmark Page {time.time()}",
                    "icon": "📊",
                    "metadata": {"benchmark": True}
                }
            )

        timings, last_page = await self.time_operation("Page Create", create_page)
        stats = self.calculate_stats(timings)
        self.print_stats("Page Create", stats, target_p95=50.0)

        # Store page_id for other benchmarks
        self.test_page_id = last_page["page_id"] if last_page else None
        return stats

    async def benchmark_page_read(self) -> Dict[str, float]:
        """Benchmark page retrieval."""
        print("\n[2/6] Benchmarking page read...")

        if not self.test_page_id:
            print("  SKIPPED: No test page created")
            return {}

        async def read_page():
            return await self.service.get_page(
                page_id=self.test_page_id,
                org_id=self.org_id
            )

        timings, _ = await self.time_operation("Page Read", read_page)
        stats = self.calculate_stats(timings)
        self.print_stats("Page Read", stats, target_p95=50.0)
        return stats

    async def benchmark_page_list(self) -> Dict[str, float]:
        """Benchmark page listing."""
        print("\n[3/6] Benchmarking page list...")

        async def list_pages():
            return await self.service.get_pages(
                org_id=self.org_id,
                pagination={"limit": 50, "offset": 0}
            )

        timings, _ = await self.time_operation("Page List", list_pages)
        stats = self.calculate_stats(timings)
        self.print_stats("Page List", stats, target_p95=100.0)
        return stats

    async def benchmark_block_create(self) -> Dict[str, float]:
        """Benchmark block creation."""
        print("\n[4/6] Benchmarking block creation...")

        if not self.test_page_id:
            print("  SKIPPED: No test page created")
            return {}

        async def create_block():
            return await self.service.create_block(
                page_id=self.test_page_id,
                org_id=self.org_id,
                user_id=self.user_id,
                block_data={
                    "block_type": "text",
                    "content": {
                        "text": f"Benchmark block created at {time.time()}"
                    }
                }
            )

        timings, last_block = await self.time_operation("Block Create", create_block)
        stats = self.calculate_stats(timings)
        self.print_stats("Block Create", stats, target_p95=100.0)

        # Store block_id for search benchmark
        self.test_block_id = last_block["block_id"] if last_block else None
        return stats

    async def benchmark_block_list(self) -> Dict[str, float]:
        """Benchmark block listing."""
        print("\n[5/6] Benchmarking block list...")

        if not self.test_page_id:
            print("  SKIPPED: No test page created")
            return {}

        async def list_blocks():
            return await self.service.get_blocks_by_page(
                page_id=self.test_page_id,
                org_id=self.org_id,
                pagination={"limit": 100, "offset": 0}
            )

        timings, _ = await self.time_operation("Block List", list_blocks)
        stats = self.calculate_stats(timings)
        self.print_stats("Block List", stats, target_p95=100.0)
        return stats

    async def benchmark_search(self) -> Dict[str, float]:
        """Benchmark semantic search."""
        print("\n[6/6] Benchmarking semantic search...")

        async def search_blocks():
            return await self.service.search_blocks(
                query="benchmark test performance",
                org_id=self.org_id,
                limit=10
            )

        timings, _ = await self.time_operation("Semantic Search", search_blocks)
        stats = self.calculate_stats(timings)
        self.print_stats("Semantic Search", stats, target_p95=200.0)
        return stats

    async def cleanup(self):
        """Clean up test data."""
        print("\n[Cleanup] Removing test data...")
        try:
            if hasattr(self, 'test_page_id') and self.test_page_id:
                await self.service.delete_page(self.test_page_id, self.org_id)
                print("  ✓ Test page and blocks deleted")
        except Exception as e:
            print(f"  Warning: Cleanup failed: {e}")

    async def run_all(self) -> Dict[str, Dict[str, float]]:
        """Run all benchmarks and return results."""
        print(f"\n{'='*70}")
        print(f"Ocean Backend Performance Benchmark")
        print(f"{'='*70}")
        print(f"Iterations per operation: {self.iterations}")
        print(f"Verbose mode: {self.verbose}")
        print(f"{'='*70}")

        results = {
            "page_create": await self.benchmark_page_create(),
            "page_read": await self.benchmark_page_read(),
            "page_list": await self.benchmark_page_list(),
            "block_create": await self.benchmark_block_create(),
            "block_list": await self.benchmark_block_list(),
            "search": await self.benchmark_search(),
        }

        # Cleanup
        await self.cleanup()

        # Print summary
        self.print_summary(results)

        return results

    def print_summary(self, results: Dict[str, Dict[str, float]]):
        """Print summary of all benchmarks."""
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")

        targets = {
            "page_create": 50.0,
            "page_read": 50.0,
            "page_list": 100.0,
            "block_create": 100.0,
            "block_list": 100.0,
            "search": 200.0
        }

        passed = 0
        failed = 0

        for operation, stats in results.items():
            if not stats:
                continue

            target = targets.get(operation, 100.0)
            p95 = stats.get("p95", float('inf'))
            status = "PASS" if p95 <= target else "FAIL"

            if status == "PASS":
                passed += 1
                status_color = "\033[92m"
            else:
                failed += 1
                status_color = "\033[91m"

            reset_color = "\033[0m"
            print(f"{operation:20} P95: {p95:6.2f}ms (target: <{target:3.0f}ms) {status_color}{status}{reset_color}")

        print(f"{'='*70}")
        print(f"Results: {passed} passed, {failed} failed")
        print(f"{'='*70}\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Ocean Backend Performance Benchmark")
    parser.add_argument(
        "--iterations",
        type=int,
        default=50,
        help="Number of iterations per operation (default: 50)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed timing for each iteration"
    )
    args = parser.parse_args()

    benchmark = PerformanceBenchmark(
        iterations=args.iterations,
        verbose=args.verbose
    )

    try:
        await benchmark.run_all()
    except KeyboardInterrupt:
        print("\n\nBenchmark interrupted by user")
        await benchmark.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\n\nBenchmark failed with error: {e}")
        import traceback
        traceback.print_exc()
        await benchmark.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
