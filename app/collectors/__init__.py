"""Built-in source collectors and registration support."""

from app.collectors.github_release import GitHubReleaseCollector
from app.collectors.html_list import HTMLListCollector
from app.collectors.registry import CollectorRegistry, default_collector_registry
from app.collectors.rss import RSSCollector

__all__ = [
    "CollectorRegistry",
    "GitHubReleaseCollector",
    "HTMLListCollector",
    "RSSCollector",
    "default_collector_registry",
]
