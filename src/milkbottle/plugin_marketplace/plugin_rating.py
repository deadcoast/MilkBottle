"""Plugin Rating - Plugin rating and review management."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List

from rich.console import Console


@dataclass
class PluginReview:
    """Plugin review and rating."""

    plugin_name: str
    user: str
    rating: float
    review: str
    timestamp: str


class PluginRating:
    """Plugin rating and review management."""

    def __init__(self):
        self.console = Console()
        self.logger = logging.getLogger("milkbottle.plugin_rating")
        self.reviews: List[PluginReview] = []

    async def submit_review(
        self, plugin_name: str, user: str, rating: float, review: str
    ) -> bool:
        """Submit a plugin review and rating."""
        try:
            review_obj = PluginReview(
                plugin_name=plugin_name,
                user=user,
                rating=rating,
                review=review,
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            self.reviews.append(review_obj)
            self.logger.info(f"Review submitted for {plugin_name} by {user}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to submit review: {e}")
            return False

    async def get_reviews(
        self, plugin_name: str, limit: int = 10
    ) -> List[PluginReview]:
        """Get reviews for a plugin."""
        return [r for r in self.reviews if r.plugin_name == plugin_name][-limit:]

    async def get_average_rating(self, plugin_name: str) -> float:
        """Get average rating for a plugin."""
        ratings = [r.rating for r in self.reviews if r.plugin_name == plugin_name]
        return sum(ratings) / len(ratings) if ratings else 0.0
