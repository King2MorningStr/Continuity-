"""
IVM Resilience Layer
====================
Inspired by the Isotropic Vector Matrix - creates balanced, distributed resilience.

Just as the IVM distributes force evenly across all vectors in 3D space,
this module distributes error handling and recovery evenly across all system components.

Principles:
1. Isotropic (Equal in all directions) - Every operation gets equal protection
2. Balanced Distribution - No single point of failure
3. Self-Healing - System maintains coherence under stress
4. Minimal Complexity - Maximum efficiency through simple patterns
"""

import functools
import threading
import time
from typing import Callable, Any, Optional, TypeVar, Dict
from dataclasses import dataclass, field
from collections import deque
import traceback

T = TypeVar('T')


@dataclass
class CircuitBreaker:
    """
    Circuit breaker pattern - prevents cascade failures.
    Like tetrahedral support in IVM: when one path fails, load redistributes.
    """
    name: str
    failure_threshold: int = 5
    timeout: float = 60.0

    # State
    failures: int = 0
    last_failure_time: float = 0
    is_open: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def record_success(self):
        """Record successful operation - close circuit if open."""
        with self._lock:
            self.failures = 0
            self.is_open = False

    def record_failure(self):
        """Record failure - open circuit if threshold exceeded."""
        with self._lock:
            self.failures += 1
            self.last_failure_time = time.time()

            if self.failures >= self.failure_threshold:
                self.is_open = True
                print(f"[IVM] Circuit breaker OPEN: {self.name} ({self.failures} failures)")

    def can_attempt(self) -> bool:
        """Check if we can attempt operation."""
        with self._lock:
            if not self.is_open:
                return True

            # Check if timeout has passed - self-healing
            if time.time() - self.last_failure_time > self.timeout:
                self.is_open = False
                self.failures = 0
                print(f"[IVM] Circuit breaker CLOSED (self-healed): {self.name}")
                return True

            return False


class IVMResilientSystem:
    """
    Central resilience coordinator - maintains system coherence.
    Like the IVM lattice structure: interconnected, balanced, self-supporting.
    """

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_log: deque = deque(maxlen=100)  # Bounded memory
        self._lock = threading.RLock()

    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a component."""
        with self._lock:
            if name not in self.circuit_breakers:
                self.circuit_breakers[name] = CircuitBreaker(name=name)
            return self.circuit_breakers[name]

    def log_error(self, component: str, error: Exception, context: str = ""):
        """Log error with bounded memory (IVM principle: maintain equilibrium)."""
        with self._lock:
            error_entry = {
                "component": component,
                "error": str(error),
                "type": type(error).__name__,
                "context": context,
                "timestamp": time.time(),
                "traceback": traceback.format_exc()
            }
            self.error_log.append(error_entry)

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        with self._lock:
            return {
                "circuit_breakers": {
                    name: {
                        "is_open": cb.is_open,
                        "failures": cb.failures
                    }
                    for name, cb in self.circuit_breakers.items()
                },
                "recent_errors": len(self.error_log),
                "error_rate": len([e for e in self.error_log if time.time() - e["timestamp"] < 60])
            }


# Global resilience system instance
RESILIENCE = IVMResilientSystem()


def ivm_resilient(
    component: str,
    fallback: Optional[Any] = None,
    silent: bool = False,
    use_circuit_breaker: bool = True
):
    """
    Decorator that applies IVM resilience principles to any function.

    Provides:
    - Circuit breaker protection (distribute load when stressed)
    - Graceful error handling (maintain coherence)
    - Automatic fallback (self-healing)
    - Error logging (system awareness)

    Args:
        component: Component name for tracking
        fallback: Return value if operation fails
        silent: If True, suppress error logs
        use_circuit_breaker: If True, use circuit breaker pattern
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Check circuit breaker
            if use_circuit_breaker:
                cb = RESILIENCE.get_circuit_breaker(component)
                if not cb.can_attempt():
                    if not silent:
                        print(f"[IVM] Circuit open for {component}, using fallback")
                    return fallback

            try:
                result = func(*args, **kwargs)

                # Record success
                if use_circuit_breaker:
                    cb.record_success()

                return result

            except Exception as e:
                # Log error
                RESILIENCE.log_error(component, e, context=f"{func.__name__}")

                # Record failure
                if use_circuit_breaker:
                    cb.record_failure()

                # Report error (unless silent)
                if not silent:
                    print(f"[IVM] Error in {component}.{func.__name__}: {type(e).__name__}: {e}")

                # Return fallback
                return fallback

        return wrapper
    return decorator


def ivm_safe_call(func: Callable, *args, fallback=None, component="unknown", **kwargs):
    """
    Safely call any function with IVM resilience.
    Useful for callbacks and dynamic functions.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        RESILIENCE.log_error(component, e, context="safe_call")
        print(f"[IVM] Safe call failed in {component}: {e}")
        return fallback


class IVMMemoryManager:
    """
    Memory management following IVM equilibrium principle.
    Prevents unbounded growth while maintaining useful data.
    """

    @staticmethod
    def bounded_append(collection: list, item: Any, max_size: int):
        """Append to list with automatic pruning to maintain size."""
        collection.append(item)
        if len(collection) > max_size:
            # Keep most recent items
            del collection[:len(collection) - max_size]

    @staticmethod
    def bounded_dict(d: dict, max_size: int, key_accessor: Optional[Callable] = None):
        """Prune dictionary to max size, keeping most recent items."""
        if len(d) <= max_size:
            return

        # If we have a key accessor (for sorting), use it
        if key_accessor:
            items = sorted(d.items(), key=lambda x: key_accessor(x[1]), reverse=True)
            # Keep top max_size items
            to_keep = dict(items[:max_size])
            d.clear()
            d.update(to_keep)
        else:
            # Simple pruning - remove oldest half
            keys = list(d.keys())
            for key in keys[:len(keys) // 2]:
                d.pop(key, None)


class IVMAsyncBridge:
    """
    Bridges async/sync operations safely.
    Like IVM's structural integrity: handles stress from different directions.
    """

    @staticmethod
    def safe_async_to_sync(coro, timeout: float = 5.0, fallback=None):
        """
        Safely run async code from sync context.
        Returns fallback on error or timeout.
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't run in already-running loop, use thread
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result(timeout=timeout)
            else:
                return loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))
        except Exception as e:
            RESILIENCE.log_error("async_bridge", e, "safe_async_to_sync")
            return fallback

    @staticmethod
    def safe_create_task(coro, fallback_sync: Optional[Callable] = None):
        """
        Safely create async task, with sync fallback if needed.
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            return loop.create_task(coro)
        except RuntimeError as e:
            # No event loop - use fallback
            if fallback_sync:
                threading.Thread(target=fallback_sync, daemon=True).start()
            else:
                RESILIENCE.log_error("async_bridge", e, "safe_create_task")
            return None


# Export public API
__all__ = [
    'RESILIENCE',
    'ivm_resilient',
    'ivm_safe_call',
    'IVMMemoryManager',
    'IVMAsyncBridge',
    'CircuitBreaker'
]
