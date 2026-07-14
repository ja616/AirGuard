import time
import logging
from typing import Callable, Any
from functools import wraps
from backend.observability.metrics import increment_counter, observe_histogram

logger = logging.getLogger("airguard.integrations")

def with_telemetry(integration_name: str, operation: str):
    """
    Decorator to automatically log latency, success, and failure rates for integrations.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"[{integration_name}] {operation} succeeded in {duration:.3f}s",
                    extra={"integration": integration_name, "operation": operation, "duration_ms": duration * 1000}
                )
                observe_histogram("airguard_integration_latency_seconds", duration, {"integration": integration_name, "operation": operation})
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"[{integration_name}] {operation} failed after {duration:.3f}s: {e}",
                    extra={"integration": integration_name, "operation": operation, "duration_ms": duration * 1000, "error": str(e)}
                )
                observe_histogram("airguard_integration_latency_seconds", duration, {"integration": integration_name, "operation": operation})
                increment_counter("airguard_integration_errors_total", {"integration": integration_name, "operation": operation})
                raise
        return wrapper
    return decorator
