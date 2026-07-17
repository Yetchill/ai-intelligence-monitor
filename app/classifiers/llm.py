"""Future LLM classification extension point; no SDK or external call is included."""

from app.domain.classification import ClassificationResult
from app.domain.collection import CollectedItem
from app.domain.enums import Category


class LLMClassifier:
    """Placeholder for a future configured model provider."""

    async def classify(
        self,
        item: CollectedItem,
        *,
        source_default: Category | str | None = None,
    ) -> ClassificationResult:
        del item, source_default
        raise NotImplementedError("LLMClassifier 尚未接入模型提供方")
