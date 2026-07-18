"""Local-only FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy.exc import SQLAlchemyError

from app.classifiers.manual import ManualCategoryError
from app.config import Settings, get_settings
from app.config.settings import PROJECT_ROOT
from app.domain.enums import Category, CrawlStatus
from app.services.error_sanitization import sanitize_error
from app.services.update_pipeline import SourceDisabledError, SourceNotFoundError
from app.services.web_data_service import EntityNotFoundError
from app.storage.database import Database
from app.utils.logging import configure_logging
from app.web.dependencies import PipelineContextFactory, UpdateInProgressError, WebServices
from app.web.routes import router
from app.web.schemas import WebInputError

WEB_ROOT = Path(__file__).resolve().parent
CATEGORY_LABELS = {
    Category.MODEL_TECHNOLOGY: "模型与技术动态",
    Category.AGENT_PRODUCT: "智能体与产品更新",
    Category.ENTERPRISE_CASE: "企业成果与应用案例",
    Category.AWARD_CASE: "获奖与优秀案例",
    Category.SOLICITATION: "奖项与成果征集",
    Category.POLICY_INDUSTRY: "政策、标准与行业动态",
    Category.UNCLASSIFIED: "待分类",
}
STATUS_LABELS = {
    CrawlStatus.RUNNING: "运行中",
    CrawlStatus.SUCCESS: "成功",
    CrawlStatus.PARTIAL_SUCCESS: "部分成功",
    CrawlStatus.FAILED: "失败",
}


def create_app(
    *,
    settings: Settings | None = None,
    database: Database | None = None,
    enforce_migrations: bool = True,
    pipeline_context_factory: PipelineContextFactory | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    resolved_database = database or Database.from_settings(resolved_settings)
    owns_database = database is None

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        configure_logging(resolved_settings)
        if enforce_migrations:
            require_current_migration(resolved_database)
        try:
            yield
        finally:
            if owns_database:
                resolved_database.dispose()

    application = FastAPI(
        title=resolved_settings.app_name,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=lifespan,
    )
    templates = _templates()
    application.state.templates = templates
    if pipeline_context_factory is None:
        application.state.services = WebServices.build(resolved_database)
    else:
        application.state.services = WebServices.build(
            resolved_database, pipeline_context_factory=pipeline_context_factory
        )
    application.mount("/static", StaticFiles(directory=WEB_ROOT / "static"), name="static")
    application.include_router(router)
    _register_error_handlers(application, templates)
    return application


def require_current_migration(database: Database) -> None:
    """Refuse startup when the configured database is not at Alembic head."""

    script = ScriptDirectory.from_config(_alembic_config())
    expected = script.get_current_head()
    with database.engine.connect() as connection:
        current = MigrationContext.configure(connection).get_current_revision()
    if current != expected:
        raise RuntimeError(
            "数据库结构未升级。请先运行 `uv run alembic upgrade head`, "
            f"当前版本为 {current or '未初始化'}, 目标版本为 {expected}。"
        )


def _alembic_config():  # type: ignore[no-untyped-def]
    from alembic.config import Config

    return Config(PROJECT_ROOT / "alembic.ini")


def _templates() -> Jinja2Templates:
    environment = Environment(
        loader=FileSystemLoader(WEB_ROOT / "templates"),
        autoescape=select_autoescape(("html", "xml"), default_for_string=True),
    )
    globals_mapping = cast(dict[str, object], environment.globals)
    globals_mapping["category_label"] = _category_label
    globals_mapping["status_label"] = _status_label
    globals_mapping["format_time"] = _format_time
    return Jinja2Templates(env=environment)


def _format_time(value: object) -> str:
    from datetime import datetime

    return value.strftime("%Y-%m-%d %H:%M") if isinstance(value, datetime) else "—"


def _category_label(value: Category | str) -> str:
    return CATEGORY_LABELS.get(Category(value), "待分类")


def _status_label(value: CrawlStatus | str) -> str:
    return STATUS_LABELS.get(CrawlStatus(value), "未知")


def _register_error_handlers(application: FastAPI, templates: Jinja2Templates) -> None:
    async def render_error(request: Request, status_code: int, message: str) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"status_code": status_code, "message": message},
            status_code=status_code,
        )

    async def input_error(request: Request, exc: Exception) -> HTMLResponse:
        return await render_error(request, 400, sanitize_error(exc, limit=300))

    async def request_validation_error(request: Request, _exc: Exception) -> HTMLResponse:
        return await render_error(request, 400, "提交参数无效, 请返回页面检查后重试。")

    async def not_found(request: Request, exc: Exception) -> HTMLResponse:
        return await render_error(request, 404, sanitize_error(exc, limit=200))

    async def update_conflict(request: Request, exc: Exception) -> HTMLResponse:
        return await render_error(request, 409, sanitize_error(exc, limit=200))

    async def database_error(request: Request, _exc: Exception) -> HTMLResponse:
        return await render_error(request, 500, "本地数据库暂时不可用, 请稍后重试并检查日志。")

    async def unexpected_error(request: Request, _exc: Exception) -> HTMLResponse:
        return await render_error(request, 500, "操作未能完成, 请稍后重试并检查应用日志。")

    application.add_exception_handler(WebInputError, input_error)
    application.add_exception_handler(ManualCategoryError, input_error)
    application.add_exception_handler(SourceDisabledError, input_error)
    application.add_exception_handler(RequestValidationError, request_validation_error)
    application.add_exception_handler(EntityNotFoundError, not_found)
    application.add_exception_handler(SourceNotFoundError, not_found)
    application.add_exception_handler(UpdateInProgressError, update_conflict)
    application.add_exception_handler(SQLAlchemyError, database_error)
    application.add_exception_handler(Exception, unexpected_error)


app = create_app()
