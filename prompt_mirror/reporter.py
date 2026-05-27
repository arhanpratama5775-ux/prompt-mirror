"""
Reporter for generating mirror reports.
Creates formatted output from analysis results.
"""

from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .analyzer import AnalysisResult, TopicCluster, TimePattern, PromptPattern


class MirrorReporter:
    """Generate formatted mirror reports."""

    def __init__(self, use_color: bool = True):
        self.console = Console(color_system="auto" if use_color else None)

    def generate_report(self, result: AnalysisResult) -> str:
        """Generate a complete mirror report."""
        lines = []

        # Header
        lines.append("")
        lines.append("=" * 50)
        lines.append("           YOUR MIRROR REPORT")
        lines.append("=" * 50)
        lines.append("")

        # Summary stats
        lines.append("OVERVIEW:")
        lines.append(f"  Total conversations: {result.total_conversations}")
        lines.append(f"  Total prompts by you: {result.total_user_prompts}")
        lines.append(f"  Total words: {result.total_words:,}")
        lines.append(f"  Average prompt length: {result.avg_prompt_length:.1f} words")

        # Date range
        if result.date_range[0] and result.date_range[1]:
            start = result.date_range[0].strftime("%b %Y")
            end = result.date_range[1].strftime("%b %Y")
            lines.append(f"  Date range: {start} - {end}")

        lines.append("")

        # Topics
        if result.topics:
            lines.append("YOUR TOP 5 TOPICS:")
            for i, topic in enumerate(result.topics[:5], 1):
                lines.append(f"  {i}. {topic.name} ({topic.percentage:.0f}%)")
            lines.append("")

        # Time patterns
        if result.time_patterns:
            lines.append("WHEN YOU ASK:")
            for tp in result.time_patterns[:3]:
                lines.append(f"  {tp.period}: {tp.count} prompts")
            lines.append("")

        # Question types
        if result.question_types:
            lines.append("QUESTION TYPES:")
            top_questions = sorted(result.question_types.items(),
                                    key=lambda x: x[1], reverse=True)[:5]
            for qtype, count in top_questions:
                if count > 0:
                    lines.append(f"  {qtype.title()}: {count} times")
            lines.append("")

        # Patterns
        if result.patterns:
            lines.append("PATTERNS DETECTED:")
            for pattern in result.patterns:
                lines.append(f"  - {pattern.description}")
            lines.append("")

        # Reflection questions
        if result.reflection_questions:
            lines.append("REFLECTION QUESTIONS:")
            for i, question in enumerate(result.reflection_questions, 1):
                lines.append(f"  {i}. {question}")
            lines.append("")

        lines.append("=" * 50)
        lines.append("")
        lines.append("Note: This is a mirror, not a judgment.")
        lines.append("Use these insights however you see fit.")
        lines.append("")

        return "\n".join(lines)

    def print_report(self, result: AnalysisResult):
        """Print formatted report to console with colors."""
        # Header
        self.console.print()
        header = Text("YOUR MIRROR REPORT", style="bold cyan", justify="center")
        self.console.print(Panel(header, style="cyan"))

        # Overview
        self.console.print("\n[bold]OVERVIEW:[/bold]")
        self.console.print(f"  Total conversations: [green]{result.total_conversations}[/green]")
        self.console.print(f"  Total prompts by you: [green]{result.total_user_prompts}[/green]")
        self.console.print(f"  Total words: [green]{result.total_words:,}[/green]")
        self.console.print(f"  Average prompt length: [green]{result.avg_prompt_length:.1f}[/green] words")

        if result.date_range[0] and result.date_range[1]:
            start = result.date_range[0].strftime("%b %Y")
            end = result.date_range[1].strftime("%b %Y")
            self.console.print(f"  Date range: [blue]{start} - {end}[/blue]")

        # Topics table
        if result.topics:
            self.console.print("\n[bold]YOUR TOP TOPICS:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=3)
            table.add_column("Topic")
            table.add_column("Prompts", justify="right")
            table.add_column("%", justify="right")

            for i, topic in enumerate(result.topics[:5], 1):
                table.add_row(
                    str(i),
                    topic.name,
                    str(topic.count),
                    f"{topic.percentage:.0f}%"
                )

            self.console.print(table)

        # Time patterns
        if result.time_patterns:
            self.console.print("\n[bold]WHEN YOU ASK:[/bold]")
            for tp in result.time_patterns[:3]:
                self.console.print(f"  {tp.period}: [yellow]{tp.count}[/yellow] prompts")

        # Question types
        if result.question_types:
            self.console.print("\n[bold]QUESTION TYPES:[/bold]")
            top_questions = sorted(result.question_types.items(),
                                    key=lambda x: x[1], reverse=True)[:5]
            for qtype, count in top_questions:
                if count > 0:
                    self.console.print(f"  {qtype.title()}: [yellow]{count}[/yellow] times")

        # Patterns
        if result.patterns:
            self.console.print("\n[bold yellow]PATTERNS DETECTED:[/bold yellow]")
            for pattern in result.patterns:
                self.console.print(f"  [yellow]-[/yellow] {pattern.description}")

        # Reflection questions
        if result.reflection_questions:
            self.console.print("\n[bold cyan]REFLECTION QUESTIONS:[/bold cyan]")
            for i, question in enumerate(result.reflection_questions, 1):
                self.console.print(f"  [cyan]{i}.[/cyan] {question}")

        # Footer
        self.console.print()
        footer = Text(
            "This is a mirror, not a judgment.\nUse these insights however you see fit.",
            style="dim italic",
            justify="center"
        )
        self.console.print(Panel(footer, style="dim"))

    def generate_json(self, result: AnalysisResult) -> dict:
        """Generate JSON representation of results."""
        return {
            "summary": {
                "total_conversations": result.total_conversations,
                "total_user_prompts": result.total_user_prompts,
                "total_words": result.total_words,
                "avg_prompt_length": result.avg_prompt_length,
                "date_range": {
                    "start": result.date_range[0].isoformat() if result.date_range[0] else None,
                    "end": result.date_range[1].isoformat() if result.date_range[1] else None
                }
            },
            "topics": [
                {
                    "name": t.name,
                    "count": t.count,
                    "percentage": t.percentage,
                    "keywords": t.keywords,
                    "sample_prompts": t.sample_prompts
                }
                for t in result.topics
            ],
            "time_patterns": [
                {
                    "period": tp.period,
                    "count": tp.count,
                    "avg_length": tp.avg_length
                }
                for tp in result.time_patterns
            ],
            "question_types": result.question_types,
            "patterns": [
                {
                    "type": p.pattern_type,
                    "description": p.description,
                    "evidence": p.evidence,
                    "reflection_question": p.reflection_question
                }
                for p in result.patterns
            ],
            "reflection_questions": result.reflection_questions
        }

    def generate_markdown(self, result: AnalysisResult) -> str:
        """Generate Markdown report."""
        lines = []

        lines.append("# Your Mirror Report")
        lines.append("")

        # Summary
        lines.append("## Overview")
        lines.append("")
        lines.append(f"- **Total conversations:** {result.total_conversations}")
        lines.append(f"- **Total prompts by you:** {result.total_user_prompts}")
        lines.append(f"- **Total words:** {result.total_words:,}")
        lines.append(f"- **Average prompt length:** {result.avg_prompt_length:.1f} words")

        if result.date_range[0] and result.date_range[1]:
            start = result.date_range[0].strftime("%B %Y")
            end = result.date_range[1].strftime("%B %Y")
            lines.append(f"- **Date range:** {start} - {end}")

        lines.append("")

        # Topics
        if result.topics:
            lines.append("## Your Top Topics")
            lines.append("")
            lines.append("| # | Topic | Prompts | % |")
            lines.append("|---|-------|---------|---|")
            for i, topic in enumerate(result.topics[:5], 1):
                lines.append(f"| {i} | {topic.name} | {topic.count} | {topic.percentage:.0f}% |")
            lines.append("")

        # Patterns
        if result.patterns:
            lines.append("## Patterns Detected")
            lines.append("")
            for pattern in result.patterns:
                lines.append(f"- **{pattern.pattern_type}:** {pattern.description}")
            lines.append("")

        # Reflection questions
        if result.reflection_questions:
            lines.append("## Reflection Questions")
            lines.append("")
            for i, question in enumerate(result.reflection_questions, 1):
                lines.append(f"{i}. {question}")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("*This is a mirror, not a judgment. Use these insights however you see fit.*")

        return "\n".join(lines)
