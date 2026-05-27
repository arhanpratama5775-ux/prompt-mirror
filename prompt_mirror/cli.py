#!/usr/bin/env python3
"""
Prompt Mirror CLI - Reflect your AI conversation patterns back to you.
"""

import os
import sys
import json
import calendar
import click
from pathlib import Path

from .parser import ConversationParser, get_warnings
from .analyzer import PromptAnalyzer
from .reporter import MirrorReporter
from .trend_analyzer import TrendAnalyzer, format_trend_report


# Maximum file size to process (500MB)
MAX_FILE_SIZE = 500 * 1024 * 1024


def validate_file_path(file_path: str) -> Path:
    """
    Validate file path for security - prevent path traversal attacks.

    Args:
        file_path: Path to validate

    Returns:
        Resolved absolute Path object

    Raises:
        ValueError: If path is invalid or potentially dangerous
    """
    path = Path(file_path)

    # Resolve to absolute path (handles .., symlinks, etc.)
    try:
        resolved = path.resolve()
    except Exception as e:
        raise ValueError(f"Invalid path: {file_path}") from e

    # Check if file exists
    if not resolved.exists():
        raise ValueError(f"File not found: {file_path}")

    # Ensure it's a file, not a directory (for analyze command)
    if resolved.is_file():
        # path.resolve() already handles path traversal safely (e.g., '../' -> absolute path)
        # No need to check for '..' in original string - that would reject valid relative paths

        # Check file size for safety
        try:
            file_size = resolved.stat().st_size
            if file_size > MAX_FILE_SIZE:
                raise ValueError(
                    f"File too large: {file_size / (1024*1024):.1f}MB. "
                    f"Maximum supported: {MAX_FILE_SIZE / (1024*1024):.0f}MB. "
                    "Consider splitting your conversations file."
                )
        except OSError:
            pass  # Can't check size, continue

    return resolved


def validate_output_path(output_path: str) -> Path:
    """
    Validate output file path for security.

    Args:
        output_path: Output path to validate

    Returns:
        Resolved Path object

    Raises:
        ValueError: If path is invalid or potentially dangerous
    """
    if not output_path:
        return None

    path = Path(output_path)

    # Check for dangerous characters that could be used in filename attacks
    filename = path.name
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\x00']
    for char in dangerous_chars:
        if char in filename:
            raise ValueError(
                f"Invalid character in filename: '{char}'. "
                "Please use a different output filename."
            )

    # Resolve parent directory and create if needed
    try:
        parent = path.parent.resolve()
        if not parent.exists():
            # BUGFIX: Actually create the directory (was only a comment before)
            parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise ValueError(f"Invalid output path: {output_path}") from e

    return path


def validate_timezone(timezone: str):
    """
    Validate timezone string before parsing.

    Args:
        timezone: Timezone string to validate (e.g., 'Asia/Jakarta')

    Raises:
        SystemExit: If timezone is invalid
    """
    if not timezone:
        return
    try:
        import zoneinfo
        zoneinfo.ZoneInfo(timezone)
    except ImportError:
        # Python 3.8 - zoneinfo not available, will warn in parser
        pass
    except Exception as e:
        click.echo(f"Error: Invalid timezone '{timezone}'", err=True)
        click.echo(f"  {e}", err=True)
        click.echo("\nCommon timezones: UTC, Asia/Jakarta, America/New_York, Europe/London", err=True)
        sys.exit(1)


@click.group()
@click.version_option(version="0.3.0")
def cli():
    """
    Prompt Mirror - See patterns in your AI conversations.

    Analyze your exported ChatGPT, Claude, or Gemini conversations
    and get insights about what you ask and how you use AI.

    \b
    Quick Start:
      1. Export your conversations from ChatGPT/Claude/Gemini
      2. Run: prompt-mirror analyze conversations.json
      3. Read your mirror report

    \b
    Commands:
      analyze     Analyze conversations and generate report
      visualize   Generate charts from analysis
      stats       Show basic statistics
      topics      List topic categories
      guide       Show how to export conversations
    """
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--format", "-f",
    type=click.Choice(["text", "json", "markdown", "pdf"]),
    default="text",
    help="Output format (text, json, markdown, pdf)"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=None,
    help="Output file path (default: stdout)"
)
@click.option(
    "--no-color",
    is_flag=True,
    help="Disable colored output"
)
@click.option(
    "--timezone", "-tz",
    default=None,
    help="Your timezone for accurate time analysis (e.g., 'Asia/Jakarta', 'America/New_York')"
)
def analyze(file_path: str, format: str, output: str, no_color: bool, timezone: str):
    """
    Analyze your AI conversation export.

    FILE_PATH: Path to your exported conversations JSON file or directory.

    \b
    Examples:
      prompt-mirror analyze conversations.json
      prompt-mirror analyze conversations.json --timezone "Asia/Jakarta"
      prompt-mirror analyze conversations.json --format json --output report.json
      prompt-mirror analyze conversations.json --format pdf --output report.pdf
    """
    try:
        # Validate file path for security
        validated_path = validate_file_path(file_path)

        # Validate output path if provided
        validated_output = validate_output_path(output)

        # Validate timezone before parsing
        validate_timezone(timezone)

        # Parse
        click.echo(f"Loading conversations from {validated_path}...")
        parser = ConversationParser()
        conversations = parser.parse(str(validated_path), local_timezone=timezone)

        if not conversations:
            click.echo("No conversations found in the file.", err=True)
            sys.exit(1)

        # Show warnings if any
        warnings = get_warnings()
        if warnings:
            click.echo("\nWarnings:", err=True)
            for warning in warnings:
                click.echo(f"  - {warning}", err=True)
            click.echo()

        click.echo(f"Found {len(conversations)} conversations.")

        # Analyze
        click.echo("Analyzing patterns...")
        analyzer = PromptAnalyzer()
        result = analyzer.analyze(conversations)

        # Report
        if format == "pdf":
            try:
                from .pdf_reporter import PDFReporter
                pdf_reporter = PDFReporter()
                
                pdf_output = validated_output or Path("mirror-report.pdf")
                
                pdf_reporter.generate(result, str(pdf_output))
                click.echo(f"PDF report saved to {pdf_output}")
                return
            except ImportError:
                click.echo("Error: reportlab is required for PDF export.", err=True)
                click.echo("Install it with: pip install reportlab", err=True)
                sys.exit(1)

        reporter = MirrorReporter(use_color=not no_color)

        if format == "json":
            output_data = json.dumps(reporter.generate_json(result), indent=2)
        elif format == "markdown":
            output_data = reporter.generate_markdown(result)
        else:
            output_data = reporter.generate_report(result)

        # Output
        if validated_output:
            validated_output.write_text(output_data, encoding="utf-8")
            click.echo(f"Report saved to {validated_output}")
        else:
            if format == "text" and not no_color:
                reporter.print_report(result)
            else:
                click.echo(output_data)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except FileNotFoundError:
        click.echo(f"Error: File not found: {file_path}", err=True)
        sys.exit(1)
    except json.JSONDecodeError:
        click.echo(f"Error: Invalid JSON file: {file_path}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="charts",
    help="Output directory for charts (default: charts/)"
)
@click.option(
    "--timezone", "-tz",
    default=None,
    help="Your timezone for accurate time analysis"
)
@click.option(
    "--summary",
    is_flag=True,
    help="Generate a single summary image instead of separate charts"
)
def visualize(file_path: str, output: str, timezone: str, summary: bool):
    """
    Generate visualizations from your conversations.

    Creates charts for topic distribution, time patterns, and question types.

    \b
    Examples:
      prompt-mirror visualize conversations.json
      prompt-mirror visualize conversations.json --output my-charts/
      prompt-mirror visualize conversations.json --summary
    """
    try:
        from .visualizer import MirrorVisualizer
    except ImportError:
        click.echo("Error: matplotlib is required for visualization.", err=True)
        click.echo("Install it with: pip install matplotlib", err=True)
        sys.exit(1)

    try:
        # Validate file path for security
        validated_path = validate_file_path(file_path)

        # Validate timezone before parsing
        validate_timezone(timezone)

        click.echo(f"Loading conversations from {validated_path}...")

        # Parse
        parser = ConversationParser()
        conversations = parser.parse(str(validated_path), local_timezone=timezone)

        if not conversations:
            click.echo("No conversations found.", err=True)
            sys.exit(1)

        click.echo(f"Found {len(conversations)} conversations.")

        # Analyze
        click.echo("Analyzing patterns...")
        analyzer = PromptAnalyzer()
        result = analyzer.analyze(conversations)

        # Visualize
        click.echo("Generating charts...")
        visualizer = MirrorVisualizer()

        if summary:
            # BUGFIX: --summary with default output="charts" would create "charts.png"
            # instead of a proper file. Now handles directory vs filename correctly.
            if output == 'charts' or os.path.isdir(output):
                # Default output is a directory name, create a filename inside it
                os.makedirs(output, exist_ok=True)
                output_path = os.path.join(output, 'summary.png')
            else:
                output_path = output if output.endswith('.png') else f"{output}.png"
            visualizer.generate_summary_image(result, output_path)
            click.echo(f"Summary chart saved to {output_path}")
        else:
            generated = visualizer.generate_all(result, output)
            click.echo(f"\nGenerated {len(generated)} charts:")
            for path in generated:
                click.echo(f"  - {path}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def topics():
    """Show available topic categories used for analysis."""
    from .analyzer import PromptAnalyzer

    analyzer = PromptAnalyzer()

    click.echo("Topic categories used for analysis:\n")

    for topic, keywords in analyzer.TOPIC_KEYWORDS.items():
        click.echo(f"  {topic}:")
        click.echo(f"    Keywords: {', '.join(keywords[:10])}...")
        click.echo()


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--timezone", "-tz",
    default=None,
    help="Your timezone (e.g., 'Asia/Jakarta')"
)
def stats(file_path: str, timezone: str):
    """Show basic statistics about your conversations."""
    try:
        # Validate file path for security
        validated_path = validate_file_path(file_path)

        # Validate timezone before parsing
        validate_timezone(timezone)

        parser = ConversationParser()
        conversations = parser.parse(str(validated_path), local_timezone=timezone)

        if not conversations:
            click.echo("No conversations found.")
            return

        # Show warnings if any
        warnings = get_warnings()
        if warnings:
            click.echo("\nWarnings:", err=True)
            for warning in warnings:
                click.echo(f"  - {warning}", err=True)

        total_messages = sum(len(c.messages) for c in conversations)
        user_messages = sum(
            1 for c in conversations for m in c.messages if m.role == "user"
        )
        assistant_messages = total_messages - user_messages

        click.echo("\nConversation Statistics:")
        click.echo(f"  Total conversations: {len(conversations)}")
        click.echo(f"  Total messages: {total_messages}")
        click.echo(f"  Your messages: {user_messages}")
        click.echo(f"  AI responses: {assistant_messages}")

        # Source breakdown
        sources = {}
        for c in conversations:
            sources[c.source] = sources.get(c.source, 0) + 1

        if len(sources) > 1:
            click.echo("\nBy source:")
            for source, count in sources.items():
                click.echo(f"  {source}: {count}")

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def guide():
    """Show how to export your conversations from various AI platforms."""
    guide_text = """
How to Export Your AI Conversations
====================================

ChatGPT (OpenAI):
  1. Go to Settings (click your profile picture)
  2. Click "Data Controls"
  3. Click "Export data"
  4. You'll receive an email with a download link
  5. Extract the ZIP file and use conversations.json

Claude (Anthropic):
  1. Go to Settings
  2. Look for "Export data" or "Download your data"
  3. Download and extract the file

Gemini (Google):
  1. Go to Gemini Settings
  2. Click "Export your data" or use Google Takeout
  3. Select "Gemini" conversations
  4. Download the export

After exporting:
  Run: prompt-mirror analyze /path/to/conversations.json

Privacy Note:
  All analysis happens locally on your machine.
  Your data never leaves your computer.
"""
    click.echo(guide_text)


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option(
    "--format", "-f",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format (text or json)"
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=None,
    help="Output file path (default: stdout)"
)
@click.option(
    "--timezone", "-tz",
    default=None,
    help="Your timezone for accurate time analysis (e.g., 'Asia/Jakarta')"
)
@click.option(
    "--charts",
    is_flag=True,
    help="Also generate trend visualization charts"
)
def trend(file_path: str, format: str, output: str, timezone: str, charts: bool):
    """
    Analyze trends in your AI usage over time.

    Shows how your topics, question types, and behaviors have changed
    across months. Helps you understand if you're becoming more reliant
    on AI or more self-sufficient.

    \b
    Examples:
      prompt-mirror trend conversations.json
      prompt-mirror trend conversations.json --timezone "Asia/Jakarta"
      prompt-mirror trend conversations.json --format json --output trends.json
    """
    try:
        # Validate file path for security
        validated_path = validate_file_path(file_path)

        # Validate output path if provided
        validated_output = validate_output_path(output)

        # Validate timezone before parsing
        validate_timezone(timezone)

        click.echo(f"Loading conversations from {validated_path}...")

        # Parse
        parser = ConversationParser()
        conversations = parser.parse(str(validated_path), local_timezone=timezone)

        if not conversations:
            click.echo("No conversations found.", err=True)
            sys.exit(1)

        click.echo(f"Found {len(conversations)} conversations.")

        # Check for timestamps
        has_timestamps = any(
            msg.timestamp 
            for conv in conversations 
            for msg in conv.messages
        )
        if not has_timestamps:
            click.echo("Warning: No timestamps found in conversations.", err=True)
            click.echo("Trend analysis requires timestamps to work properly.", err=True)
            sys.exit(1)

        # Analyze trends
        click.echo("Analyzing trends over time...")
        trend_analyzer = TrendAnalyzer()
        result = trend_analyzer.analyze_trends(conversations)

        # BUGFIX: Generate trend charts if --charts flag is provided
        # Previously, generate_trend_charts() in visualizer.py was dead code
        # (never called from CLI). Now accessible via --charts flag.
        if charts:
            try:
                from .visualizer import MirrorVisualizer
                visualizer = MirrorVisualizer()
                chart_dir = "trend_charts"
                generated = visualizer.generate_trend_charts(result, chart_dir)
                if generated:
                    click.echo(f"Generated {len(generated)} trend charts:")
                    for path in generated:
                        click.echo(f"  - {path}")
            except ImportError:
                click.echo("Warning: matplotlib not installed. Skipping chart generation.", err=True)

        # Output
        if format == "json":
            output_data = json.dumps({
                "monthly_stats": [
                    {
                        "month": f"{calendar.month_abbr[stat.month]} {stat.year}",
                        "total_prompts": stat.total_prompts,
                        "total_words": stat.total_words,
                        "avg_prompt_length": round(stat.avg_prompt_length, 1),
                        "top_topics": stat.top_topics[:5],
                        "question_types": stat.question_types
                    }
                    for stat in result.monthly_stats
                ],
                "insights": [
                    {
                        "trend_type": insight.trend_type,
                        "category": insight.category,
                        "description": insight.description,
                        "evidence": insight.evidence,
                        "advice": insight.advice
                    }
                    for insight in result.insights
                ],
                "most_active_month": result.most_active_month,
                "behavior_shifts": result.behavior_shifts
            }, indent=2)
        else:
            output_data = format_trend_report(result)

        if validated_output:
            validated_output.write_text(output_data, encoding="utf-8")
            click.echo(f"Trend report saved to {validated_output}")
        else:
            click.echo(output_data)

    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
