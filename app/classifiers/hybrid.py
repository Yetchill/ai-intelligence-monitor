"""Future rule/LLM orchestration extension point."""

from app.domain.classification import ClassificationResult
from app.domain.collection import CollectedItem
from app.domain.enums import Category


class HybridClassifier:
    """Placeholder; expected confidence routing is documented, not activated."""

    async def classify(
        self,
        item: CollectedItem,
        *,
        source_default: Category | str | None = None,
    ) -> ClassificationResult:
        del item, source_default
        raise NotImplementedError("HybridClassifier 尚未启用; 当前请直接使用规则分类器")
