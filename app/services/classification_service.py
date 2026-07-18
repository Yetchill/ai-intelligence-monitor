"""Classification orchestration and durable reclassification entry points."""

from collections.abc import Callable

from app.domain.classification import ClassificationResult, Classifier
from app.domain.collection import CollectedItem
from app.domain.enums import Category
from app.domain.models import IntelligenceItem
from app.storage.repositories import RepositoryUnitOfWork

UnitOfWorkFactory = Callable[[], RepositoryUnitOfWork]


class ClassificationService:
    def __init__(self, classifier: Classifier, uow_factory: UnitOfWorkFactory) -> None:
        self._classifier = classifier
        self._uow_factory = uow_factory

    async def classify(
        self,
        item: CollectedItem,
        *,
        source_default: Category | str | None,
    ) -> ClassificationResult:
        return await self._classifier.classify(item, source_default=source_default)

    async def reclassify_item(self, item_id: int) -> ClassificationResult:
        with self._uow_factory() as uow:
            item = uow.items.get(item_id)
            if item is None:
                raise LookupError(f"intelligence item {item_id} does not exist")
            source = uow.sources.get(item.source_id)
            if source is None:
                raise LookupError(f"source {item.source_id} does not exist")
            collected = CollectedItem(
                title=item.title,
                original_url=item.original_url,
                canonical_url=item.canonical_url,
                published_at=item.published_at,
                summary=item.summary,
                extra=item.extra,
            )
            source_default = source.default_category

        result = await self.classify(collected, source_default=source_default)
        with self._uow_factory() as uow:
            current = uow.items.get(item_id)
            if current is None:
                raise LookupError(f"intelligence item {item_id} no longer exists")
            _persist_result(current, result)
        return result

    async def reclassify_all(self, *, source_id: int | None = None) -> int:
        with self._uow_factory() as uow:
            item_ids = (
                [item.id for item in uow.items.list_by_source(source_id)]
                if source_id is not None
                else [item.id for item in uow.items.list()]
            )
        for item_id in item_ids:
            await self.reclassify_item(item_id)
        return len(item_ids)


def _persist_result(item: IntelligenceItem, result: ClassificationResult) -> None:
    item.category = result.category
    item.classification_score = result.score
    item.classification_reason = result.reason
    item.automatic_category_provider = result.provider
