"""Fixed-corpus and boundary tests for the pure classification system."""

from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from app.classifiers import (
    FinalCategoryResolver,
    ManualCategoryError,
    RuleBasedClassifier,
    RuleConfigError,
    load_classification_rules,
)
from app.domain.classification import ClassificationResult
from app.domain.collection import CollectedItem
from app.domain.enums import Category
from app.utils.text import normalize_text

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "classification_cases.yaml"


def _item(title: str, summary: str | None = None) -> CollectedItem:
    return CollectedItem(
        title=title,
        summary=summary,
        original_url="https://example.com/item",
        canonical_url="https://example.com/item",
    )


def _cases() -> list[dict[str, Any]]:
    raw_object: object = yaml.safe_load(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert isinstance(raw_object, dict)
    raw = cast(dict[str, object], raw_object)
    cases = raw["cases"]
    assert isinstance(cases, list)
    return cast(list[dict[str, Any]], cases)


@pytest.mark.parametrize("case", _cases(), ids=lambda case: str(case["id"]))
async def test_fixed_classification_case(case: dict[str, Any]) -> None:
    classifier = RuleBasedClassifier.from_yaml()
    result = await classifier.classify(
        _item(str(case["title"]), cast(str | None, case.get("summary"))),
        source_default=cast(str | None, case.get("source_default")),
    )

    assert result.category.value == case["expected"], result.reason
    assert result.is_ambiguous is bool(case.get("expected_ambiguous", False))
    assert result.reason


async def test_fixed_corpus_accuracy_and_confusion_report() -> None:
    classifier = RuleBasedClassifier.from_yaml()
    cases = _cases()
    correct_by_expected: Counter[str] = Counter()
    total_by_expected: Counter[str] = Counter()
    confusion: list[str] = []

    for case in cases:
        result = await classifier.classify(
            _item(str(case["title"]), cast(str | None, case.get("summary"))),
            source_default=cast(str | None, case.get("source_default")),
        )
        expected = str(case["expected"])
        total_by_expected[expected] += 1
        if result.category.value == expected:
            correct_by_expected[expected] += 1
        else:
            confusion.append(f"{case['id']}: {expected} -> {result.category.value}")

    total_correct = sum(correct_by_expected.values())
    accuracy = total_correct / len(cases)
    print(f"classification accuracy: {total_correct}/{len(cases)} = {accuracy:.2%}")
    for category in Category:
        expected_total = total_by_expected[category.value]
        print(
            f"{category.value}: {correct_by_expected[category.value]}/{expected_total} "
            f"= {correct_by_expected[category.value] / expected_total:.2%}"
        )
    print(f"confusion: {confusion or 'none'}")

    assert accuracy >= 0.90
    for category in (Category.SOLICITATION, Category.AWARD_CASE):
        assert correct_by_expected[category.value] / total_by_expected[category.value] >= 0.90


async def test_manual_category_always_overrides_automatic_result() -> None:
    classifier = RuleBasedClassifier.from_yaml()
    automatic = await classifier.classify(_item("某公司发布新一代大模型"))
    original = deepcopy(automatic)

    final = FinalCategoryResolver().resolve(automatic, manual_category=Category.SOLICITATION)

    assert final.category is Category.SOLICITATION
    assert final.provider == "manual"
    assert "最高优先级" in final.reason
    assert automatic == original


def test_manual_category_rejects_unknown_value() -> None:
    automatic = ClassificationResult(Category.UNCLASSIFIED, 0, "none", "rule_based")
    with pytest.raises(ManualCategoryError, match="未知人工分类"):
        FinalCategoryResolver().resolve(automatic, manual_category="other")


async def test_classifier_does_not_mutate_collected_item() -> None:
    item = _item("智能体平台2.0正式上线", "新增多个功能")
    original = deepcopy(item)
    await RuleBasedClassifier.from_yaml().classify(item)
    assert item == original


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  智能体　平台\n2.0  ", "智能体 平台 2.0"),
        ("\uff21\uff47\uff45\uff4e\uff54 平台", "agent 平台"),
        ("模型\uff0c发布\uff01V2.1", "模型,发布!v2.1"),
        ("大模型\uff08增强版\uff09", "大模型(增强版)"),
    ],
)
def test_text_normalization(raw: str, expected: str) -> None:
    assert normalize_text(raw) == expected


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (
            "settings: {}\ncategories:\n  invented: {}\n",
            "settings 缺少字段",
        ),
        (
            """
settings:
  minimum_score: ten
  minimum_margin: 3
  title_weight: 2
  summary_weight: 1
  phrase_weight: 1.5
  source_default_weight: 2
categories: {}
""",
            "minimum_score 必须是数值",
        ),
        ("settings: [broken", "YAML 格式错误"),
    ],
)
def test_rule_loader_reports_clear_errors(tmp_path: Path, content: str, message: str) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(RuleConfigError, match=message):
        load_classification_rules(path)


def test_rule_loader_rejects_unknown_category(tmp_path: Path) -> None:
    valid = yaml.safe_load(
        (Path(__file__).parents[2] / "app/config/classification_rules.yaml").read_text(
            encoding="utf-8"
        )
    )
    valid["categories"]["invented"] = {
        "priority": 1,
        "phrases": {},
        "keywords": {},
        "negative_phrases": {},
    }
    path = tmp_path / "unknown.yaml"
    path.write_text(yaml.safe_dump(valid, allow_unicode=True), encoding="utf-8")
    with pytest.raises(RuleConfigError, match="未知分类: invented"):
        load_classification_rules(path)


async def test_unknown_source_default_is_rejected() -> None:
    with pytest.raises(ValueError, match="未知来源默认分类"):
        await RuleBasedClassifier.from_yaml().classify(_item("普通消息"), source_default="invented")
