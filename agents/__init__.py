"""
Research Historian Agent System

A production-ready multi-agent system for historical research using Claude Agent SDK.
Follows Anthropic's recommended patterns and industry best practices.
"""

from .core import (
    RetryConfig,
    CircuitBreaker,
    AgentError,
    RetriableError,
    NonRetriableError,
)
from .historian import (
    ResearchHistorian,
    ResearchTask,
    ResearchType,
    quick_research,
    parallel_research,
)

__all__ = [
    "ResearchHistorian",
    "ResearchTask",
    "ResearchType",
    "quick_research",
    "parallel_research",
    "RetryConfig",
    "CircuitBreaker",
    "AgentError",
    "RetriableError",
    "NonRetriableError",
]
