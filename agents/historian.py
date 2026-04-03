"""
Research Historian - Main orchestrator agent.

Implements Anthropic's orchestrator-worker pattern:
- Lead agent (Sonnet) plans and delegates
- Specialized subagents (Haiku) execute in parallel
- Results synthesize through coordinator

Key features:
- Effort scaling based on task complexity
- Token budget management
- Parallel subagent execution
- State persistence for resumability
- Production tracing for observability
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, AsyncGenerator, Any

from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    HookMatcher,
    CLINotFoundError,
    ProcessError,
)

from .core import (
    RetryConfig,
    CircuitBreaker,
    AgentState,
    ExecutionTracer,
    ComplexityLevel,
    EffortConfig,
    with_retry,
    RetriableError,
    NonRetriableError,
)
from .subagents import (
    get_subagent_definition,
    get_subagents_for_task,
    get_all_subagent_definitions,
    SUBAGENT_REGISTRY,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Research Task Configuration
# =============================================================================

class ResearchType(Enum):
    """Types of research the historian can perform."""
    FACT_FINDING = "fact_finding"        # Quick answers to specific questions
    DEEP_RESEARCH = "deep_research"      # Comprehensive analysis and reports
    SOURCE_VERIFICATION = "verification" # Fact-checking and validation
    TIMELINE_BUILDING = "timeline"       # Chronological event mapping
    BIAS_ANALYSIS = "bias_analysis"      # Analyze sources for bias/perspective
    COMPARISON = "comparison"            # Compare multiple topics/events
    COUNTER_ANALYSIS = "counter"         # Challenge prevailing narratives
    COMPREHENSIVE = "comprehensive"      # All capabilities combined


@dataclass
class ResearchTask:
    """
    A research task to be executed.

    Attributes:
        topic: The subject to research
        research_type: Type of research to perform
        local_sources: Path to local documents to analyze (optional)
        output_path: Where to save results (optional)
        context: Additional context or constraints
        complexity: Override automatic complexity detection
    """
    topic: str
    research_type: ResearchType = ResearchType.FACT_FINDING
    local_sources: Optional[str] = None
    output_path: Optional[str] = None
    context: Optional[str] = None
    complexity: Optional[ComplexityLevel] = None

    # Generated fields
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# Complexity Detection
# =============================================================================

def detect_complexity(task: ResearchTask) -> ComplexityLevel:
    """
    Automatically detect task complexity for effort scaling.

    Simple heuristics based on:
    - Research type (fact-finding is simple, comprehensive is complex)
    - Topic length and specificity
    - Whether local sources are involved
    """
    if task.complexity:
        return task.complexity

    # Research type is primary indicator
    type_complexity = {
        ResearchType.FACT_FINDING: ComplexityLevel.SIMPLE,
        ResearchType.SOURCE_VERIFICATION: ComplexityLevel.MODERATE,
        ResearchType.TIMELINE_BUILDING: ComplexityLevel.MODERATE,
        ResearchType.BIAS_ANALYSIS: ComplexityLevel.MODERATE,
        ResearchType.COMPARISON: ComplexityLevel.MODERATE,
        ResearchType.COUNTER_ANALYSIS: ComplexityLevel.MODERATE,
        ResearchType.DEEP_RESEARCH: ComplexityLevel.COMPLEX,
        ResearchType.COMPREHENSIVE: ComplexityLevel.COMPLEX,
    }

    base = type_complexity[task.research_type]

    # Adjust based on other factors
    if task.local_sources and base == ComplexityLevel.SIMPLE:
        base = ComplexityLevel.MODERATE

    # Long topics suggest more complex research
    if len(task.topic.split()) > 20 and base != ComplexityLevel.COMPLEX:
        base = ComplexityLevel.MODERATE

    return base


# =============================================================================
# Research Historian Orchestrator
# =============================================================================

class ResearchHistorian:
    """
    Main research historian orchestrator.

    Coordinates specialized subagents for historical research tasks.
    Implements Anthropic's orchestrator-worker pattern with:
    - Dynamic task delegation with clear boundaries
    - Parallel subagent execution for efficiency
    - Effort scaling based on complexity
    - Production-grade error handling and tracing
    """

    def __init__(
        self,
        working_dir: str = ".",
        output_dir: str = "./research_output",
        state_dir: Optional[str] = None,
        trace_dir: Optional[str] = None,
        model: str = "opus",  # Orchestrator uses Opus for complex planning (per Anthropic's pattern)
    ):
        """
        Initialize the Research Historian.

        Args:
            working_dir: Base directory for file operations
            output_dir: Directory for research output
            state_dir: Directory for state persistence (enables resumability)
            trace_dir: Directory for execution traces (enables observability)
            model: Model for orchestrator (default: sonnet)
        """
        self.working_dir = Path(working_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.state_dir = Path(state_dir).resolve() if state_dir else None
        self.model = model

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.state_dir:
            self.state_dir.mkdir(parents=True, exist_ok=True)

        # Observability
        self.tracer = ExecutionTracer(
            trace_dir=Path(trace_dir) if trace_dir else None
        )

        # Fault tolerance
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
        )
        self.retry_config = RetryConfig(
            max_retries=3,
            base_delay=2.0,
            max_delay=30.0,
        )

    def _build_orchestrator_prompt(
        self,
        task: ResearchTask,
        effort: EffortConfig,
    ) -> str:
        """Build the orchestrator's system prompt."""

        agent_descriptions = "\n".join(
            f"- **{name}**: {config.description}"
            for name, config in SUBAGENT_REGISTRY.items()
        )

        return f"""You are a master research historian orchestrating specialized research agents.

## Available Agents
{agent_descriptions}

## Your Role
You coordinate research by:
1. Analyzing the research request
2. Breaking it into appropriate subtasks
3. Delegating to specialized agents using the Task tool
4. Synthesizing results into coherent output

## Effort Guidelines (Complexity: {effort.complexity.value})
- Maximum agents to use: {effort.max_agents}
- Maximum tool calls per agent: {effort.max_tool_calls_per_agent}
- Token budget: {effort.max_total_tokens:,}

## Task Delegation Best Practices
When spawning agents, provide:
1. **Clear objective**: What specific question or task
2. **Output format**: How results should be structured
3. **Scope boundaries**: What NOT to do
4. **Tool guidance**: Which tools are most relevant

Example delegation:
```
Use the fact-finder agent to:
- Find the exact date of [event]
- Verify against at least 2 sources
- Return: date, sources, confidence level
- Do NOT expand into related events
```

## Parallel Execution
When tasks are independent, spawn multiple agents simultaneously:
- Run fact-finder for dates WHILE deep-researcher gathers context
- Run source-verifier AFTER facts are gathered (depends on results)

## Output Directory
Save all outputs to: {self.output_dir}

## Current Task
Topic: {task.topic}
Type: {task.research_type.value}
Local Sources: {task.local_sources or 'None'}
Additional Context: {task.context or 'None'}
"""

    def _get_subagents_for_task(self, task: ResearchTask) -> dict:
        """Select appropriate subagents based on research type."""

        type_to_agents = {
            ResearchType.FACT_FINDING: {
                "fact-finder": get_subagent_definition("fact-finder"),
            },
            ResearchType.DEEP_RESEARCH: {
                "fact-finder": get_subagent_definition("fact-finder"),
                "deep-researcher": get_subagent_definition("deep-researcher"),
                "critic": get_subagent_definition("critic"),
            },
            ResearchType.SOURCE_VERIFICATION: {
                "fact-finder": get_subagent_definition("fact-finder"),
                "source-verifier": get_subagent_definition("source-verifier"),
            },
            ResearchType.TIMELINE_BUILDING: {
                "fact-finder": get_subagent_definition("fact-finder"),
                "timeline-builder": get_subagent_definition("timeline-builder"),
            },
            ResearchType.BIAS_ANALYSIS: {
                "fact-finder": get_subagent_definition("fact-finder"),
                "bias-detector": get_subagent_definition("bias-detector"),
            },
            ResearchType.COMPARISON: {
                "fact-finder": get_subagent_definition("fact-finder"),
                "comparator": get_subagent_definition("comparator"),
                "synthesizer": get_subagent_definition("synthesizer"),
            },
            ResearchType.COUNTER_ANALYSIS: {
                "fact-finder": get_subagent_definition("fact-finder"),
                "devils-advocate": get_subagent_definition("devils-advocate"),
                "source-verifier": get_subagent_definition("source-verifier"),
            },
            ResearchType.COMPREHENSIVE: get_all_subagent_definitions(),
        }

        agents = type_to_agents[task.research_type].copy()

        # Add local analyst if local sources specified
        if task.local_sources:
            agents["local-analyst"] = get_subagent_definition("local-analyst")

        # Add critic for quality validation on complex research
        if task.research_type in (ResearchType.DEEP_RESEARCH, ResearchType.COMPREHENSIVE):
            agents["critic"] = get_subagent_definition("critic")

        # Add synthesizer for multi-source research
        if task.research_type == ResearchType.COMPREHENSIVE:
            agents["synthesizer"] = get_subagent_definition("synthesizer")

        return agents

    async def _audit_hook(
        self,
        input_data: dict,
        tool_use_id: str,
        context: dict
    ) -> dict:
        """Hook for auditing tool usage."""
        tool_name = input_data.get("tool_name", "unknown")

        self.tracer.record(
            event_type="tool_call",
            agent_id="orchestrator",
            data={"tool": tool_name, "tool_use_id": tool_use_id},
        )

        return {}

    async def research(
        self,
        task: ResearchTask,
    ) -> AsyncGenerator[Any, None]:
        """
        Execute a research task.

        Args:
            task: The research task to execute

        Yields:
            Messages from the research process
        """
        # Determine effort based on complexity
        complexity = detect_complexity(task)
        effort = EffortConfig.for_complexity(complexity)

        logger.info(
            f"Starting research: {task.topic} "
            f"(type={task.research_type.value}, complexity={complexity.value})"
        )

        # Initialize state for resumability
        state = None
        if self.state_dir:
            state_path = self.state_dir / f"{task.task_id}.json"
            state = AgentState.load(state_path) or AgentState(task_id=task.task_id)
            state.status = "running"
            state.context["topic"] = task.topic
            state.context["research_type"] = task.research_type.value
            state.save(state_path)

        # Start tracing
        self.tracer.start_operation(task.task_id)

        # Build agent options
        options = ClaudeAgentOptions(
            allowed_tools=["Read", "Write", "WebSearch", "WebFetch", "Glob", "Grep", "Task"],
            cwd=str(self.working_dir),
            model=self.model,
            permission_mode="acceptEdits",
            system_prompt=self._build_orchestrator_prompt(task, effort),
            agents=self._get_subagents_for_task(task),
            hooks={
                "PostToolUse": [HookMatcher(hooks=[self._audit_hook])]
            },
        )

        # Build the research prompt
        prompt = self._build_task_prompt(task, effort)

        try:
            async for message in query(prompt=prompt, options=options):
                # Record message in trace
                if hasattr(message, "type"):
                    self.tracer.record(
                        event_type=message.type,
                        agent_id="orchestrator",
                        data={"content_preview": str(message)[:200]},
                    )

                # Update state with results
                if state and hasattr(message, "result"):
                    state.add_result(str(message.result)[:1000])
                    state.save(self.state_dir / f"{task.task_id}.json")

                yield message

            # Mark success
            if state:
                state.status = "completed"
                state.save(self.state_dir / f"{task.task_id}.json")

            self.tracer.record(
                event_type="completion",
                agent_id="orchestrator",
                data={"status": "success"},
                operation_id=task.task_id,
            )

        except Exception as e:
            logger.error(f"Research failed: {e}")

            if state:
                state.status = "failed"
                state.add_error(str(e))
                state.save(self.state_dir / f"{task.task_id}.json")

            self.tracer.record(
                event_type="error",
                agent_id="orchestrator",
                data={"error": str(e)},
                operation_id=task.task_id,
            )

            raise

        finally:
            # Save trace
            if self.tracer.trace_dir:
                self.tracer.save(f"trace_{task.task_id}.json")

    def _build_task_prompt(self, task: ResearchTask, effort: EffortConfig) -> str:
        """Build the prompt for the research task."""

        type_instructions = {
            ResearchType.FACT_FINDING: """
Find and verify specific facts about this topic.
Use the fact-finder agent to locate precise information.
Return concise answers with sources and confidence levels.
""",
            ResearchType.DEEP_RESEARCH: """
Conduct comprehensive research on this topic.
1. Use fact-finder for initial information gathering
2. Use deep-researcher for thorough analysis
3. Use critic to review the research quality
4. Produce a detailed report with:
   - Historical context
   - Key events and figures
   - Different interpretations
   - Full bibliography
""",
            ResearchType.SOURCE_VERIFICATION: """
Verify claims and cross-reference sources related to this topic.
1. Use fact-finder to identify key claims
2. Use source-verifier to validate each claim
3. Report verdict for each claim:
   - VERIFIED / LIKELY TRUE / DISPUTED / UNVERIFIED / FALSE
   - Confidence level
   - Supporting and contradicting evidence
""",
            ResearchType.TIMELINE_BUILDING: """
Build a detailed chronological timeline for this topic.
1. Use fact-finder to identify key events and dates
2. Use timeline-builder to construct the timeline
3. Include:
   - Precise dates (with uncertainty noted)
   - Cause-and-effect relationships
   - Parallel developments
   - Major turning points
""",
            ResearchType.BIAS_ANALYSIS: """
Analyze the sources and narratives around this topic for bias and perspective.
1. Use fact-finder to gather information and identify key sources
2. Use bias-detector to analyze each major source for:
   - Political, nationalist, religious, and cultural biases
   - Framing choices and language
   - Missing perspectives
   - Reliability assessment
3. Synthesize into a balanced analysis of how this topic is presented
""",
            ResearchType.COMPARISON: """
Create a structured comparison of the subjects in this topic.
1. Use fact-finder to research each subject equally
2. Use comparator to create a structured comparative analysis:
   - Overview table of key attributes
   - Key similarities and differences
   - Causal connections
   - Historiographical comparison
3. Use synthesizer to merge findings into a coherent comparison document
""",
            ResearchType.COUNTER_ANALYSIS: """
Challenge the prevailing narrative or assumptions about this topic.
1. Use fact-finder to establish the mainstream view
2. Use devils-advocate to:
   - Identify challenges to the prevailing view
   - Find alternative interpretations
   - Surface overlooked evidence
   - Ask questions the mainstream doesn't address
3. Use source-verifier to validate counter-arguments
4. Produce a balanced assessment of prevailing vs. alternative views
""",
            ResearchType.COMPREHENSIVE: """
Conduct comprehensive historical research including:
1. Fact-finding for key information
2. Deep analysis for context and interpretation
3. Source verification for accuracy
4. Timeline construction for chronology
5. Bias analysis for balanced perspective
6. Counter-analysis to stress-test conclusions

Use multiple agents in parallel where tasks are independent.
Use synthesizer to merge all findings into a cohesive document.
Use critic for final quality review before output.
""",
        }

        prompt_parts = [
            f"## Research Request\n\n**Topic**: {task.topic}",
            type_instructions[task.research_type],
        ]

        if task.local_sources:
            prompt_parts.append(
                f"\n## Local Sources\nAnalyze documents in: {task.local_sources}\n"
                "Use local-analyst to index and extract information from local files."
            )

        if task.context:
            prompt_parts.append(f"\n## Additional Context\n{task.context}")

        if task.output_path:
            prompt_parts.append(f"\n## Output\nSave final results to: {task.output_path}")

        prompt_parts.append(
            f"\n## Constraints\n"
            f"- Complexity level: {effort.complexity.value}\n"
            f"- Max agents: {effort.max_agents}\n"
            f"- Max tool calls per agent: {effort.max_tool_calls_per_agent}"
        )

        return "\n".join(prompt_parts)

    async def research_batch(
        self,
        tasks: list[ResearchTask],
        max_concurrent: int = 3,
    ) -> list[Any]:
        """
        Execute multiple research tasks concurrently.

        Args:
            tasks: List of research tasks
            max_concurrent: Maximum concurrent tasks

        Returns:
            List of results (or exceptions) for each task
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_one(task: ResearchTask) -> Any:
            async with semaphore:
                result = None
                async for message in self.research(task):
                    if hasattr(message, "result"):
                        result = message.result
                return result

        return await asyncio.gather(
            *[run_one(task) for task in tasks],
            return_exceptions=True,
        )

    def get_trace_summary(self) -> dict:
        """Get summary of execution traces."""
        return self.tracer.get_summary()


# =============================================================================
# Convenience Functions
# =============================================================================

async def quick_research(
    topic: str,
    research_type: ResearchType = ResearchType.FACT_FINDING,
    working_dir: str = ".",
    output_dir: str = "./research_output",
) -> Optional[str]:
    """
    Quick convenience function for single research queries.

    Args:
        topic: Topic to research
        research_type: Type of research
        working_dir: Working directory
        output_dir: Output directory

    Returns:
        Research result as string, or None
    """
    historian = ResearchHistorian(
        working_dir=working_dir,
        output_dir=output_dir,
    )

    task = ResearchTask(topic=topic, research_type=research_type)

    result = None
    async for message in historian.research(task):
        if hasattr(message, "result"):
            result = message.result

    return result


async def parallel_research(
    topics: list[str],
    research_type: ResearchType = ResearchType.FACT_FINDING,
    max_concurrent: int = 5,
    working_dir: str = ".",
    output_dir: str = "./research_output",
) -> dict[str, Any]:
    """
    Research multiple topics in parallel.

    Args:
        topics: List of topics to research
        research_type: Type of research for all topics
        max_concurrent: Maximum concurrent research tasks
        working_dir: Working directory
        output_dir: Output directory

    Returns:
        Dictionary mapping topics to results
    """
    historian = ResearchHistorian(
        working_dir=working_dir,
        output_dir=output_dir,
    )

    tasks = [
        ResearchTask(topic=topic, research_type=research_type)
        for topic in topics
    ]

    results = await historian.research_batch(tasks, max_concurrent=max_concurrent)

    return dict(zip(topics, results))
