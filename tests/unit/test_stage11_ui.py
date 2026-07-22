# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportMissingParameterType=false
"""Stage 11 UI/AI workflow tests — navigation, read status, dates, enums."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.storage.database import Database
from app.web.app import create_app


@pytest.fixture
def stage11_client(database: Database) -> Iterator[TestClient]:
    app = create_app(database=database, enforce_migrations=False)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# --- Navigation ---

def test_navigation_has_five_entries(stage11_client):
    resp = stage11_client.get("/")
    assert resp.status_code == 200
    nav_start = resp.text.index('<nav')
    nav_end = resp.text.index('</nav>', nav_start)
    nav = resp.text[nav_start:nav_end]
    link_count = nav.count('<a ')
    assert link_count == 5, f"Expected 5 nav links, got {link_count}"


def test_nav_entries_correct_order(stage11_client):
    resp = stage11_client.get("/")
    entries = ["资讯", "AI", "来源", "设置", "更新记录"]
    positions = [resp.text.index(e) for e in entries]
    assert positions == sorted(positions)


def test_leadership_page_redirects(stage11_client):
    resp = stage11_client.get("/leadership", follow_redirects=False)
    assert resp.status_code in (301, 302, 307, 308)
    assert resp.headers["location"] == "/"


def test_industry_leads_not_in_nav(stage11_client):
    resp = stage11_client.get("/")
    nav_start = resp.text.index('<nav')
    nav_end = resp.text.index('</nav>', nav_start)
    nav_html = resp.text[nav_start:nav_end]
    assert "行业线索" not in nav_html


def test_homepage_all_scope(stage11_client):
    resp = stage11_client.get("/")
    html = resp.text
    assert "全部来源" in html


# --- Read / Unread ---

def test_is_read_filter_works(stage11_client):
    for val in ("yes", "no", "all"):
        resp = stage11_client.get(f"/?is_read={val}")
        assert resp.status_code == 200


def test_read_status_endpoint_rejects_invalid(stage11_client):
    resp = stage11_client.post("/items/1/read", data={"is_read": "invalid", "return_to": "/"})
    assert resp.status_code == 400


def test_batch_read_rejects_empty(stage11_client):
    resp = stage11_client.post(
        "/items/batch-read",
        data={"item_ids": "", "is_read": "true", "return_to": "/"},
    )
    assert resp.status_code == 400


# --- Date validation ---

def test_date_from_after_to_rejected(stage11_client):
    resp = stage11_client.get("/?published_from=2025-06-01&published_to=2025-01-01")
    assert resp.status_code == 400


def test_date_invalid_val_rejected(stage11_client):
    resp = stage11_client.get("/?published_from=12025-01-01")
    assert resp.status_code == 400


def test_date_bad_month_safe(stage11_client):
    resp = stage11_client.get("/?published_from=2025-13-01")
    assert resp.status_code == 400


def test_date_feb29_leap_ok(stage11_client):
    resp = stage11_client.get("/?published_from=2024-02-29")
    assert resp.status_code == 200


def test_date_feb29_nonleap_bad(stage11_client):
    resp = stage11_client.get("/?published_from=2025-02-29")
    assert resp.status_code == 400


def test_date_html_min_attr(stage11_client):
    resp = stage11_client.get("/")
    assert 'min="2000-01-01"' in resp.text


# --- No raw internal English enum values in visible text ---

def test_no_internal_english_display(stage11_client):
    """Check pages don't show raw enum values like 'automatic' in user text."""
    pages = ["/", "/sources", "/runs", "/settings", "/ai"]
    raw_terms = ["automatic", "pending", "active", "media_only"]
    for path in pages:
        resp = stage11_client.get(path)
        if resp.status_code != 200:
            continue
        visible = _strip_tags(resp.text)
        for term in raw_terms:
            assert term not in visible, f"'{term}' found in visible text on {path}"


def _strip_tags(html: str) -> str:
    import re
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.lower()


# --- AI page ---

def test_ai_page_loads(stage11_client):
    resp = stage11_client.get("/ai")
    assert resp.status_code == 200
    assert "AI 工具" in resp.text


def test_ai_page_shows_key_status(stage11_client):
    resp = stage11_client.get("/ai")
    assert ("已配置" in resp.text) or ("未配置" in resp.text)


def test_ai_page_has_connection_test_button(stage11_client):
    resp = stage11_client.get("/ai")
    assert "测试连接" in resp.text


# --- Foundation: No API key needed for rule mode ---

def test_items_page_loads(stage11_client):
    resp = stage11_client.get("/")
    assert resp.status_code == 200


# --- Settings page ---

def test_settings_page_loads(stage11_client):
    resp = stage11_client.get("/settings")
    assert resp.status_code == 200
    assert "设置" in resp.text


# --- Sources page ---

def test_sources_page_loads(stage11_client):
    resp = stage11_client.get("/sources")
    assert resp.status_code == 200


# --- Runs page ---

def test_runs_page_loads(stage11_client):
    resp = stage11_client.get("/runs")
    assert resp.status_code == 200


# --- Update button text ---

def test_update_button_uses_chinese_label(stage11_client):
    resp = stage11_client.get("/")
    html = resp.text
    assert "更新全部启用来源" in html
    assert "更新全部 active 来源" not in html
