"""
UDAC Crash Trap (Android-friendly)

Installs global exception hooks so uncaught Python exceptions are written
to a persistent log file instead of causing a silent Android crash dialog.

This does NOT change app behavior; it only makes crashes visible.
"""
from __future__ import annotations

import asyncio
import os
import sys
import threading
import traceback
from datetime import datetime

try:
    import platformdirs
except Exception:  # pragma: no cover
    platformdirs = None  # type: ignore


def _default_log_path() -> str:
    # Prefer a stable, app-private location.
    # On Android (Chaquopy), HOME usually points to app files dir.
    home = os.environ.get("HOME")
    if home:
        base = os.path.join(home, "udac_logs")
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, "udac_crash.log")

    if platformdirs is not None:
        base = platformdirs.user_data_dir("UDAC Portal", "UDAC")
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, "udac_crash.log")

    # Last resort: current working directory
    return os.path.abspath("udac_crash.log")


def _write_log(text: str, path: str) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        pass
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text)
            if not text.endswith("\n"):
                f.write("\n")
    except Exception:
        # If we can't write, at least try stderr.
        try:
            sys.stderr.write(text + "\n")
        except Exception:
            pass


def install(log_path: str | None = None) -> str:
    """
    Install crash hooks. Returns the log_path in use.
    """
    path = log_path or _default_log_path()

    banner = (
        "\n"
        "================ UDAC Crash Trap Installed ================\n"
        f"Timestamp: {datetime.utcnow().isoformat()}Z\n"
        f"Python: {sys.version}\n"
        f"Log path: {path}\n"
        "===========================================================\n"
    )
    _write_log(banner, path)

    def _format(exc_type, exc, tb) -> str:
        return "".join(traceback.format_exception(exc_type, exc, tb))

    def _hook(exc_type, exc, tb):
        txt = (
            "\n"
            "------------------- UNCAUGHT EXCEPTION -------------------\n"
            f"Timestamp: {datetime.utcnow().isoformat()}Z\n"
            + _format(exc_type, exc, tb) +
            "----------------------------------------------------------\n"
        )
        _write_log(txt, path)

    sys.excepthook = _hook

    # Thread exceptions (Python 3.8+)
    if hasattr(threading, "excepthook"):
        def _thread_hook(args):
            _hook(args.exc_type, args.exc_value, args.exc_traceback)
        threading.excepthook = _thread_hook  # type: ignore[attr-defined]

    # Asyncio exceptions
    try:
        loop = asyncio.get_event_loop()
        def _asyncio_handler(loop, context):
            exc = context.get("exception")
            if exc is not None:
                _hook(type(exc), exc, exc.__traceback__)
            else:
                msg = context.get("message", "Asyncio error (no exception object)")
                _write_log(
                    "\n--- ASYNCIO CONTEXT ERROR ---\n"
                    f"Timestamp: {datetime.utcnow().isoformat()}Z\n"
                    f"{msg}\n"
                    "-----------------------------\n",
                    path,
                )
        loop.set_exception_handler(_asyncio_handler)
    except Exception as e:
        _write_log(f"[CrashTrap] Could not set asyncio handler: {e}", path)

    return path
