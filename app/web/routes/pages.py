"""Server-rendered HTML pages and POST-only manual operations."""

from typing import Annotated
from urllib.parse import urlencode, urlsplit

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.domain.enums import Category
from app.web.schemas import ItemQueryParams, PageParams, WebInputError

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def items_page(request: Request) -> HTMLResponse:
    params = ItemQueryParams.parse(dict(request.query_params))
    services = request.app.state.services
    page = services.data.list_items(params.to_domain())
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


@router.get("/runs", response_class=HTMLResponse)
async def runs_page(request: Request) -> HTMLResponse:
    params = PageParams.parse(dict(request.query_params))
    page = request.app.state.services.data.list_crawl_runs(
        page=params.page, per_page=params.per_page
    )
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
    item_id: int,
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
    item_id: int,
    category: Annotated[str, Form(max_length=50)] = "",
    return_to: Annotated[str, Form(max_length=2048)] = "/",
) -> RedirectResponse:
    request.app.state.services.data.set_manual_category(item_id, category or None)
    return RedirectResponse(_safe_return_to(return_to, default="/"), status_code=303)


@router.post("/sources/{source_id}/enabled", response_class=HTMLResponse)
async def set_source_enabled(
    request: Request,
    source_id: int,
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
async def update_source(request: Request, source_id: int) -> HTMLResponse:
    result = await request.app.state.services.updates.update(source_id=source_id)
    return _update_response(request, result)


def _update_response(request: Request, result: object) -> HTMLResponse:
    return request.app.state.templates.TemplateResponse(
        request,
        "update-result.html",
        {"result": result},
    )


def _page_url(path: str, values: dict[str, str], page: int) -> str:
    query = {**values, "page": str(page)}
    return f"{path}?{urlencode(query)}"


def _current_path(request: Request) -> str:
    return request.url.path + (f"?{request.url.query}" if request.url.query else "")


def _safe_return_to(value: str, *, default: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/") or value.startswith("//"):
        return default
    return value
