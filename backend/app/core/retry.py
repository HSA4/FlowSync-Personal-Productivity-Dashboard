"""Retry Logic for External API Calls"""
import asyncio
from typing import Callable, TypeVar, Optional, Any
from functools import wraps
from datetime import datetime, timedelta

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


class RetryStats:
    """Track retry statistics"""

    def __init__(self):
        self.attempts = 0
        self.successes = 0
        self.failures = 0
        self.total_delay = 0.0
        self.last_attempt: Optional[datetime] = None
        self.last_success: Optional[datetime] = None
        self.last_failure: Optional[datetime] = None

    def record_attempt(self):
        """Record an attempt"""
        self.attempts += 1
        self.last_attempt = datetime.utcnow()

    def record_success(self, delay: float = 0.0):
        """Record a successful attempt"""
        self.successes += 1
        self.total_delay += delay
        self.last_success = datetime.utcnow()

    def record_failure(self):
        """Record a failed attempt"""
        self.failures += 1
        self.last_failure = datetime.utcnow()

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.attempts == 0:
            return 0.0
        return self.successes / self.attempts


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay for the next retry attempt with exponential backoff and jitter"""
    delay = config.base_delay * (config.exponential_base ** attempt)

    # Apply jitter to avoid thundering herd
    if config.jitter:
        delay = delay * (0.5 + asyncio.get_event_loop().time() % 0.5)

    return min(delay, config.max_delay)


async def retry_async(
    func: Callable[..., T],
    config: Optional[RetryConfig] = None,
    operation_name: str = "operation",
    *args: Any,
    **kwargs: Any,
) -> T:
    """
    Retry an async function with exponential backoff

    Args:
        func: The async function to retry
        config: Retry configuration
        operation_name: Name of the operation for logging
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The result of the function call

    Raises:
        The last exception if all retries fail
    """
    if config is None:
        config = RetryConfig()

    stats = RetryStats()
    last_exception = None

    for attempt in range(config.max_attempts):
        stats.record_attempt()

        try:
            result = await func(*args, **kwargs)
            stats.record_success()

            if attempt > 0:
                logger.info(
                    f"{operation_name} succeeded after {attempt + 1} attempts",
                    extra={
                        "operation": operation_name,
                        "attempts": attempt + 1,
                        "total_delay": stats.total_delay,
                    },
                )

            return result

        except Exception as e:
            last_exception = e
            stats.record_failure()

            if attempt < config.max_attempts - 1:
                delay = calculate_delay(attempt, config)
                stats.total_delay += delay

                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{config.max_attempts}), "
                    f"retrying in {delay:.2f}s",
                    extra={
                        "operation": operation_name,
                        "attempt": attempt + 1,
                        "max_attempts": config.max_attempts,
                        "delay": delay,
                        "error": str(e),
                    },
                )

                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"{operation_name} failed after {config.max_attempts} attempts",
                    extra={
                        "operation": operation_name,
                        "attempts": config.max_attempts,
                        "total_delay": stats.total_delay,
                        "error": str(e),
                    },
                )

    raise last_exception


def retry_decorator(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    operation_name: str = "operation",
):
    """
    Decorator for retrying async functions

    Args:
        max_attempts: Maximum number of attempts
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        operation_name: Name of the operation for logging
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
            )
            return await retry_async(
                func,
                config,
                operation_name,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator


class SyncOperationTracker:
    """Track sync operations and their status"""

    def __init__(self):
        self._operations: dict[str, RetryStats] = {}

    def get_stats(self, operation: str) -> RetryStats:
        """Get stats for an operation"""
        if operation not in self._operations:
            self._operations[operation] = RetryStats()
        return self._operations[operation]

    def reset_stats(self, operation: str):
        """Reset stats for an operation"""
        if operation in self._operations:
            del self._operations[operation]

    def get_all_stats(self) -> dict[str, dict]:
        """Get all operation stats"""
        return {
            op: {
                "attempts": stats.attempts,
                "successes": stats.successes,
                "failures": stats.failures,
                "success_rate": stats.success_rate,
                "total_delay": stats.total_delay,
                "last_attempt": stats.last_attempt.isoformat() if stats.last_attempt else None,
                "last_success": stats.last_success.isoformat() if stats.last_success else None,
                "last_failure": stats.last_failure.isoformat() if stats.last_failure else None,
            }
            for op, stats in self._operations.items()
        }


# Global tracker instance
sync_tracker = SyncOperationTracker()
