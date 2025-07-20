"""Plugin Analytics - Plugin download tracking and analytics."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List

from rich.console import Console


@dataclass
class DownloadEvent:
    """Plugin download event."""

    plugin_name: str
    user: str
    timestamp: str
    version: str


@dataclass
class UsageStat:
    """Plugin usage statistics."""

    plugin_name: str
    user: str
    action: str
    timestamp: str


class PluginAnalytics:
    """Plugin download tracking and analytics."""

    def __init__(self):
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.plugin_analytics")
        self.download_events: List[DownloadEvent] = []
        self.usage_stats: List[UsageStat] = []

    async def record_download(self, plugin_name: str, user: str, version: str) -> None:
        """Record a plugin download event."""
        event = DownloadEvent(
            plugin_name=plugin_name,
            user=user,
            version=version,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.download_events.append(event)
        self.logger.info(f"Download recorded for {plugin_name} by {user}")

    async def record_usage(self, plugin_name: str, user: str, action: str) -> None:
        """Record a plugin usage event."""
        stat = UsageStat(
            plugin_name=plugin_name,
            user=user,
            action=action,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.usage_stats.append(stat)
        self.logger.info(f"Usage recorded for {plugin_name} by {user}: {action}")

    async def get_download_count(self, plugin_name: str) -> int:
        """Get total download count for a plugin."""
        return len([e for e in self.download_events if e.plugin_name == plugin_name])

    async def get_usage_stats(self, plugin_name: str) -> List[UsageStat]:
        """Get usage stats for a plugin."""
        return [s for s in self.usage_stats if s.plugin_name == plugin_name]
