"""统一的 Loguru 日志配置。"""

from __future__ import annotations

import sys
from typing import Any, Dict
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfo

from loguru import logger as loguru_logger

from app.saas.core.config.settings import settings
from app.saas.core.logging.context import get_log_context

_DEFAULT_EXTRAS: dict[str, Any] = {}


class ContextInjector:
    """在日志记录时注入上下文变量，并统一时区。"""

    def __init__(self, timezone: ZoneInfo | None = None) -> None:
        self.timezone = timezone or ZoneInfo("Asia/Shanghai")

    def __call__(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """在日志 extra 字段中合并上下文并转换时区。"""

        if self.timezone is not None:
            record["time"] = record["time"].astimezone(self.timezone)
        record["extra"].update(get_log_context())
        return record


def configure_logging() -> None:
    """初始化日志输出，开发环境启用彩色格式。"""

    global logger

    loguru_logger.remove()

    level = settings.log_level.upper()
    colorize = settings.environment.lower() == "development"

    loguru_logger.configure(extra=_DEFAULT_EXTRAS)
    # 日志格式中追加时区信息，方便排查跨时区问题
    def formatter(record: Dict[str, Any]) -> str:
        time_part = (
            f"<green>{record['time'].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} "
            f"{record['time'].strftime('%z')}</green>"
        )
        level_part = f"<level>{record['level'].name: <2}</level>"
        base = f"{time_part} | {level_part}"

        extra = record.get("extra", {})
        extras_to_show = []
        for label, field in [
            ("tenant", "tenant_id"),
            ("user", "user_id"),
            ("req", "request_id"),
            ("component", "component"),
            ("method", "method"),
            ("path", "path"),
            ("status", "status"),
            ("error", "error"),
            ("params", "params"),
            ("duration", "duration_ms"),
        ]:
            value = extra.get(field)
            if value not in (None, "", "-", []):
                if field in {"component", "method", "path", "error", "status"}:
                    extras_to_show.append(str(value))
                elif field == "duration_ms":
                    extras_to_show.append(f"{label}={value}ms")
                else:
                    extras_to_show.append(f"{label}={value}")

        if extras_to_show:
            base += " | " + " ".join(extras_to_show)

        component = extra.get("component")
        include_location = component not in {"api", "http", "server_error"}

        message = record.get("message", "")
        if include_location:
            location = f"<cyan>{record['name']}</cyan>:<cyan>{record['function']}</cyan>:<cyan>{record['line']}</cyan>"
            return f"{base} | {location} - <level>{message}</level>\n"
        return f"{base} - <level>{message}</level>\n"

    loguru_logger.add(
        sys.stdout,
        level=level,
        colorize=colorize,
        backtrace=settings.debug,
        diagnose=settings.debug,
        format=formatter,
    )
    shanghai_tz = ZoneInfo("Asia/Shanghai")
    logger = loguru_logger.patch(ContextInjector(shanghai_tz))


logger = loguru_logger
