"""
UDAC Listener - Full Bidirectional Support
==========================================
HTTP server that handles:
1. POST /udac/event - Receive accessibility events (capture)
2. POST /udac/inject - Return messages with continuity context (inject)
3. GET /udac/stats - Get current statistics
4. GET /udac/health - Health check

The injection endpoint is the key to invisible continuity - it receives
the user's message and returns it with relevant context prepended.
"""

import json
import threading
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional, Callable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("UDAC")

# Thread-safe state storage
_state_lock = threading.Lock()
_state = {
    "total_events": 0,
    "total_injections": 0,
    "injections_applied": 0,
    "last_source": None,
    "last_text": "",
    "last_timestamp": 0,
    "platform_counts": {},
    "session_start": time.time(),
    "events_per_minute": 0,
    "recent_events": [],
}

# Callbacks
_event_processor: Optional[Callable[[Dict[str, Any]], None]] = None
_injection_processor: Optional[Callable[[str, str], Dict[str, Any]]] = None


def set_event_processor(processor: Callable[[Dict[str, Any]], None]):
    """Register callback for processing captured events."""
    global _event_processor
    _event_processor = processor
    logger.info("Event processor registered")


def set_injection_processor(processor: Callable[[str, str], Dict[str, Any]]):
    """
    Register callback for processing injection requests.

    The processor should accept (message: str, platform: str) and return:
    {
        "injected_message": str,  # Message with context prepended
        "injected": bool,         # Whether injection was applied
        "relevance": float,       # Relevance score 0-1
        "context_summary": str    # Brief description of injected context
    }
    """
    global _injection_processor
    _injection_processor = processor
    logger.info("Injection processor registered")


def _process_event(payload: Dict[str, Any]):
    """Process an incoming capture event."""
    text = (payload.get("text") or "").strip()
    source_app = (payload.get("source_app") or "").strip()
    event_type = payload.get("event_type", 0)
    timestamp = payload.get("timestamp", time.time() * 1000)

    # Map package names to friendly names
    platform_map = {
        "com.openai.chatgpt": "ChatGPT",
        "com.anthropic.claude": "Claude",
        "ai.perplexity.app.android": "Perplexity",
        "com.google.android.apps.bard": "Gemini",
        "UDAC_SERVICE": "System",
    }

    friendly_name = platform_map.get(source_app, source_app)

    with _state_lock:
        _state["total_events"] += 1
        _state["last_source"] = friendly_name
        _state["last_text"] = text
        _state["last_timestamp"] = timestamp

        if source_app:
            _state["platform_counts"][friendly_name] = (
                _state["platform_counts"].get(friendly_name, 0) + 1
            )

        _state["recent_events"].append({
            "source": friendly_name,
            "text": text[:200] if text else "",
            "timestamp": timestamp,
            "type": "capture",
        })
        if len(_state["recent_events"]) > 20:
            _state["recent_events"].pop(0)

        elapsed = time.time() - _state["session_start"]
        if elapsed > 0:
            _state["events_per_minute"] = round((_state["total_events"] / elapsed) * 60, 2)

    # Route to Trinity processor
    if _event_processor and text:
        try:
            event_data = {
                "platform": friendly_name,
                "text": text,
                "event_type": event_type,
                "timestamp": timestamp,
                "package_name": source_app,
            }
            _event_processor(event_data)
        except Exception as e:
            logger.error(f"Event processor error: {e}")

    logger.info(f"[CAPTURE] {friendly_name}: {text[:60]}...")


def _process_injection(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an injection request - return message with continuity context.
    """
    message = (payload.get("message") or "").strip()
    platform = (payload.get("platform") or "Unknown").strip()

    with _state_lock:
        _state["total_injections"] += 1

    # Default response (no injection)
    response = {
        "original_message": message,
        "injected_message": message,
        "injected": False,
        "relevance": 0.0,
        "context_summary": "",
    }

    if not message:
        return response

    # Use injection processor if registered
    if _injection_processor:
        try:
            result = _injection_processor(message, platform)

            if result.get("injected", False):
                with _state_lock:
                    _state["injections_applied"] += 1
                    _state["recent_events"].append({
                        "source": platform,
                        "text": f"[INJECTED] {message[:100]}",
                        "timestamp": time.time() * 1000,
                        "type": "injection",
                    })
                    if len(_state["recent_events"]) > 20:
                        _state["recent_events"].pop(0)

            response.update(result)
            logger.info(f"[INJECT] {platform}: injected={result.get('injected')}, relevance={result.get('relevance', 0):.2f}")

        except Exception as e:
            logger.error(f"Injection processor error: {e}")
    else:
        logger.warning("No injection processor registered")

    return response


class _UDACRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for UDAC endpoints."""

    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers.get("Content-Length", 0))

        if content_length == 0:
            self.send_error(400, "Empty body")
            return

        try:
            body = self.rfile.read(content_length)
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON: {e}")
            self.send_error(400, "Invalid JSON")
            return
        except Exception as e:
            logger.error(f"Request error: {e}")
            self.send_error(500, "Internal Error")
            return

        # Route to appropriate handler
        if self.path == "/udac/event":
            _process_event(payload)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")

        elif self.path == "/udac/inject":
            response = _process_injection(payload)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))

        else:
            self.send_error(404, "Not Found")

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/udac/stats":
            stats = get_udac_stats()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(stats, indent=2).encode("utf-8"))

        elif self.path == "/udac/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"UDAC Listener OK")

        else:
            self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def start_udac_listener(port: int = 7013) -> threading.Thread:
    """Start the UDAC HTTP server."""
    server = HTTPServer(("127.0.0.1", port), _UDACRequestHandler)
    server.socket.settimeout(1)

    def run_server():
        logger.info(f"UDAC Listener started on http://127.0.0.1:{port}")
        logger.info(f"  - POST /udac/event  (capture)")
        logger.info(f"  - POST /udac/inject (inject)")
        logger.info(f"  - GET  /udac/stats  (statistics)")
        try:
            server.serve_forever()
        except Exception as e:
            logger.error(f"Server error: {e}")

    thread = threading.Thread(target=run_server, name="UDAC-Listener", daemon=True)
    thread.start()
    return thread


def get_udac_stats() -> Dict[str, Any]:
    """Get current statistics."""
    with _state_lock:
        return {
            "total_events": _state["total_events"],
            "total_injections": _state["total_injections"],
            "injections_applied": _state["injections_applied"],
            "injection_rate": (
                round(_state["injections_applied"] / _state["total_injections"], 2)
                if _state["total_injections"] > 0 else 0
            ),
            "last_source": _state["last_source"],
            "last_text": _state["last_text"],
            "last_timestamp": _state["last_timestamp"],
            "platform_counts": dict(_state["platform_counts"]),
            "events_per_minute": _state["events_per_minute"],
            "session_duration_seconds": round(time.time() - _state["session_start"], 1),
            "recent_events": list(_state["recent_events"]),
        }


def reset_udac_stats():
    """Reset all statistics."""
    with _state_lock:
        _state["total_events"] = 0
        _state["total_injections"] = 0
        _state["injections_applied"] = 0
        _state["last_source"] = None
        _state["last_text"] = ""
        _state["last_timestamp"] = 0
        _state["platform_counts"] = {}
        _state["session_start"] = time.time()
        _state["events_per_minute"] = 0
        _state["recent_events"] = []
    logger.info("UDAC stats reset")


__all__ = [
    "start_udac_listener",
    "get_udac_stats",
    "set_event_processor",
    "set_injection_processor",
    "reset_udac_stats",
]
