#!/usr/bin/env python3
"""
Research Historian CLI

Command-line interface for running historical research agents.

Usage:
    python -m agents.cli "What caused the fall of Rome?"
    python -m agents.cli --type deep "The French Revolution"
    python -m agents.cli --parallel "Topic 1" "Topic 2" "Topic 3"
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from .historian import (
    ResearchHistorian,
    ResearchTask,
    ResearchType,
    quick_research,
    parallel_research,
)


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Research Historian - AI-powered historical research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick fact-finding
  python -m agents.cli "When did World War II end?"

  # Deep research
  python -m agents.cli --type deep "The Industrial Revolution"

  # Source verification
  python -m agents.cli --type verify "Napoleon was 5 feet tall"

  # Build a timeline
  python -m agents.cli --type timeline "The American Civil War"

  # Bias analysis
  python -m agents.cli --type bias "Media coverage of the Vietnam War"

  # Compare topics
  python -m agents.cli --type compare "French Revolution vs American Revolution"

  # Challenge prevailing narrative
  python -m agents.cli --type counter "Columbus discovered America"

  # Comprehensive research
  python -m agents.cli --type comprehensive "The Renaissance"

  # Research multiple topics in parallel
  python -m agents.cli --parallel "Topic 1" "Topic 2" "Topic 3"

  # Include local sources
  python -m agents.cli --local ./sources "The Cold War"

  # Save output to file
  python -m agents.cli --output ./report.md "The Roman Empire"
""",
    )

    parser.add_argument(
        "topics",
        nargs="+",
        help="Topic(s) to research",
    )

    parser.add_argument(
        "-t", "--type",
        choices=["fact", "deep", "verify", "timeline", "bias", "compare", "counter", "comprehensive"],
        default="fact",
        help="Type of research: fact, deep, verify, timeline, bias, compare, counter, comprehensive (default: fact)",
    )

    parser.add_argument(
        "-p", "--parallel",
        action="store_true",
        help="Research all topics in parallel",
    )

    parser.add_argument(
        "-c", "--concurrent",
        type=int,
        default=3,
        help="Max concurrent tasks when using --parallel (default: 3)",
    )

    parser.add_argument(
        "-l", "--local",
        type=str,
        help="Path to local source documents",
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Save output to file",
    )

    parser.add_argument(
        "-d", "--output-dir",
        type=str,
        default="./research_output",
        help="Directory for research outputs (default: ./research_output)",
    )

    parser.add_argument(
        "--state-dir",
        type=str,
        help="Directory for state persistence (enables resume)",
    )

    parser.add_argument(
        "--trace-dir",
        type=str,
        help="Directory for execution traces",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


def get_research_type(type_str: str) -> ResearchType:
    """Convert CLI type string to ResearchType enum."""
    mapping = {
        "fact": ResearchType.FACT_FINDING,
        "deep": ResearchType.DEEP_RESEARCH,
        "verify": ResearchType.SOURCE_VERIFICATION,
        "timeline": ResearchType.TIMELINE_BUILDING,
        "bias": ResearchType.BIAS_ANALYSIS,
        "compare": ResearchType.COMPARISON,
        "counter": ResearchType.COUNTER_ANALYSIS,
        "comprehensive": ResearchType.COMPREHENSIVE,
    }
    return mapping[type_str]


async def run_single_research(args) -> None:
    """Run research on a single topic."""
    topic = " ".join(args.topics)
    research_type = get_research_type(args.type)

    print(f"\n🔍 Researching: {topic}")
    print(f"   Type: {research_type.value}")
    if args.local:
        print(f"   Local sources: {args.local}")
    print()

    historian = ResearchHistorian(
        working_dir=".",
        output_dir=args.output_dir,
        state_dir=args.state_dir,
        trace_dir=args.trace_dir,
    )

    task = ResearchTask(
        topic=topic,
        research_type=research_type,
        local_sources=args.local,
        output_path=args.output,
    )

    result = None
    try:
        async for message in historian.research(task):
            # Print progress indicators
            if hasattr(message, "type"):
                if message.type == "tool_use":
                    print(".", end="", flush=True)

            if hasattr(message, "result"):
                result = message.result

        print("\n")

        if result:
            print("=" * 60)
            print("RESEARCH RESULTS")
            print("=" * 60)
            print(result)

            if args.output:
                Path(args.output).write_text(result)
                print(f"\n✅ Saved to: {args.output}")

        # Print trace summary if tracing enabled
        if args.trace_dir:
            summary = historian.get_trace_summary()
            print(f"\n📊 Trace: {summary['tool_calls']} tool calls, "
                  f"{summary['agents_spawned']} agents, "
                  f"{summary['total_duration_ms']:.0f}ms total")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


async def run_parallel_research(args) -> None:
    """Run research on multiple topics in parallel."""
    topics = args.topics
    research_type = get_research_type(args.type)

    print(f"\n🔍 Researching {len(topics)} topics in parallel")
    print(f"   Type: {research_type.value}")
    print(f"   Max concurrent: {args.concurrent}")
    print(f"   Topics: {', '.join(topics)}")
    print()

    try:
        results = await parallel_research(
            topics=topics,
            research_type=research_type,
            max_concurrent=args.concurrent,
            output_dir=args.output_dir,
        )

        print("\n" + "=" * 60)
        print("RESEARCH RESULTS")
        print("=" * 60)

        for topic, result in results.items():
            print(f"\n### {topic}")
            print("-" * 40)
            if isinstance(result, Exception):
                print(f"❌ Error: {result}")
            else:
                print(result or "(no result)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    args = parse_args()
    setup_logging(args.verbose)

    if args.parallel:
        asyncio.run(run_parallel_research(args))
    else:
        asyncio.run(run_single_research(args))


if __name__ == "__main__":
    main()
