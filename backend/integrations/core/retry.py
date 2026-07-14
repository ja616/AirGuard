import time
import logging
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger("airguard.integrations.retry")

class IntegrationException(Exception):
    """Base exception for all integration failures."""
    pass

class CircuitBreakerOpenException(IntegrationException):
    """Thrown when the circuit breaker is open to prevent cascading failures."""
    pass

def with_retry(max_retries: int = 3, initial_backoff: float = 1.0, max_backoff: float = 16.0):
    """
    Exponential backoff retry decorator enforcing per-service resiliency policies.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            retries = 0
            backoff = initial_backoff
            
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded. Failing.")
                        raise IntegrationException(f"Integration call failed after {max_retries} retries: {str(e)}") from e
                        
                    logger.warning(f"Call failed: {str(e)}. Retrying in {backoff}s ({retries}/{max_retries})")
                    time.sleep(backoff)
                    backoff = min(backoff * 2, max_backoff)
        return wrapper
    return decorator
