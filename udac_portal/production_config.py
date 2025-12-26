"""
Production Configuration & Health Monitoring
============================================
Production-ready configuration following IVM principles of system coherence.
"""

import os
import time
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from pathlib import Path
from platformdirs import user_data_dir

APP_NAME = "UDAC Portal"
APP_AUTHOR = "Sunni"
APP_VERSION = "1.0.0"


@dataclass
class ProductionConfig:
    """Production configuration settings."""

    # App metadata
    version: str = APP_VERSION
    environment: str = "production"  # development, staging, production

    # Performance settings
    max_webview_cache_mb: int = 100
    javascript_injection_timeout_ms: int = 5000
    webview_load_timeout_ms: int = 30000

    # Memory management (IVM equilibrium)
    max_threads_per_platform: int = 10
    max_turns_per_thread: int = 500
    max_cross_platform_memories: int = 100
    max_error_log_entries: int = 100

    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 60

    # Storage settings
    enable_state_persistence: bool = True
    auto_save_interval_seconds: int = 30
    max_crash_log_size_mb: int = 10

    # Feature flags
    enable_continuity: bool = True
    enable_data_trading: bool = True
    enable_voice_support: bool = False  # Future feature
    enable_telemetry: bool = False  # Opt-in telemetry

    # Safety & compliance
    enable_content_filtering: bool = False
    max_prompt_length: int = 10000
    rate_limit_messages_per_minute: int = 60

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductionConfig':
        """Load from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})

    def save(self):
        """Persist configuration."""
        config_dir = user_data_dir(APP_NAME, APP_AUTHOR)
        Path(config_dir).mkdir(parents=True, exist_ok=True)
        config_file = os.path.join(config_dir, "production_config.json")

        try:
            with open(config_file, 'w') as f:
                json.dump(self.to_dict(), f, indent=2)
        except Exception as e:
            print(f"[Config] Failed to save configuration: {e}")

    @classmethod
    def load(cls) -> 'ProductionConfig':
        """Load persisted configuration."""
        config_dir = user_data_dir(APP_NAME, APP_AUTHOR)
        config_file = os.path.join(config_dir, "production_config.json")

        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                return cls.from_dict(data)
            except Exception as e:
                print(f"[Config] Failed to load configuration: {e}")

        # Return defaults
        return cls()


class HealthMonitor:
    """
    Production health monitoring system.
    Tracks system vitals following IVM principle of maintaining coherence.
    """

    def __init__(self):
        self.start_time = time.time()
        self.metrics = {
            "total_sessions": 0,
            "total_messages": 0,
            "total_errors": 0,
            "total_circuit_breaks": 0,
            "memory_warnings": 0
        }
        self._lock = __import__('threading').RLock()

    def record_session_start(self):
        """Record new session started."""
        with self._lock:
            self.metrics["total_sessions"] += 1

    def record_message(self):
        """Record message processed."""
        with self._lock:
            self.metrics["total_messages"] += 1

    def record_error(self):
        """Record error occurred."""
        with self._lock:
            self.metrics["total_errors"] += 1

    def record_circuit_break(self):
        """Record circuit breaker activation."""
        with self._lock:
            self.metrics["total_circuit_breaks"] += 1

    def record_memory_warning(self):
        """Record memory warning."""
        with self._lock:
            self.metrics["memory_warnings"] += 1

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        with self._lock:
            uptime_seconds = time.time() - self.start_time
            uptime_hours = uptime_seconds / 3600

            # Calculate health score (0-100)
            health_score = 100
            error_rate = self.metrics["total_errors"] / max(self.metrics["total_messages"], 1)
            if error_rate > 0.1:  # More than 10% errors
                health_score -= 50
            elif error_rate > 0.05:  # More than 5% errors
                health_score -= 25

            if self.metrics["total_circuit_breaks"] > 10:
                health_score -= 20

            if self.metrics["memory_warnings"] > 5:
                health_score -= 10

            status = "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "unhealthy"

            return {
                "status": status,
                "health_score": max(0, health_score),
                "uptime_hours": round(uptime_hours, 2),
                "metrics": self.metrics.copy(),
                "error_rate": round(error_rate * 100, 2),
                "timestamp": time.time()
            }

    def get_health_report(self) -> str:
        """Get human-readable health report."""
        health = self.get_health_status()
        return f"""
UDAC Portal Health Report
=========================
Status: {health['status'].upper()}
Health Score: {health['health_score']}/100
Uptime: {health['uptime_hours']} hours

Metrics:
- Sessions: {health['metrics']['total_sessions']}
- Messages: {health['metrics']['total_messages']}
- Errors: {health['metrics']['total_errors']} ({health['error_rate']}%)
- Circuit Breaks: {health['metrics']['total_circuit_breaks']}
- Memory Warnings: {health['metrics']['memory_warnings']}

Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(health['timestamp']))}
        """.strip()


# Global instances
CONFIG = ProductionConfig.load()
HEALTH = HealthMonitor()


# Export public API
__all__ = ['ProductionConfig', 'HealthMonitor', 'CONFIG', 'HEALTH']
