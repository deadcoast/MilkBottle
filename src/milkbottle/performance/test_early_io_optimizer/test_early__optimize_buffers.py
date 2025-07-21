# test_io_optimizer_optimize_buffers.py

import pytest

from milkbottle.performance.io_optimizer import IOOptimizer, IOStats


@pytest.mark.usefixtures("io_optimizer")
class TestIOOptimizerOptimizeBuffers:
    """Unit tests for IOOptimizer._optimize_buffers method."""

    @pytest.fixture(autouse=True)
    def io_optimizer(self):
        """Fixture to create a fresh IOOptimizer for each test."""
        self.optimizer = IOOptimizer(buffer_size=8192, max_concurrent_operations=10)

    # -------------------- Happy Path Tests --------------------

    @pytest.mark.happy_path
    def test_no_read_operations_returns_current_buffer(self):
        """
        Test that when there are no read operations, the buffer size remains unchanged,
        and no suggestions are made.
        """
        self.optimizer.io_stats = IOStats(read_bytes=0, read_operations=0)
        result = self.optimizer._optimize_buffers()
        assert result["success"] is True
        assert result["buffer_optimization"]["current_size"] == 8192
        assert result["buffer_optimization"]["optimal_size"] == 8192
        assert result["buffer_optimization"]["should_adjust"] is False
        assert result["suggestions"] == []

    @pytest.mark.happy_path
    def test_optimal_buffer_size_increases_with_large_reads(self):
        """
        Test that with large average read size, the optimal buffer size increases,
        and a suggestion is made if the difference is significant.
        """
        self.optimizer.io_stats = IOStats(read_bytes=200_000, read_operations=2)
        # avg_read_size = 100_000, optimal = min(65536, 200_000) = 65536
        result = self.optimizer._optimize_buffers()
        assert result["success"] is True
        assert result["buffer_optimization"]["current_size"] == 8192
        assert result["buffer_optimization"]["optimal_size"] == 65536
        assert result["buffer_optimization"]["should_adjust"] is True
        assert any("Consider adjusting buffer size" in s for s in result["suggestions"])

    @pytest.mark.happy_path
    def test_optimal_buffer_size_decreases_with_small_reads(self):
        """
        Test that with small average read size, the optimal buffer size decreases,
        but not below 4096, and a suggestion is made if the difference is significant.
        """
        self.optimizer.io_stats = IOStats(read_bytes=9000, read_operations=10)
        # avg_read_size = 900, optimal = max(4096, 1800) = 4096
        result = self.optimizer._optimize_buffers()
        assert result["success"] is True
        assert result["buffer_optimization"]["current_size"] == 8192
        assert result["buffer_optimization"]["optimal_size"] == 4096
        assert result["buffer_optimization"]["should_adjust"] is True
        assert any("Consider adjusting buffer size" in s for s in result["suggestions"])

    @pytest.mark.happy_path
    def test_no_suggestion_when_difference_is_small(self):
        """
        Test that if the optimal buffer size is close to the current size (<=1024 difference),
        no suggestion is made.
        """
        self.optimizer.io_stats = IOStats(read_bytes=18_000, read_operations=8)
        # avg_read_size = 2250, optimal = max(4096, 4500) = 4500
        # difference = 8192 - 4500 = 3692 > 1024, so suggestion should be made
        # Let's adjust so difference is <= 1024
        self.optimizer.settings["buffer_size"] = 5000
        self.optimizer.io_stats = IOStats(
            read_bytes=10_000, read_operations=2
        )  # avg=5000, optimal=10000
        # difference = 5000
        # Let's try with avg_read_size = 3000, optimal = 6000, current = 5000, diff = 1000
        self.optimizer.settings["buffer_size"] = 5000
        self.optimizer.io_stats = IOStats(
            read_bytes=6000, read_operations=2
        )  # avg=3000, optimal=6000
        result = self.optimizer._optimize_buffers()
        assert result["success"] is True
        assert result["buffer_optimization"]["should_adjust"] is False
        assert result["suggestions"] == []

    @pytest.mark.happy_path
    def test_bulk_operations_suggestion(self):
        """
        Test that when read_operations > 1000, a bulk operation suggestion is included.
        """
        self.optimizer.io_stats = IOStats(read_bytes=2_000_000, read_operations=2000)
        result = self.optimizer._optimize_buffers()
        assert result["success"] is True
        assert any("bulk operations" in s for s in result["suggestions"])

    # -------------------- Edge Case Tests --------------------

    @pytest.mark.edge_case
    def test_optimal_buffer_size_cannot_exceed_65536(self):
        """
        Test that the optimal buffer size is capped at 65536 even for very large reads.
        """
        self.optimizer.io_stats = IOStats(read_bytes=10_000_000, read_operations=1)
        result = self.optimizer._optimize_buffers()
        assert result["success"] is True
        assert result["buffer_optimization"]["optimal_size"] == 65536

    @pytest.mark.edge_case
    def test_optimal_buffer_size_cannot_go_below_4096(self):
        """
        Test that the optimal buffer size is floored at 4096 even for very small reads.
        """
        self.optimizer.io_stats = IOStats(read_bytes=100, read_operations=10)
        result = self.optimizer._optimize_buffers()
        assert result["success"] is True
        assert result["buffer_optimization"]["optimal_size"] == 4096

    @pytest.mark.edge_case
    def test_zero_read_bytes_with_positive_operations(self):
        """
        Test that if read_bytes is zero but read_operations is positive,
        optimal buffer size is floored at 4096.
        """
        self.optimizer.io_stats = IOStats(read_bytes=0, read_operations=5)
        result = self.optimizer._optimize_buffers()
        assert result["success"] is True
        assert result["buffer_optimization"]["optimal_size"] == 4096

    @pytest.mark.edge_case
    def test_negative_read_bytes_and_operations(self):
        """
        Test that negative read_bytes or read_operations do not cause a crash,
        and optimal buffer size is set to current buffer size.
        """
        self.optimizer.io_stats = IOStats(read_bytes=-100, read_operations=-5)
        result = self.optimizer._optimize_buffers()
        assert result["success"] is True
        # Since read_operations <= 0, optimal = current
        assert (
            result["buffer_optimization"]["optimal_size"]
            == self.optimizer.settings["buffer_size"]
        )

    @pytest.mark.edge_case
    def test_missing_buffer_size_in_settings(self, monkeypatch):
        """
        Test that if 'buffer_size' is missing from settings, an error is returned.
        """
        del self.optimizer.settings["buffer_size"]
        result = self.optimizer._optimize_buffers()
        assert result["success"] is False
        assert "buffer_size" in result["error"]

    @pytest.mark.edge_case
    def test_exception_in_optimization_logic(self, monkeypatch):
        """
        Test that if an exception is raised inside the try block, it is caught and reported.
        """

        # Patch io_stats to raise an exception on attribute access
        class BadStats:
            @property
            def read_operations(self):
                raise RuntimeError("Simulated failure")

        self.optimizer.io_stats = BadStats()
        result = self.optimizer._optimize_buffers()
        assert result["success"] is False
        assert "Simulated failure" in result["error"]
