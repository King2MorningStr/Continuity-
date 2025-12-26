# IVM Architecture for UDAC Portal

## Isotropic Vector Matrix Principles Applied

The UDAC Portal has been architected using principles from the **Isotropic Vector Matrix (IVM)** - a geometric framework that represents maximum structural efficiency through balanced, distributed force across all vectors.

### Core IVM Principles

1. **Isotropic (Equal in All Directions)**
   - Every component has equal error resilience
   - No privileged failure paths
   - Uniform protection across all operations

2. **Balanced Load Distribution**
   - Errors don't cascade through the system
   - Circuit breakers prevent overload
   - Graceful degradation under stress

3. **Self-Healing Coherence**
   - Automatic recovery from failures
   - Circuit breakers reset after timeout
   - System maintains stability under stress

4. **Minimal Complexity, Maximum Efficiency**
   - Lightweight error handling patterns
   - No over-engineering
   - Simple, effective solutions

---

## Architecture Components

### 1. IVM Resilience Layer (`ivm_resilience.py`)

The foundation of our crash-resistant architecture:

```python
@ivm_resilient(component="my_component", fallback=default_value)
def critical_operation():
    # Protected operation
    pass
```

**Features:**
- **Circuit Breakers**: Prevent cascade failures
- **Automatic Fallbacks**: Graceful degradation
- **Error Logging**: Bounded memory tracking
- **Self-Healing**: Auto-recovery after timeout

**Circuit Breaker Pattern:**
```
Normal → Failures Accumulate → Circuit Opens → Timeout → Circuit Closes
  ↓           ↓                     ↓              ↓            ↓
Success   Threshold Met      Block Requests   Self-Heal    Try Again
```

### 2. Memory Management (IVM Equilibrium)

Following the IVM principle of maintaining balance:

```python
# Bounded collections prevent memory leaks
IVMMemoryManager.bounded_append(collection, item, max_size=100)
IVMMemoryManager.bounded_dict(dictionary, max_size=100)
```

**Applied to:**
- Conversation threads (max 500 turns → prune to 250)
- Global thread dictionary (max 100 threads)
- Cross-platform memories (max 100 entries)
- Error logs (max 100 entries)

### 3. Async/Sync Bridge

Handles the tetrahedral stress of different execution contexts:

```python
# Safely bridge async and sync worlds
IVMAsyncBridge.safe_create_task(coro, fallback_sync=sync_function)
```

**Use Cases:**
- WebView JavaScript injection (async preferred, sync fallback)
- Event loop unavailability
- Threading vs. asyncio coordination

### 4. Production Health Monitoring

System coherence tracking:

```python
from udac_portal.production_config import HEALTH

HEALTH.get_health_status()  # Returns health metrics
HEALTH.get_health_report()  # Human-readable report
```

**Metrics Tracked:**
- Total sessions / messages
- Error rate (target: <5%)
- Circuit breaker activations
- Memory warnings
- Health score (0-100)

---

## IVM Protection Map

### Component Protection Matrix

| Component | Protection Type | Fallback Strategy |
|-----------|----------------|-------------------|
| `app.on_send_press()` | Circuit Breaker | Use raw text, skip enrichment |
| `app.on_webview_loaded()` | Async Bridge | Thread-based injection fallback |
| `engine.enrich_input()` | Circuit Breaker | Return raw text without context |
| `engine.record_output()` | Silent Protection | Skip recording, continue |
| `session.on_user_submit()` | Safe Call Wrapper | Return minimal payload |

### Error Handling Flow

```
User Action
    ↓
@ivm_resilient decorator
    ↓
Circuit Breaker Check → [OPEN?] → Return Fallback
    ↓ [CLOSED]
Execute Operation
    ↓
[SUCCESS] → Record Success → Continue
    ↓
[FAILURE] → Log Error → Record Failure → Check Threshold
                            ↓
                    [Threshold Met] → Open Circuit
                            ↓
                    Return Fallback
```

### Memory Equilibrium Flow

```
Data Added to Collection
    ↓
Size Check
    ↓
[Over Limit?]
    ↓ YES
Prune to Equilibrium (50% or last N items)
    ↓
System Balanced
```

---

## Production-Ready Features

### 1. Crash Logging
- Global exception hooks installed
- Persistent on-device logs
- Full Python tracebacks
- Thread/async exception capture

**Location:** `$HOME/udac_logs/udac_crash.log`

### 2. Circuit Breaker Protection

**Thresholds:**
- Failure count: 5 consecutive failures
- Timeout: 60 seconds
- Auto-recovery: Yes

**Protected Operations:**
- WebView JavaScript injection
- Continuity enrichment
- Session management
- Message sending

### 3. Memory Limits

**Enforced Boundaries:**
- Thread turns: 500 max → prune to 250
- Global threads: 100 max
- Cross-platform memory: 100 entries
- Error logs: 100 entries
- Seen message hashes (JS): 500 → prune to 250

### 4. Configuration Management

```python
from udac_portal.production_config import CONFIG

# Adjust production settings
CONFIG.max_threads_per_platform = 20
CONFIG.circuit_breaker_timeout_seconds = 120
CONFIG.save()
```

---

## IVM Principles in Practice

### Example: WebView Injection

**Problem:** JavaScript injection can fail (WebView not ready, network issue, DOM not loaded)

**IVM Solution:**
```python
@ivm_resilient(component="webview_injection")
def safe_inject():
    script = PortalScriptBuilder.build(platform)
    self.webview.evaluate_javascript(script)

# Async with sync fallback (balanced distribution)
IVMAsyncBridge.safe_create_task(
    delayed_inject(),
    fallback_sync=sync_inject
)
```

**Result:**
- If async fails → sync fallback
- If injection fails → circuit breaker prevents repeated attempts
- System continues functioning without crashes

### Example: Continuity Enrichment

**Problem:** Enrichment logic complex, many failure points (file I/O, threading, memory)

**IVM Solution:**
```python
@ivm_resilient(component="continuity_enrichment", fallback=default_payload)
def enrich_input(platform_id, text):
    try:
        return _enrich_input_internal(platform_id, text)
    except:
        return ContinuityPayload(final_prompt_text=text, ...)
```

**Result:**
- If enrichment fails → user gets raw text (degraded but functional)
- Circuit breaker prevents repeated failures
- App never crashes from continuity logic

### Example: Memory Management

**Problem:** Unbounded growth in conversation history leads to OOM crashes

**IVM Solution:**
```python
# Maintain equilibrium
if len(thread.turns) > 500:
    thread.turns = thread.turns[-250:]  # Keep recent half

# Bounded dictionaries
IVMMemoryManager.bounded_dict(self.global_threads, max_size=100)
```

**Result:**
- Memory usage bounded
- System maintains coherence
- Long-running sessions don't crash

---

## Testing IVM Resilience

### 1. Circuit Breaker Test
```python
# Trigger 5+ failures to open circuit
for i in range(6):
    result = engine.enrich_input("chatgpt", "test")
    # Should see circuit open message after 5 failures

# Wait 60 seconds
time.sleep(61)

# Circuit should auto-heal
result = engine.enrich_input("chatgpt", "test")
```

### 2. Memory Test
```python
# Add 600 turns to thread
for i in range(600):
    thread.add_turn("user", f"message {i}")

# Check pruning
assert len(thread.turns) <= 500
```

### 3. Async Bridge Test
```python
# Test with no event loop
def sync_fallback():
    print("Sync fallback executed")

IVMAsyncBridge.safe_create_task(
    my_async_func(),
    fallback_sync=sync_fallback
)
```

---

## Maintenance & Monitoring

### Health Checks

```python
from udac_portal.production_config import HEALTH

# Get health status
status = HEALTH.get_health_status()
print(f"Status: {status['status']}")
print(f"Health Score: {status['health_score']}/100")
print(f"Error Rate: {status['error_rate']}%")

# Get full report
print(HEALTH.get_health_report())
```

### Circuit Breaker Status

```python
from udac_portal.ivm_resilience import RESILIENCE

# Check system health
health = RESILIENCE.get_system_health()
print(health)

# Output:
# {
#   "circuit_breakers": {
#     "webview_injection": {"is_open": False, "failures": 0},
#     "continuity_enrichment": {"is_open": False, "failures": 0}
#   },
#   "recent_errors": 5,
#   "error_rate": 2
# }
```

### Error Log Review

```python
# View recent errors
for error in RESILIENCE.error_log:
    print(f"{error['component']}: {error['error']}")
    print(f"  Time: {error['timestamp']}")
    print(f"  Context: {error['context']}")
```

---

## Play Store Readiness

### Crash Prevention ✓
- Global exception hooks
- Circuit breakers on all critical paths
- Graceful degradation
- Comprehensive error logging

### Performance ✓
- Bounded memory usage
- No memory leaks
- Efficient pruning algorithms
- Thread-safe operations

### Stability ✓
- Self-healing circuit breakers
- Async/sync bridge for robustness
- No single point of failure
- Comprehensive fallback strategies

### Monitoring ✓
- Health status tracking
- Error rate monitoring
- Circuit breaker metrics
- Session statistics

---

## Summary

The IVM architecture transforms UDAC Portal from a potentially fragile WebView app into a production-grade, crash-resistant system:

1. **Isotropic Protection**: Every operation equally protected
2. **Balanced Distribution**: Load spreads evenly, no cascade failures
3. **Self-Healing**: Automatic recovery from errors
4. **Minimal Complexity**: Simple, effective patterns
5. **Maximum Efficiency**: Lightweight overhead, robust results

Like the IVM's tetrahedral-octahedral lattice that distributes force evenly across all connections, our architecture distributes error handling and resilience evenly across all components - creating a stable, coherent system that remains functional under stress.

**Result:** A production-ready app that gracefully handles failures, maintains user experience, and never crashes unexpectedly.
