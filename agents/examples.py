"""
Research Historian - Usage Examples

This file demonstrates various ways to use the Research Historian agent system.
"""

import asyncio
from pathlib import Path

from .historian import (
    ResearchHistorian,
    ResearchTask,
    ResearchType,
    quick_research,
    parallel_research,
)
from .core import ComplexityLevel


# =============================================================================
# Example 1: Quick Fact-Finding
# =============================================================================

async def example_fact_finding():
    """
    Simple fact-finding query.
    Uses a single agent to answer specific questions quickly.
    """
    result = await quick_research(
        topic="When was the Declaration of Independence signed?",
        research_type=ResearchType.FACT_FINDING,
    )
    print("Fact-finding result:")
    print(result)


# =============================================================================
# Example 2: Deep Research
# =============================================================================

async def example_deep_research():
    """
    Comprehensive research on a topic.
    Uses multiple agents for thorough analysis.
    """
    historian = ResearchHistorian(
        working_dir=".",
        output_dir="./research_output",
        trace_dir="./traces",  # Enable tracing for observability
    )

    task = ResearchTask(
        topic="The causes and consequences of the French Revolution",
        research_type=ResearchType.DEEP_RESEARCH,
        output_path="./research_output/french_revolution.md",
    )

    async for message in historian.research(task):
        if hasattr(message, "result"):
            print("Research complete!")
            print(message.result)

    # Print execution statistics
    summary = historian.get_trace_summary()
    print(f"\nExecution stats: {summary}")


# =============================================================================
# Example 3: Source Verification
# =============================================================================

async def example_verification():
    """
    Verify historical claims.
    Cross-references sources and provides confidence ratings.
    """
    historian = ResearchHistorian()

    task = ResearchTask(
        topic="Cleopatra lived closer in time to the Moon landing than to the construction of the Great Pyramid",
        research_type=ResearchType.SOURCE_VERIFICATION,
    )

    async for message in historian.research(task):
        if hasattr(message, "result"):
            print("Verification result:")
            print(message.result)


# =============================================================================
# Example 4: Timeline Building
# =============================================================================

async def example_timeline():
    """
    Build a chronological timeline.
    Identifies key dates and causal relationships.
    """
    result = await quick_research(
        topic="Key events of World War I from 1914 to 1918",
        research_type=ResearchType.TIMELINE_BUILDING,
    )
    print("Timeline:")
    print(result)


# =============================================================================
# Example 5: Parallel Research (Multiple Topics)
# =============================================================================

async def example_parallel():
    """
    Research multiple topics simultaneously.
    Efficient for batch research tasks.
    """
    topics = [
        "The fall of Constantinople 1453",
        "The Black Death in Europe",
        "The Mongol Empire expansion",
    ]

    results = await parallel_research(
        topics=topics,
        research_type=ResearchType.FACT_FINDING,
        max_concurrent=3,
    )

    for topic, result in results.items():
        print(f"\n=== {topic} ===")
        print(result)


# =============================================================================
# Example 6: Research with Local Sources
# =============================================================================

async def example_with_local_sources():
    """
    Combine web research with local document analysis.
    Useful when you have existing research materials.
    """
    historian = ResearchHistorian(
        working_dir=".",
        output_dir="./research_output",
    )

    task = ResearchTask(
        topic="Analysis of primary sources on the American Revolution",
        research_type=ResearchType.COMPREHENSIVE,
        local_sources="./sources",  # Directory with local documents
        context="Focus on letters and documents from founding fathers",
    )

    async for message in historian.research(task):
        if hasattr(message, "result"):
            print(message.result)


# =============================================================================
# Example 7: Resumable Research with State Persistence
# =============================================================================

async def example_resumable():
    """
    Research with state persistence for long-running tasks.
    Can be resumed if interrupted.
    """
    historian = ResearchHistorian(
        working_dir=".",
        output_dir="./research_output",
        state_dir="./state",  # Enable state persistence
    )

    task = ResearchTask(
        topic="Comprehensive history of the Roman Empire",
        research_type=ResearchType.COMPREHENSIVE,
        complexity=ComplexityLevel.COMPLEX,  # Force complex handling
    )

    # State is saved after each step
    # If interrupted, can check ./state/{task_id}.json
    async for message in historian.research(task):
        if hasattr(message, "result"):
            print(message.result)


# =============================================================================
# Example 8: Custom Research Pipeline
# =============================================================================

async def example_custom_pipeline():
    """
    Build a custom research pipeline with multiple steps.
    Demonstrates advanced usage patterns.
    """
    historian = ResearchHistorian(
        output_dir="./research_output",
        trace_dir="./traces",
    )

    # Step 1: Gather initial facts
    print("Step 1: Gathering facts...")
    facts_task = ResearchTask(
        topic="Key figures in the Scientific Revolution",
        research_type=ResearchType.FACT_FINDING,
    )

    facts = None
    async for msg in historian.research(facts_task):
        if hasattr(msg, "result"):
            facts = msg.result

    # Step 2: Build timeline based on facts
    print("\nStep 2: Building timeline...")
    timeline_task = ResearchTask(
        topic="Timeline of the Scientific Revolution (1500-1700)",
        research_type=ResearchType.TIMELINE_BUILDING,
        context=f"Include these figures: {facts[:500] if facts else ''}",
    )

    timeline = None
    async for msg in historian.research(timeline_task):
        if hasattr(msg, "result"):
            timeline = msg.result

    # Step 3: Deep dive on a specific aspect
    print("\nStep 3: Deep research...")
    deep_task = ResearchTask(
        topic="Isaac Newton's contributions to physics and mathematics",
        research_type=ResearchType.DEEP_RESEARCH,
        output_path="./research_output/newton_analysis.md",
    )

    async for msg in historian.research(deep_task):
        if hasattr(msg, "result"):
            print("Final report saved!")

    # Print overall execution stats
    print(f"\nTotal execution: {historian.get_trace_summary()}")


# =============================================================================
# Run Examples
# =============================================================================

async def run_all_examples():
    """Run all examples (for testing)."""
    print("\n" + "=" * 60)
    print("Example 1: Fact Finding")
    print("=" * 60)
    await example_fact_finding()

    # Add more as needed...


if __name__ == "__main__":
    # Run a specific example
    asyncio.run(example_fact_finding())
