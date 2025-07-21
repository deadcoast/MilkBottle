"""Tests for the plugin marketplace system."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.milkbottle.config import MilkBottleConfig
from src.milkbottle.plugin_marketplace import (
    MarketplaceManager,
    PluginAnalytics,
    PluginRating,
    PluginRepository,
    PluginSecurity,
)


class TestMarketplaceManager:
    """Test MarketplaceManager functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MilkBottleConfig()

    @pytest.fixture
    def marketplace_manager(self, config):
        """Create MarketplaceManager instance."""
        return MarketplaceManager(config)

    @pytest.mark.asyncio
    async def test_search_plugins(self, marketplace_manager):
        """Test plugin search functionality."""
        with patch.object(
            marketplace_manager.repository, "search_plugins"
        ) as mock_search:
            mock_search.return_value = []

            results = await marketplace_manager.search_plugins("test")
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_install_plugin(self, marketplace_manager):
        """Test plugin installation."""
        with patch.object(
            marketplace_manager.repository, "download_plugin"
        ) as mock_download:
            mock_download.return_value = Path("/tmp/test_plugin")

            result = await marketplace_manager.install_plugin("test-plugin")
            assert result is True

    @pytest.mark.asyncio
    async def test_get_plugin_info(self, marketplace_manager):
        """Test getting plugin information."""
        with patch.object(marketplace_manager.repository, "get_plugin") as mock_get:
            mock_get.return_value = Mock()

            info = await marketplace_manager.get_plugin_info("test-plugin")
            assert info is not None


class TestPluginRepository:
    """Test PluginRepository functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MilkBottleConfig()

    @pytest.fixture
    def repository(self, config):
        """Create PluginRepository instance."""
        return PluginRepository(config)

    @pytest.mark.asyncio
    async def test_search_plugins(self, repository):
        """Test plugin search."""
        with patch.object(repository, "_update_cache_if_needed"):
            results = await repository.search_plugins("test")
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_get_plugin(self, repository):
        """Test getting plugin information."""
        with patch.object(repository, "_update_cache_if_needed"):
            plugin = await repository.get_plugin("test-plugin")
            assert plugin is None  # No plugins in cache initially

    @pytest.mark.asyncio
    async def test_download_plugin(self, repository):
        """Test plugin download."""
        with (
            patch.object(repository, "get_plugin") as mock_get,
            patch.object(repository, "_download_file") as mock_download,
            patch.object(repository, "_verify_checksum") as mock_verify,
            patch.object(repository, "_extract_plugin") as mock_extract,
        ):

            mock_plugin = Mock()
            mock_plugin.latest_version = "1.0.0"
            mock_plugin.versions = [Mock(version="1.0.0", checksum="abc123")]
            mock_get.return_value = mock_plugin
            mock_download.return_value = Path("/tmp/test.zip")
            mock_verify.return_value = True
            mock_extract.return_value = Path("/tmp/test_plugin")

            result = await repository.download_plugin("test-plugin")
            assert result is not None

    @pytest.mark.asyncio
    async def test_validate_plugin(self, repository):
        """Test plugin validation."""
        with patch.object(repository, "get_plugin_metadata") as mock_metadata:
            mock_metadata.return_value = {
                "name": "test-plugin",
                "version": "1.0.0",
                "description": "Test plugin",
                "author": "Test Author",
            }

            result = await repository.validate_plugin(Path("/tmp/test_plugin"))
            assert result["valid"] is True


class TestPluginRating:
    """Test PluginRating functionality."""

    @pytest.fixture
    def rating_system(self):
        """Create PluginRating instance."""
        return PluginRating()

    @pytest.mark.asyncio
    async def test_submit_review(self, rating_system):
        """Test review submission."""
        result = await rating_system.submit_review(
            "test-plugin", "testuser", 4.5, "Great plugin!"
        )
        assert result is True
        assert len(rating_system.reviews) == 1

    @pytest.mark.asyncio
    async def test_get_reviews(self, rating_system):
        """Test getting reviews."""
        # Submit a review first
        await rating_system.submit_review(
            "test-plugin", "testuser", 4.5, "Great plugin!"
        )

        reviews = await rating_system.get_reviews("test-plugin")
        assert len(reviews) == 1
        assert reviews[0].rating == 4.5

    @pytest.mark.asyncio
    async def test_get_average_rating(self, rating_system):
        """Test average rating calculation."""
        # Submit multiple reviews
        await rating_system.submit_review("test-plugin", "user1", 4.0, "Good")
        await rating_system.submit_review("test-plugin", "user2", 5.0, "Excellent")

        avg_rating = await rating_system.get_average_rating("test-plugin")
        assert avg_rating == 4.5

    @pytest.mark.asyncio
    async def test_get_average_rating_no_reviews(self, rating_system):
        """Test average rating with no reviews."""
        avg_rating = await rating_system.get_average_rating("nonexistent-plugin")
        assert avg_rating == 0.0


class TestPluginAnalytics:
    """Test PluginAnalytics functionality."""

    @pytest.fixture
    def analytics(self):
        """Create PluginAnalytics instance."""
        return PluginAnalytics()

    @pytest.mark.asyncio
    async def test_record_download(self, analytics):
        """Test download recording."""
        await analytics.record_download("test-plugin", "testuser", "1.0.0")
        assert len(analytics.download_events) == 1
        assert analytics.download_events[0].plugin_name == "test-plugin"

    @pytest.mark.asyncio
    async def test_record_usage(self, analytics):
        """Test usage recording."""
        await analytics.record_usage("test-plugin", "testuser", "execute")
        assert len(analytics.usage_stats) == 1
        assert analytics.usage_stats[0].action == "execute"

    @pytest.mark.asyncio
    async def test_get_download_count(self, analytics):
        """Test download count retrieval."""
        await analytics.record_download("test-plugin", "user1", "1.0.0")
        await analytics.record_download("test-plugin", "user2", "1.0.0")
        await analytics.record_download("other-plugin", "user3", "1.0.0")

        count = await analytics.get_download_count("test-plugin")
        assert count == 2

    @pytest.mark.asyncio
    async def test_get_usage_stats(self, analytics):
        """Test usage stats retrieval."""
        await analytics.record_usage("test-plugin", "user1", "execute")
        await analytics.record_usage("test-plugin", "user2", "configure")
        await analytics.record_usage("other-plugin", "user3", "execute")

        stats = await analytics.get_usage_stats("test-plugin")
        assert len(stats) == 2


class TestPluginSecurity:
    """Test PluginSecurity functionality."""

    @pytest.fixture
    def security(self):
        """Create PluginSecurity instance."""
        return PluginSecurity()

    @pytest.mark.asyncio
    async def test_verify_signature(self, security):
        """Test signature verification."""
        result = await security.verify_signature("/tmp/test_plugin", "abc123")
        assert result is True

    @pytest.mark.asyncio
    async def test_scan_plugin(self, security):
        """Test plugin security scanning."""
        result = await security.scan_plugin("test-plugin", "/tmp/test_plugin")
        assert result.passed is True
        assert result.plugin_name == "test-plugin"

    @pytest.mark.asyncio
    async def test_get_scan_result(self, security):
        """Test getting scan results."""
        # First scan the plugin
        scan_result = await security.scan_plugin("test-plugin", "/tmp/test_plugin")

        # Verify scan was completed successfully
        assert scan_result is not None
        assert scan_result.passed is True

        # Then retrieve the result
        result = await security.get_scan_result("test-plugin")
        assert result is not None
        assert result.plugin_name == "test-plugin"

    @pytest.mark.asyncio
    async def test_get_scan_result_nonexistent(self, security):
        """Test getting scan result for non-existent plugin."""
        result = await security.get_scan_result("nonexistent-plugin")
        assert result is None


class TestMarketplaceIntegration:
    """Integration tests for the marketplace system."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return MilkBottleConfig()

    @pytest.fixture
    def marketplace_manager(self, config):
        """Create MarketplaceManager instance."""
        return MarketplaceManager(config)

    @pytest.mark.asyncio
    async def test_full_plugin_lifecycle(self, marketplace_manager):
        """Test complete plugin lifecycle: search, install, rate, track usage."""
        # Search for plugins
        with patch.object(
            marketplace_manager.repository, "search_plugins"
        ) as mock_search:
            mock_search.return_value = [Mock(name="test-plugin")]
            results = await marketplace_manager.search_plugins("test")
            assert len(results) == 1

        # Install plugin
        with patch.object(
            marketplace_manager.repository, "download_plugin"
        ) as mock_download:
            mock_download.return_value = Path("/tmp/test_plugin")
            install_result = await marketplace_manager.install_plugin("test-plugin")
            assert install_result is True

        # Submit review
        review_result = await marketplace_manager.submit_review(
            "test-plugin", "testuser", 4.5, "Great plugin!"
        )
        assert review_result is True

        # Record usage
        await marketplace_manager.record_usage("test-plugin", "testuser", "execute")

        # Get analytics
        download_count = await marketplace_manager.get_download_count("test-plugin")
        assert download_count >= 1

        # Get average rating
        avg_rating = await marketplace_manager.get_average_rating("test-plugin")
        assert avg_rating == 4.5
