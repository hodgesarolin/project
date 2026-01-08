"""
Core infrastructure for resilient agent execution.

Implements:
- Exponential backoff with jitter for retries
- Circuit breaker pattern for fault tolerance
- Error classification (retriable vs non-retriable)
- State management for resumability
- Observability hooks for production tracing
"""

import asyncio
import random
import time
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable, Any, TypeVar, Generic
from functools import wraps

logger = logging.getLogger(__name__)


# =============================================================================
# Error Classification
# =============================================================================

class AgentError(Exception):
    """Base exception for agent errors."""
    pass


class RetriableError(AgentError):
    """
    Error that may succeed on retry.

    Use for: rate limits, network timeouts, temporary service outages.
    """
    pass


class NonRetriableError(AgentError):
    """
    Error that will not succeed on retry.

    Use for: invalid input, authentication failures, missing resources.
    """
    pass


class CircuitOpenError(AgentError):
    """Raised when circuit breaker is open and blocking requests."""
    pass


# =============================================================================
# Retry Configuration
# =============================================================================

@dataclass
class RetryConfig:
    """
    Configuration for retry behavior with exponential backoff and jitter.

    Best practices:
    - Use 3-5 retries for external API calls
    - Base delay of 1-5 seconds depending on service
    - Always include jitter to prevent synchronized retry storms
    """
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # cap delay at 60 seconds
    exponential_base: float = 2.0
    jitter_range: float = 0.5  # ±50% jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        # Exponential backoff
        delay = self.base_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        # Add jitter (±jitter_range)
        jitter = delay * self.jitter_range * (2 * random.random() - 1)
        return max(0, delay + jitter)


# =============================================================================
# Circuit Breaker Pattern
# =============================================================================

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for fault tolerance.

    Prevents cascading failures by stopping requests to failing services.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, requests blocked immediately
    - HALF_OPEN: Testing recovery, limited requests allowed

    Best practices:
    - Set failure_threshold based on acceptable error rate
    - recovery_timeout should match expected service recovery time
    - Use separate circuit breakers for different services
    """
    failure_threshold: int = 5  # failures before opening
    recovery_timeout: float = 30.0  # seconds before trying again
    half_open_max_calls: int = 3  # test calls in half-open state

    # Internal state
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: Optional[float] = field(default=None, init=False)
    _half_open_calls: int = field(default=0, init=False)

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for timeout-based transitions."""
        if self._state == CircuitState.OPEN:
            if self._last_failure_time is not None:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
        return self._state

    def record_success(self) -> None:
        """Record a successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1
            if self._half_open_calls >= self.half_open_max_calls:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                logger.info("Circuit breaker CLOSED after successful recovery")
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
            logger.warning("Circuit breaker OPEN after half-open failure")
        elif self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(f"Circuit breaker OPEN after {self._failure_count} failures")

    def allow_request(self) -> bool:
        """Check if a request should be allowed."""
        state = self.state  # triggers timeout check
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.HALF_OPEN:
            return True
        return False  # OPEN

    def reset(self) -> None:
        """Manually reset the circuit breaker."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._half_open_calls = 0


# =============================================================================
# Retry Decorator with Circuit Breaker
# =============================================================================

T = TypeVar('T')


def with_retry(
    retry_config: Optional[RetryConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
):
    """
    Decorator for retry logic with optional circuit breaker.

    Args:
        retry_config: Configuration for retry behavior
        circuit_breaker: Optional circuit breaker for fault tolerance
        on_retry: Optional callback called before each retry (attempt_num, exception)

    Example:
        @with_retry(RetryConfig(max_retries=3), circuit_breaker)
        async def call_external_api():
            ...
    """
    config = retry_config or RetryConfig()

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check circuit breaker
            if circuit_breaker and not circuit_breaker.allow_request():
                raise CircuitOpenError(
                    f"Circuit breaker open, blocking request to {func.__name__}"
                )

            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    result = await func(*args, **kwargs)
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    return result

                except NonRetriableError:
                    # Don't retry non-retriable errors
                    if circuit_breaker:
                        circuit_breaker.record_failure()
                    raise

                except Exception as e:
                    last_exception = e

                    # Check if this is a retriable error
                    if not isinstance(e, (RetriableError, asyncio.TimeoutError, ConnectionError)):
                        if circuit_breaker:
                            circuit_breaker.record_failure()
                        raise

                    if attempt < config.max_retries:
                        delay = config.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )

                        if on_retry:
                            on_retry(attempt + 1, e)

                        await asyncio.sleep(delay)
                    else:
                        if circuit_breaker:
                            circuit_breaker.record_failure()
                        raise

            # Should never reach here, but just in case
            raise last_exception or AgentError("Retry exhausted")

        return wrapper
    return decorator


# =============================================================================
# State Management for Resumability
# =============================================================================

@dataclass
class AgentState:
    """
    Persistent state for agent resumability.

    Enables agents to recover from failures mid-process by saving
    checkpoints to external storage.
    """
    task_id: str
    status: str = "pending"  # pending, running, completed, failed
    current_step: int = 0
    total_steps: Optional[int] = None
    context: dict = field(default_factory=dict)
    results: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert state to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "context": self.context,
            "results": self.results,
            "errors": self.errors,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AgentState":
        """Create state from dictionary."""
        return cls(**data)

    def save(self, path: Path) -> None:
        """Save state to file."""
        self.updated_at = datetime.now().isoformat()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> Optional["AgentState"]:
        """Load state from file, returns None if not found."""
        if not path.exists():
            return None
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))

    def add_result(self, result: Any) -> None:
        """Add a result and advance step."""
        self.results.append(result)
        self.current_step += 1
        self.updated_at = datetime.now().isoformat()

    def add_error(self, error: str) -> None:
        """Record an error."""
        self.errors.append({
            "step": self.current_step,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now().isoformat()


# =============================================================================
# Observability - Production Tracing
# =============================================================================

@dataclass
class TraceEvent:
    """A single event in the execution trace."""
    timestamp: str
    event_type: str  # tool_call, agent_spawn, completion, error
    agent_id: str
    data: dict
    duration_ms: Optional[float] = None


class ExecutionTracer:
    """
    Production tracing for agent execution.

    Tracks decision patterns and interaction structures without
    exposing sensitive conversation content.
    """

    def __init__(self, trace_dir: Optional[Path] = None):
        self.trace_dir = trace_dir
        self.events: list[TraceEvent] = []
        self._start_times: dict[str, float] = {}

    def start_operation(self, operation_id: str) -> None:
        """Start timing an operation."""
        self._start_times[operation_id] = time.time()

    def end_operation(self, operation_id: str) -> Optional[float]:
        """End timing and return duration in ms."""
        start = self._start_times.pop(operation_id, None)
        if start:
            return (time.time() - start) * 1000
        return None

    def record(
        self,
        event_type: str,
        agent_id: str,
        data: dict,
        operation_id: Optional[str] = None
    ) -> None:
        """Record a trace event."""
        duration = None
        if operation_id:
            duration = self.end_operation(operation_id)

        event = TraceEvent(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            agent_id=agent_id,
            data=data,
            duration_ms=duration
        )
        self.events.append(event)
        logger.debug(f"Trace: {event_type} | {agent_id} | {duration}ms")

    def save(self, filename: str) -> None:
        """Save trace to file."""
        if not self.trace_dir:
            return

        self.trace_dir.mkdir(parents=True, exist_ok=True)
        path = self.trace_dir / filename

        with open(path, 'w') as f:
            json.dump(
                [{"timestamp": e.timestamp, "event_type": e.event_type,
                  "agent_id": e.agent_id, "data": e.data, "duration_ms": e.duration_ms}
                 for e in self.events],
                f, indent=2
            )

    def get_summary(self) -> dict:
        """Get summary statistics from trace."""
        tool_calls = [e for e in self.events if e.event_type == "tool_call"]
        agent_spawns = [e for e in self.events if e.event_type == "agent_spawn"]
        errors = [e for e in self.events if e.event_type == "error"]

        durations = [e.duration_ms for e in self.events if e.duration_ms]

        return {
            "total_events": len(self.events),
            "tool_calls": len(tool_calls),
            "agents_spawned": len(agent_spawns),
            "errors": len(errors),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "total_duration_ms": sum(durations),
        }


# =============================================================================
# Effort Scaling
# =============================================================================

class ComplexityLevel(Enum):
    """Task complexity levels for effort scaling."""
    SIMPLE = "simple"        # 1 agent, 3-10 tool calls
    MODERATE = "moderate"    # 2-4 agents, 10-15 calls each
    COMPLEX = "complex"      # 5-10 agents with divided responsibilities


@dataclass
class EffortConfig:
    """
    Configuration for effort scaling based on task complexity.

    Following Anthropic's recommendations:
    - Simple fact-finding: 1 agent, 3-10 tool calls
    - Comparisons: 2-4 subagents, 10-15 calls each
    - Complex research: 10+ subagents with divided responsibilities
    """
    complexity: ComplexityLevel
    max_agents: int
    max_tool_calls_per_agent: int
    max_total_tokens: int

    @classmethod
    def for_complexity(cls, level: ComplexityLevel) -> "EffortConfig":
        """Get default configuration for complexity level."""
        configs = {
            ComplexityLevel.SIMPLE: cls(
                complexity=level,
                max_agents=1,
                max_tool_calls_per_agent=10,
                max_total_tokens=50_000,
            ),
            ComplexityLevel.MODERATE: cls(
                complexity=level,
                max_agents=4,
                max_tool_calls_per_agent=15,
                max_total_tokens=200_000,
            ),
            ComplexityLevel.COMPLEX: cls(
                complexity=level,
                max_agents=10,
                max_tool_calls_per_agent=25,
                max_total_tokens=500_000,
            ),
        }
        return configs[level]
