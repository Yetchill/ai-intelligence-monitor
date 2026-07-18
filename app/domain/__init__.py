"""Domain models and shared enumerations."""

from app.domain.classification import ClassificationResult, Classifier
from app.domain.collection import CollectContext, CollectedItem, Collector, Fetcher, FetchResult
from app.domain.enums import Category, CrawlStatus, SourceOrigin, SourceType
from app.domain.models import Base, CrawlRun, IntelligenceItem, ItemRevision, Source
from app.domain.queries import ItemQuery, Page
from app.domain.update import SourceUpdateResult, SourceUpdateStatus, UpdateMode, UpdateResult

__all__ = [
    "Base",
    "Category",
    "ClassificationResult",
    "Classifier",
    "CollectContext",
    "CollectedItem",
    "Collector",
    "CrawlRun",
    "CrawlStatus",
    "FetchResult",
    "Fetcher",
    "IntelligenceItem",
    "ItemQuery",
    "ItemRevision",
    "Page",
    "Source",
    "SourceOrigin",
    "SourceType",
    "SourceUpdateResult",
    "SourceUpdateStatus",
    "UpdateMode",
    "UpdateResult",
]
