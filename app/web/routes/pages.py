"""Server-rendered HTML pages and POST-only manual operations."""

from typing import Annotated
from urllib.parse import urlencode, urlsplit

from fastapi import APIRouter, Form, Path, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.domain.enums import Category
from app.domain.onboarding import DiscoverySession
from app.domain.update import UpdateResult
from app.services.error_sanitization import sanitize_error
from app.web.schemas import MAX_DATABASE_ID, ItemQueryParams, PageParams, WebInputError

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def items_page(request: Request) -> HTMLResponse:
    params = ItemQueryParams.parse(dict(request.query_params))
    services = request.app.state.services
    page = services.data.list_items(params.to_domain())
    _require_existing_page(page.page, page.total_pages)
    return request.app.state.templates.TemplateResponse(
        request,
        "items.html",
        {
            "page": page,
            "filters": params,
            "source_options": services.data.source_options(),
            "categories": tuple(Category),
            "previous_url": _page_url("/", params.query_values(), page.page - 1)
            if page.page > 1
            else None,
            "next_url": _page_url("/", params.query_values(), page.page + 1)
            if page.page < page.total_pages
            else None,
            "return_to": _current_path(request),
        },
    )


@router.get("/sources", response_class=HTMLResponse)
async def sources_page(request: Request) -> HTMLResponse:
    params = PageParams.parse(dict(request.query_params))
    page = request.app.state.services.data.list_sources(page=params.page, per_page=params.per_page)
    _require_existing_page(page.page, page.total_pages)
    values = {"per_page": str(params.per_page)}
    return request.app.state.templates.TemplateResponse(
        request,
        "sources.html",
        {
            "page": page,
            "previous_url": _page_url("/sources", values, page.page - 1) if page.page > 1 else None,
            "next_url": _page_url("/sources", values, page.page + 1)
            if page.page < page.total_pages
            else None,
            "return_to": _current_path(request),
        },
    )


@router.get("/sources/new", response_class=HTMLResponse)
async def new_source_page(request: Request) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(request, "source-new.html", {})


@router.post("/sources/discover", response_class=HTMLResponse)
async def discover_source(
    request: Request,
    url: Annotated[str, Form(min_length=1, max_length=2048)],
) -> RedirectResponse:
    token = await request.app.state.services.onboarding.start(url)
    return RedirectResponse(f"/sources/discover/{token}", status_code=303)


@router.get("/sources/discover/{token}", response_class=HTMLResponse)
async def discovery_page(
    request: Request,
    token: Annotated[str, Path(min_length=1, max_length=128)],
) -> HTMLResponse:
    session: DiscoverySession = request.app.state.services.sources.get_discovery(token)
    return request.app.state.templates.TemplateResponse(
        request,
        "source-discovery.html",
        {
            "token": token,
            "session": session,
            "categories": tuple(Category),
            "suggested_name": str(urlsplit(session.discovery.normalized_url).hostname or "新来源"),
        },
    )


@router.post("/sources", response_class=HTMLResponse)
async def create_source(
    request: Request,
    token: Annotated[str, Form(min_length=1, max_length=128)],
    name: Annotated[str, Form(min_length=1, max_length=255)],
    default_category: Annotated[str, Form(max_length=50)] = "",
    description: Annotated[str, Form(max_length=2000)] = "",
    enabled: Annotated[str | None, Form(max_length=5)] = None,
    action: Annotated[str, Form(max_length=30)] = "save",
) -> Response:
    if enabled not in {None, "true"}:
        raise WebInputError("来源状态无效。")
    if action not in {"save", "save_and_update"}:
        raise WebInputError("保存操作无效。")
    source = request.app.state.services.sources.create_from_token(
        token,
        name=name,
        default_category=default_category or None,
        enabled=enabled == "true",
        description=description or None,
    )
    if action == "save_and_update" and source.enabled:
        result = await request.app.state.services.updates.update(source_id=source.id)
        return _update_response(request, result)
    return RedirectResponse(f"/sources/{source.id}?saved=1", status_code=303)


@router.get("/sources/{source_id}", response_class=HTMLResponse)
async def source_detail_page(
    request: Request,
    source_id: Annotated[int, Path(ge=1, le=MAX_DATABASE_ID)],
) -> HTMLResponse:
    source = request.app.state.services.sources.get_source(source_id)
    return request.app.state.templates.TemplateResponse(
        request,
        "source-detail.html",
        {
            "source": source,
            "categories": tuple(Category),
            "saved": request.query_params.get("saved") == "1",
            "updated": request.query_params.get("updated") == "1",
        },
    )


@router.post("/sources/{source_id}/edit", response_class=HTMLResponse)
async def edit_source(
    request: Request,
    source_id: Annotated[int, Path(ge=1, le=MAX_DATABASE_ID)],
    name: Annotated[str, Form(min_length=1, max_length=255)],
    default_category: Annotated[str, Form(max_length=50)] = "",
    description: Annotated[str, Form(max_length=2000)] = "",
    enabled: Annotated[str | None, Form(max_length=5)] = None,
) -> RedirectResponse:
    if enabled not in {None, "true"}:
        raise WebInputError("来源状态无效。")
    request.app.state.services.sources.edit(
        source_id,
        name=name,
        default_category=default_category or None,
        enabled=enabled == "true",
        description=description or None,
    )
    return RedirectResponse(f"/sources/{source_id}?updated=1", status_code=303)


@router.post("/sources/{source_id}/rediscover", response_class=HTMLResponse)
async def rediscover_source(
    request: Request,
    source_id: Annotated[int, Path(ge=1, le=MAX_DATABASE_ID)],
) -> RedirectResponse:
    source = request.app.state.services.sources.get_source(source_id)
    if source.start_url is None:
        raise WebInputError("当前来源网址无效, 无法重新检测。")
    token = await request.app.state.services.onboarding.start(
        source.start_url, rediscover_source_id=source_id
    )
    return RedirectResponse(f"/sources/discover/{token}", status_code=303)


@router.post("/sources/{source_id}/rediscover/confirm", response_class=HTMLResponse)
async def confirm_rediscovery(
    request: Request,
    source_id: Annotated[int, Path(ge=1, le=MAX_DATABASE_ID)],
    token: Annotated[str, Form(min_length=1, max_length=128)],
) -> RedirectResponse:
    request.app.state.services.sources.confirm_rediscovery(source_id, token)
    return RedirectResponse(f"/sources/{source_id}?updated=1", status_code=303)


@router.get("/runs", response_class=HTMLResponse)
async def runs_page(request: Request) -> HTMLResponse:
    params = PageParams.parse(dict(request.query_params))
    page = request.app.state.services.data.list_crawl_runs(
        page=params.page, per_page=params.per_page
    )
    _require_existing_page(page.page, page.total_pages)
    values = {"per_page": str(params.per_page)}
    return request.app.state.templates.TemplateResponse(
        request,
        "runs.html",
        {
            "page": page,
            "previous_url": _page_url("/runs", values, page.page - 1) if page.page > 1 else None,
            "next_url": _page_url("/runs", values, page.page + 1)
            if page.page < page.total_pages
            else None,
        },
    )


@router.post("/items/{item_id}/favorite", response_class=HTMLResponse)
async def set_favorite(
    request: Request,
    item_id: Annotated[int, Path(ge=1, le=MAX_DATABASE_ID)],
    favorite: Annotated[str, Form(max_length=5)],
    return_to: Annotated[str, Form(max_length=2048)] = "/",
) -> RedirectResponse:
    if favorite not in {"true", "false"}:
        raise WebInputError("收藏状态无效。")
    request.app.state.services.data.set_favorite(item_id, favorite == "true")
    return RedirectResponse(_safe_return_to(return_to, default="/"), status_code=303)


@router.post("/items/{item_id}/category", response_class=HTMLResponse)
async def set_category(
    request: Request,
    item_id: Annotated[int, Path(ge=1, le=MAX_DATABASE_ID)],
    category: Annotated[str, Form(max_length=50)] = "",
    return_to: Annotated[str, Form(max_length=2048)] = "/",
) -> RedirectResponse:
    request.app.state.services.data.set_manual_category(item_id, category or None)
    return RedirectResponse(_safe_return_to(return_to, default="/"), status_code=303)


@router.post("/sources/{source_id}/enabled", response_class=HTMLResponse)
async def set_source_enabled(
    request: Request,
    source_id: Annotated[int, Path(ge=1, le=MAX_DATABASE_ID)],
    enabled: Annotated[str, Form(max_length=5)],
    return_to: Annotated[str, Form(max_length=2048)] = "/sources",
) -> RedirectResponse:
    if enabled not in {"true", "false"}:
        raise WebInputError("来源状态无效。")
    request.app.state.services.data.set_source_enabled(source_id, enabled == "true")
    return RedirectResponse(_safe_return_to(return_to, default="/sources"), status_code=303)


@router.post("/updates", response_class=HTMLResponse)
async def update_all(request: Request) -> HTMLResponse:
    result = await request.app.state.services.updates.update()
    return _update_response(request, result)


@router.post("/sources/{source_id}/updates", response_class=HTMLResponse)
async def update_source(
    request: Request,
    source_id: Annotated[int, Path(ge=1, le=MAX_DATABASE_ID)],
) -> HTMLResponse:
    result = await request.app.state.services.updates.update(source_id=source_id)
    return _update_response(request, result)


def _update_response(request: Request, result: UpdateResult) -> HTMLResponse:
    error_summary = result.error_summary
    return request.app.state.templates.TemplateResponse(
        request,
        "update-result.html",
        {
            "result": result,
            "error_summary": sanitize_error(error_summary, limit=300) if error_summary else None,
        },
    )


def _page_url(path: str, values: dict[str, str], page: int) -> str:
    query = {**values, "page": str(page)}
    return f"{path}?{urlencode(query)}"


def _current_path(request: Request) -> str:
    return request.url.path + (f"?{request.url.query}" if request.url.query else "")


def _safe_return_to(value: str, *, default: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme
        or parsed.netloc
        or not parsed.path.startswith("/")
        or value.startswith("//")
        or "\\" in value
        or "\r" in value
        or "\n" in value
    ):
        return default
    return value


def _require_existing_page(page: int, total_pages: int) -> None:
    if page > total_pages:
        raise WebInputError(f"页码超出范围; 当前结果共 {total_pages} 页。")
