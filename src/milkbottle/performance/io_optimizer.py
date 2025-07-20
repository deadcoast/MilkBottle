"""I/O optimization system for MilkBottle."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiofiles

logger = logging.getLogger("milkbottle.io_optimizer")


@dataclass
class IOStats:
    """I/O statistics."""

    read_bytes: int = 0
    write_bytes: int = 0
    read_operations: int = 0
    write_operations: int = 0
    read_time: float = 0.0
    write_time: float = 0.0
    avg_read_time: float = 0.0
    avg_write_time: float = 0.0
    throughput_mbps: float = 0.0


@dataclass
class FileIOInfo:
    """File I/O information."""

    file_path: str
    size_bytes: int
    read_count: int = 0
    write_count: int = 0
    last_accessed: float = 0.0
    access_pattern: str = "unknown"


class IOOptimizer:
    """Advanced I/O optimization system."""

    def __init__(self, buffer_size: int = 8192, max_concurrent_operations: int = 10):
        """Initialize I/O optimizer.

        Args:
            buffer_size: Default buffer size for I/O operations
            max_concurrent_operations: Maximum concurrent I/O operations
        """
        self.buffer_size = buffer_size
        self.max_concurrent_operations = max_concurrent_operations
        self.io_stats = IOStats()
        self.file_io_history: Dict[str, FileIOInfo] = {}
        self.optimization_history: List[Dict[str, Any]] = []

        # I/O optimization settings
        self.settings = {
            "enable_buffering": True,
            "enable_async_io": True,
            "enable_compression": False,
            "enable_caching": True,
            "buffer_size": buffer_size,
            "max_concurrent": max_concurrent_operations,
        }

        logger.info("I/O optimizer initialized")

    def get_io_stats(self) -> IOStats:
        """Get current I/O statistics.

        Returns:
            Current I/O statistics
        """
        return self.io_stats

    def optimize(self) -> Dict[str, Any]:
        """Run comprehensive I/O optimization.

        Returns:
            Optimization results
        """
        # File I/O optimization
        file_io_result = self._optimize_file_io()
        optimizations = {"file_io": file_io_result}
        # Network I/O optimization
        network_io_result = self._optimize_network_io()
        optimizations["network_io"] = network_io_result

        # Buffer optimization
        buffer_result = self._optimize_buffers()
        optimizations["buffers"] = buffer_result

        # Cache optimization
        cache_result = self._optimize_caching()
        optimizations["caching"] = cache_result

        # Compression optimization
        compression_result = self._optimize_compression()
        optimizations["compression"] = compression_result

        # Store optimization in history
        self.optimization_history.append(
            {"timestamp": time.time(), "results": optimizations}
        )

        logger.info("I/O optimization completed")
        return optimizations

    def _optimize_file_io(self) -> Dict[str, Any]:
        """Optimize file I/O operations."""
        try:
            # Analyze file access patterns
            access_patterns = self._analyze_file_access_patterns()

            # Identify frequently accessed files
            frequent_files = [
                f
                for f in self.file_io_history.values()
                if f.read_count + f.write_count > 10
            ]

            # Calculate potential improvements
            total_io_time = self.io_stats.read_time + self.io_stats.write_time
            potential_improvement = total_io_time * 0.2  # Assume 20% improvement

            suggestions = []
            if frequent_files:
                suggestions.append(
                    "Consider implementing file caching for frequently accessed files"
                )
                suggestions.append("Use memory-mapped files for large files")

            if self.io_stats.read_operations > 100:
                suggestions.append("Consider batch reading operations")
                suggestions.append("Implement read-ahead buffering")

            if self.io_stats.write_operations > 100:
                suggestions.extend(
                    (
                        "Consider batch writing operations",
                        "Use write-behind buffering",
                    )
                )
            return {
                "success": True,
                "frequent_files_count": len(frequent_files),
                "total_io_time": total_io_time,
                "potential_improvement": potential_improvement,
                "suggestions": suggestions,
                "access_patterns": access_patterns,
            }

        except Exception as e:
            logger.error(f"File I/O optimization failed: {e}")
            return {"success": False, "error": str(e)}

    def _optimize_network_io(self) -> Dict[str, Any]:
        """Optimize network I/O operations."""
        try:
            suggestions = []

            # Check for connection pooling opportunities
            if self.settings["enable_async_io"]:
                suggestions.extend(
                    (
                        "Use connection pooling for HTTP requests",
                        "Implement request batching",
                        "Use keep-alive connections",
                    )
                )
            # Check for compression opportunities
            if not self.settings["enable_compression"]:
                suggestions.extend(
                    (
                        "Enable compression for network transfers",
                        "Use gzip compression for large responses",
                    )
                )
            # Check for caching opportunities
            if not self.settings["enable_caching"]:
                suggestions.extend(
                    (
                        "Implement response caching",
                        "Use ETags for conditional requests",
                    )
                )
            return {
                "success": True,
                "suggestions": suggestions,
                "async_io_enabled": self.settings["enable_async_io"],
                "compression_enabled": self.settings["enable_compression"],
                "caching_enabled": self.settings["enable_caching"],
            }

        except Exception as e:
            logger.error(f"Network I/O optimization failed: {e}")
            return {"success": False, "error": str(e)}

    def _optimize_buffers(self) -> Dict[str, Any]:
        """Optimize buffer usage."""
        try:
            current_buffer_size = self.settings["buffer_size"]

            # Analyze optimal buffer size based on usage patterns
            if self.io_stats.read_operations > 0:
                avg_read_size = self.io_stats.read_bytes / self.io_stats.read_operations
                optimal_buffer_size = max(4096, min(65536, int(avg_read_size * 2)))
            else:
                optimal_buffer_size = current_buffer_size

            # Check if buffer size should be adjusted
            buffer_optimization = {
                "current_size": current_buffer_size,
                "optimal_size": optimal_buffer_size,
                "should_adjust": abs(optimal_buffer_size - current_buffer_size) > 1024,
            }

            suggestions = []
            if buffer_optimization["should_adjust"]:
                suggestions.append(
                    f"Consider adjusting buffer size from {current_buffer_size} to {optimal_buffer_size}"
                )

            if self.io_stats.read_operations > 1000:
                suggestions.append("Consider using larger buffers for bulk operations")

            return {
                "success": True,
                "buffer_optimization": buffer_optimization,
                "suggestions": suggestions,
            }

        except Exception as e:
            logger.error(f"Buffer optimization failed: {e}")
            return {"success": False, "error": str(e)}

    def _optimize_caching(self) -> Dict[str, Any]:
        """Optimize caching strategies."""
        try:
            # Analyze cache effectiveness
            cache_hits = 0  # This would be tracked in a real implementation
            cache_misses = 0
            cache_effectiveness = (
                cache_hits / (cache_hits + cache_misses)
                if (cache_hits + cache_misses) > 0
                else 0
            )

            suggestions = []

            if cache_effectiveness < 0.5:
                suggestions.extend(
                    (
                        "Consider increasing cache size",
                        "Review cache eviction policies",
                        "Implement cache warming strategies",
                    )
                )
            if not self.settings["enable_caching"]:
                suggestions.append("Enable I/O caching for frequently accessed data")
                suggestions.append("Implement file system caching")

            return {
                "success": True,
                "cache_effectiveness": cache_effectiveness,
                "caching_enabled": self.settings["enable_caching"],
                "suggestions": suggestions,
            }

        except Exception as e:
            logger.error(f"Caching optimization failed: {e}")
            return {"success": False, "error": str(e)}

    def _optimize_compression(self) -> Dict[str, Any]:
        """Optimize compression settings."""
        try:
            suggestions = []

            # Check if compression should be enabled
            if not self.settings["enable_compression"]:
                suggestions.extend(
                    (
                        "Enable compression for text-based files",
                        "Use gzip compression for large files",
                        "Consider zstd compression for better performance",
                    )
                )
            # Check compression ratios
            if self.io_stats.read_bytes > 100 * 1024 * 1024:  # 100MB
                suggestions.append("Monitor compression ratios for large files")
                suggestions.append("Consider adaptive compression based on file type")

            return {
                "success": True,
                "compression_enabled": self.settings["enable_compression"],
                "suggestions": suggestions,
            }

        except Exception as e:
            logger.error(f"Compression optimization failed: {e}")
            return {"success": False, "error": str(e)}

    def _analyze_file_access_patterns(self) -> Dict[str, Any]:
        """Analyze file access patterns."""
        try:
            patterns = {"sequential": 0, "random": 0, "mixed": 0}

            for file_info in self.file_io_history.values():
                if file_info.read_count > file_info.write_count * 2:
                    patterns["sequential"] += 1
                elif file_info.write_count > file_info.read_count * 2:
                    patterns["random"] += 1
                else:
                    patterns["mixed"] += 1

            return patterns

        except Exception as e:
            logger.error(f"File access pattern analysis failed: {e}")
            return {"error": str(e)}

    def record_file_read(
        self, file_path: str, bytes_read: int, read_time: float
    ) -> None:
        """Record a file read operation.

        Args:
            file_path: Path to the file
            bytes_read: Number of bytes read
            read_time: Time taken for the read operation
        """
        # Update I/O stats
        self.io_stats.read_bytes += bytes_read
        self.io_stats.read_operations += 1
        self.io_stats.read_time += read_time
        self.io_stats.avg_read_time = (
            self.io_stats.read_time / self.io_stats.read_operations
        )

        # Update file I/O history
        if file_path not in self.file_io_history:
            self.file_io_history[file_path] = FileIOInfo(
                file_path=file_path, size_bytes=0
            )

        file_info = self.file_io_history[file_path]
        file_info.read_count += 1
        file_info.last_accessed = time.time()

    def record_file_write(
        self, file_path: str, bytes_written: int, write_time: float
    ) -> None:
        """Record a file write operation.

        Args:
            file_path: Path to the file
            bytes_written: Number of bytes written
            write_time: Time taken for the write operation
        """
        # Update I/O stats
        self.io_stats.write_bytes += bytes_written
        self.io_stats.write_operations += 1
        self.io_stats.write_time += write_time
        self.io_stats.avg_write_time = (
            self.io_stats.write_time / self.io_stats.write_operations
        )

        # Update file I/O history
        if file_path not in self.file_io_history:
            self.file_io_history[file_path] = FileIOInfo(
                file_path=file_path, size_bytes=0
            )

        file_info = self.file_io_history[file_path]
        file_info.write_count += 1
        file_info.last_accessed = time.time()

    def get_io_report(self) -> Dict[str, Any]:
        """Get comprehensive I/O report.

        Returns:
            I/O report dictionary
        """
        # Calculate throughput
        total_time = self.io_stats.read_time + self.io_stats.write_time
        total_bytes = self.io_stats.read_bytes + self.io_stats.write_bytes
        throughput_mbps = (
            (total_bytes / (1024 * 1024)) / total_time if total_time > 0 else 0
        )

        # Get recent optimizations
        recent_optimizations = (
            self.optimization_history[-5:] if self.optimization_history else []
        )

        return {
            "io_stats": {
                "read_bytes": self.io_stats.read_bytes,
                "write_bytes": self.io_stats.write_bytes,
                "read_operations": self.io_stats.read_operations,
                "write_operations": self.io_stats.write_operations,
                "avg_read_time": self.io_stats.avg_read_time,
                "avg_write_time": self.io_stats.avg_write_time,
                "throughput_mbps": throughput_mbps,
            },
            "file_io": {
                "files_tracked": len(self.file_io_history),
                "frequent_files": len(
                    [
                        f
                        for f in self.file_io_history.values()
                        if f.read_count + f.write_count > 10
                    ]
                ),
            },
            "settings": self.settings,
            "optimization_history": {
                "total_optimizations": len(self.optimization_history),
                "recent_optimizations": [
                    {
                        "timestamp": opt["timestamp"],
                        "optimizations": list(opt["results"].keys()),
                    }
                    for opt in recent_optimizations
                ],
            },
        }

    def set_buffer_size(self, buffer_size: int) -> None:
        """Set buffer size for I/O operations.

        Args:
            buffer_size: New buffer size
        """
        self.settings["buffer_size"] = buffer_size
        self.buffer_size = buffer_size
        logger.info(f"Buffer size set to {buffer_size}")

    def enable_async_io(self, enabled: bool = True) -> None:
        """Enable or disable async I/O.

        Args:
            enabled: Whether to enable async I/O
        """
        self.settings["enable_async_io"] = enabled
        logger.info(f"Async I/O {'enabled' if enabled else 'disabled'}")

    def enable_compression(self, enabled: bool = True) -> None:
        """Enable or disable compression.

        Args:
            enabled: Whether to enable compression
        """
        self.settings["enable_compression"] = enabled
        logger.info(f"Compression {'enabled' if enabled else 'disabled'}")

    def enable_caching(self, enabled: bool = True) -> None:
        """Enable or disable caching.

        Args:
            enabled: Whether to enable caching
        """
        self.settings["enable_caching"] = enabled
        logger.info(f"Caching {'enabled' if enabled else 'disabled'}")

    def clear_history(self) -> None:
        """Clear I/O history."""
        self.file_io_history.clear()
        self.optimization_history.clear()
        self.io_stats = IOStats()
        logger.info("I/O history cleared")

    def get_frequent_files(self, min_operations: int = 10) -> List[FileIOInfo]:
        """Get list of frequently accessed files.

        Args:
            min_operations: Minimum number of operations to consider frequent

        Returns:
            List of frequently accessed files
        """
        return [
            f
            for f in self.file_io_history.values()
            if f.read_count + f.write_count >= min_operations
        ]

    async def async_read_file(
        self, file_path: str, chunk_size: Optional[int] = None
    ) -> bytes:
        """Read a file asynchronously with optimization.

        Args:
            file_path: Path to the file
            chunk_size: Chunk size for reading (None for default)

        Returns:
            File contents
        """
        chunk_size = chunk_size or self.buffer_size
        start_time = time.time()

        try:
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()

            read_time = time.time() - start_time
            self.record_file_read(file_path, len(content), read_time)

            return content

        except Exception as e:
            logger.error(f"Async file read failed for {file_path}: {e}")
            raise

    async def async_write_file(
        self, file_path: str, content: bytes, chunk_size: Optional[int] = None
    ) -> None:
        """Write a file asynchronously with optimization.

        Args:
            file_path: Path to the file
            content: Content to write
            chunk_size: Chunk size for writing (None for default)
        """
        chunk_size = chunk_size or self.buffer_size
        start_time = time.time()

        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            write_time = time.time() - start_time
            self.record_file_write(file_path, len(content), write_time)

        except Exception as e:
            logger.error(f"Async file write failed for {file_path}: {e}")
            raise e
