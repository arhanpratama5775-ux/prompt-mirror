"""
Trend Analyzer for tracking changes in AI conversation patterns over time.
Analyzes how topics, question types, and behaviors evolve.
"""

import re
import calendar
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from .parser import Conversation, Message
from .analyzer import PromptAnalyzer, TopicCluster


@dataclass
class MonthlyStats:
    """Statistics for a single month."""
    year: int
    month: int
    total_prompts: int
    total_words: int
    avg_prompt_length: float
    top_topics: List[Tuple[str, int]]  # (topic_name, count)
    question_types: Dict[str, int]


@dataclass
class TrendInsight:
    """A detected trend or change in behavior."""
    trend_type: str  # 'increasing', 'decreasing', 'emerging', 'fading', 'stable'
    category: str  # 'topic', 'question_type', 'activity'
    description: str
    evidence: str
    timeframe: str
    advice: str


@dataclass
class TrendAnalysisResult:
    """Complete trend analysis result."""
    monthly_stats: List[MonthlyStats]
    insights: List[TrendInsight]
    most_active_month: Optional[Tuple[str, int]]  # (month_name, prompt_count)
    topic_changes: List[Dict]  # List of topic changes over time
    behavior_shifts: List[str]  # Detected behavior shifts


class TrendAnalyzer:
    """Analyze trends and changes in AI conversations over time."""

    def __init__(self):
        self.analyzer = PromptAnalyzer()
        
        # Pre-compile regex patterns for better performance
        # This prevents re-compiling the same pattern thousands of times
        self._keyword_patterns = {}
        for topic, keywords in self.analyzer.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                pattern = r'\b' + re.escape(keyword) + r'\b'
                self._keyword_patterns[(topic, keyword)] = re.compile(pattern, re.IGNORECASE)
        
        # Pre-compile question type patterns
        self._question_patterns = {}
        for qtype, pattern in self.analyzer.QUESTION_PATTERNS.items():
            self._question_patterns[qtype] = re.compile(pattern, re.IGNORECASE)

    def analyze_trends(self, conversations: List[Conversation]) -> TrendAnalysisResult:
        """
        Analyze trends in conversations over time.
        
        Returns monthly statistics and detected insights.
        """
        # Group conversations by month
        monthly_data = self._group_by_month(conversations)
        
        # Calculate monthly stats
        monthly_stats = self._calculate_monthly_stats(monthly_data)
        
        # Detect insights
        insights = self._detect_trend_insights(monthly_stats)
        
        # Find most active month
        most_active = self._find_most_active_month(monthly_stats)
        
        # Track topic changes
        topic_changes = self._track_topic_changes(monthly_stats)
        
        # Detect behavior shifts
        behavior_shifts = self._detect_behavior_shifts(monthly_stats, insights)
        
        return TrendAnalysisResult(
            monthly_stats=monthly_stats,
            insights=insights,
            most_active_month=most_active,
            topic_changes=topic_changes,
            behavior_shifts=behavior_shifts
        )

    def _group_by_month(self, conversations: List[Conversation]) -> Dict[Tuple[int, int], List[str]]:
        """Group user prompts by year-month."""
        monthly_prompts = defaultdict(list)
        
        for conv in conversations:
            for msg in conv.messages:
                if msg.role == "user" and msg.content.strip():
                    if msg.timestamp:
                        key = (msg.timestamp.year, msg.timestamp.month)
                        monthly_prompts[key].append(msg.content.strip())
                    else:
                        # Group messages without timestamp as "unknown"
                        monthly_prompts[(0, 0)].append(msg.content.strip())
        
        return monthly_prompts

    def _calculate_monthly_stats(self, monthly_data: Dict[Tuple[int, int], List[str]]) -> List[MonthlyStats]:
        """Calculate statistics for each month."""
        stats = []
        
        for (year, month), prompts in sorted(monthly_data.items()):
            if year == 0:  # Skip unknown dates
                continue
            
            total_words = sum(len(p.split()) for p in prompts)
            
            # Analyze topics for this month
            topic_counts = self._count_topics(prompts)
            top_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Count question types
            question_types = self._count_question_types(prompts)
            
            stats.append(MonthlyStats(
                year=year,
                month=month,
                total_prompts=len(prompts),
                total_words=total_words,
                avg_prompt_length=total_words / len(prompts) if prompts else 0,
                top_topics=top_topics,
                question_types=question_types
            ))
        
        return stats

    def _count_topics(self, prompts: List[str]) -> Dict[str, int]:
        """Count topic occurrences in prompts using pre-compiled patterns."""
        topic_counts = defaultdict(int)
        
        for prompt in prompts:
            matched = False
            for topic, keywords in self.analyzer.TOPIC_KEYWORDS.items():
                if matched:
                    break
                for keyword in keywords:
                    pattern = self._keyword_patterns.get((topic, keyword))
                    if pattern and pattern.search(prompt):
                        topic_counts[topic] += 1
                        matched = True
                        break
        
        return dict(topic_counts)

    def _count_question_types(self, prompts: List[str]) -> Dict[str, int]:
        """Count question types in prompts using pre-compiled patterns."""
        question_types = defaultdict(int)
        
        for prompt in prompts:
            for qtype, pattern in self._question_patterns.items():
                if pattern.search(prompt):
                    question_types[qtype] += 1
        
        return dict(question_types)

    def _detect_trend_insights(self, monthly_stats: List[MonthlyStats]) -> List[TrendInsight]:
        """Detect meaningful trends from monthly statistics."""
        insights = []
        
        if len(monthly_stats) < 2:
            insights.append(TrendInsight(
                trend_type="insufficient_data",
                category="activity",
                description="Not enough data for trend analysis",
                evidence=f"Only {len(monthly_stats)} month(s) of data",
                timeframe="N/A",
                advice="Continue using AI and export again in a few months"
            ))
            return insights
        
        # Check activity trend
        first_half = monthly_stats[:len(monthly_stats)//2]
        second_half = monthly_stats[len(monthly_stats)//2:]
        
        first_avg = sum(m.total_prompts for m in first_half) / len(first_half)
        second_avg = sum(m.total_prompts for m in second_half) / len(second_half)
        
        if second_avg > first_avg * 1.5:
            insights.append(TrendInsight(
                trend_type="increasing",
                category="activity",
                description="Your AI usage is increasing significantly",
                evidence=f"From avg {first_avg:.0f} to {second_avg:.0f} prompts/month",
                timeframe=f"{self._month_name(monthly_stats[0])} to {self._month_name(monthly_stats[-1])}",
                advice="Consider whether this increase serves your goals"
            ))
        elif second_avg < first_avg * 0.7:
            insights.append(TrendInsight(
                trend_type="decreasing",
                category="activity",
                description="Your AI usage has decreased",
                evidence=f"From avg {first_avg:.0f} to {second_avg:.0f} prompts/month",
                timeframe=f"{self._month_name(monthly_stats[0])} to {self._month_name(monthly_stats[-1])}",
                advice="Are you becoming more self-reliant, or avoiding something?"
            ))
        
        # Check topic evolution
        if len(monthly_stats) >= 3:
            first_topics = set(t[0] for t in monthly_stats[0].top_topics[:3])
            last_topics = set(t[0] for t in monthly_stats[-1].top_topics[:3])
            
            emerging = last_topics - first_topics
            fading = first_topics - last_topics
            
            if emerging:
                insights.append(TrendInsight(
                    trend_type="emerging",
                    category="topic",
                    description=f"New focus area(s) detected: {', '.join(emerging)}",
                    evidence=f"Appeared in top topics recently",
                    timeframe=f"Last few months",
                    advice="Is this shift intentional or reactive?"
                ))
            
            if fading:
                insights.append(TrendInsight(
                    trend_type="fading",
                    category="topic",
                    description=f"Topics you've moved away from: {', '.join(fading)}",
                    evidence=f"Dropped from top topics",
                    timeframe=f"Over {len(monthly_stats)} months",
                    advice="Did you solve these problems or lose interest?"
                ))
        
        # Check question type trends
        if len(monthly_stats) >= 2:
            first_should = monthly_stats[0].question_types.get("should", 0)
            last_should = monthly_stats[-1].question_types.get("should", 0)
            
            # BUGFIX: Handle case when either month has 0 "should" questions
            # This is actually the most interesting case (stopped asking "should"!)
            first_should_pct = first_should / monthly_stats[0].total_prompts * 100 if monthly_stats[0].total_prompts > 0 else 0
            last_should_pct = last_should / monthly_stats[-1].total_prompts * 100 if monthly_stats[-1].total_prompts > 0 else 0
            
            # Only skip if both are 0 (no "should" questions at all)
            if first_should == 0 and last_should == 0:
                pass  # No "should" questions to analyze
            # BUGFIX: Check absolute zero cases FIRST (before percentage comparison)
            # Previously, "stopped entirely" (10%→0%) was caught by the generic
            # "decreasing" condition (0 < 10-5), making the specific message unreachable
            elif first_should > 0 and last_should == 0:
                # Special case: stopped asking "should" completely!
                insights.append(TrendInsight(
                    trend_type="decreasing",
                    category="question_type",
                    description="You've stopped asking 'should' questions entirely",
                    evidence=f"{first_should_pct:.1f}% → 0% 'should' questions",
                    timeframe=f"{self._month_name(monthly_stats[0])} to {self._month_name(monthly_stats[-1])}",
                    advice="Excellent! You're making decisions independently now."
                ))
            elif first_should == 0 and last_should > 0:
                # Special case: started asking "should" questions - new pattern!
                insights.append(TrendInsight(
                    trend_type="increasing",
                    category="question_type",
                    description="You've started asking 'should' questions recently",
                    evidence=f"0% → {last_should_pct:.1f}% 'should' questions",
                    timeframe=f"{self._month_name(monthly_stats[0])} to {self._month_name(monthly_stats[-1])}",
                    advice="Are you starting to outsource decisions? Stay aware of this pattern."
                ))
            elif last_should_pct > first_should_pct + 5:
                insights.append(TrendInsight(
                    trend_type="increasing",
                    category="question_type",
                    description="You're asking more 'should' questions over time",
                    evidence=f"{first_should_pct:.1f}% → {last_should_pct:.1f}% 'should' questions",
                    timeframe=f"{self._month_name(monthly_stats[0])} to {self._month_name(monthly_stats[-1])}",
                    advice="Are you outsourcing more decisions? Consider why."
                ))
            elif last_should_pct < first_should_pct - 5:
                insights.append(TrendInsight(
                    trend_type="decreasing",
                    category="question_type",
                    description="You're asking fewer 'should' questions",
                    evidence=f"{first_should_pct:.1f}% → {last_should_pct:.1f}% 'should' questions",
                    timeframe=f"{self._month_name(monthly_stats[0])} to {self._month_name(monthly_stats[-1])}",
                    advice="Good sign! You may be making more decisions independently."
                ))
        
        return insights

    def _find_most_active_month(self, monthly_stats: List[MonthlyStats]) -> Optional[Tuple[str, int]]:
        """Find the most active month."""
        if not monthly_stats:
            return None
        
        most_active = max(monthly_stats, key=lambda m: m.total_prompts)
        month_name = self._month_name(most_active)
        
        return (month_name, most_active.total_prompts)

    def _track_topic_changes(self, monthly_stats: List[MonthlyStats]) -> List[Dict]:
        """Track how topics change over time."""
        if len(monthly_stats) < 2:
            return []
        
        changes = []
        all_topics = set()
        
        # Collect all topics that appear
        for stat in monthly_stats:
            for topic, count in stat.top_topics:
                all_topics.add(topic)
        
        # Track each topic over time
        for topic in all_topics:
            trajectory = []
            for stat in monthly_stats:
                count = dict(stat.top_topics).get(topic, 0)
                trajectory.append({
                    'month': self._month_name(stat),
                    'count': count
                })
            
            # Only include if there's activity
            if any(t['count'] > 0 for t in trajectory):
                changes.append({
                    'topic': topic,
                    'trajectory': trajectory
                })
        
        return sorted(changes, key=lambda x: sum(t['count'] for t in x['trajectory']), reverse=True)[:10]

    def _detect_behavior_shifts(self, monthly_stats: List[MonthlyStats], insights: List[TrendInsight]) -> List[str]:
        """Detect significant behavior shifts."""
        shifts = []
        
        if len(monthly_stats) < 3:
            return ["Need more data to detect behavior patterns"]
        
        # Prompt length trend
        lengths = [m.avg_prompt_length for m in monthly_stats]
        if lengths[-1] > lengths[0] * 1.3:
            shifts.append("Your prompts are getting longer - you may be providing more context")
        elif lengths[-1] < lengths[0] * 0.7:
            shifts.append("Your prompts are getting shorter - you may be getting more concise")
        
        # Activity consistency
        prompts_per_month = [m.total_prompts for m in monthly_stats]
        avg = sum(prompts_per_month) / len(prompts_per_month)
        variance = sum((p - avg) ** 2 for p in prompts_per_month) / len(prompts_per_month)
        std_dev = variance ** 0.5
        
        if std_dev > avg * 0.5:
            shifts.append("Your AI usage is inconsistent - some months much more active than others")
        
        # Topic concentration trend
        if monthly_stats[0].top_topics and monthly_stats[-1].top_topics:
            first_concentration = monthly_stats[0].top_topics[0][1] / monthly_stats[0].total_prompts if monthly_stats[0].total_prompts > 0 else 0
            last_concentration = monthly_stats[-1].top_topics[0][1] / monthly_stats[-1].total_prompts if monthly_stats[-1].total_prompts > 0 else 0
            
            if last_concentration > first_concentration + 0.1:
                shifts.append("You're becoming more focused - concentrating on fewer topics")
            elif last_concentration < first_concentration - 0.1:
                shifts.append("You're exploring more diverse topics")
        
        return shifts if shifts else ["Your behavior patterns are relatively stable"]

    def _month_name(self, stat: MonthlyStats) -> str:
        """Get month name from MonthlyStats."""
        return f"{calendar.month_abbr[stat.month]} {stat.year}"


def format_trend_report(result: TrendAnalysisResult) -> str:
    """Format trend analysis result as a readable report."""
    lines = []
    
    lines.append("=" * 60)
    lines.append("       YOUR TREND ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append("")
    
    # Monthly overview
    lines.append("MONTHLY OVERVIEW:")
    lines.append("-" * 40)
    
    for stat in result.monthly_stats[-6:]:  # Last 6 months
        month_name = f"{calendar.month_abbr[stat.month]} {stat.year}"
        lines.append(f"  {month_name}: {stat.total_prompts} prompts, {stat.total_words:,} words")
    
    lines.append("")
    
    # Most active month
    if result.most_active_month:
        lines.append(f"PEAK ACTIVITY: {result.most_active_month[0]} with {result.most_active_month[1]} prompts")
        lines.append("")
    
    # Insights
    if result.insights:
        lines.append("TREND INSIGHTS:")
        lines.append("-" * 40)
        
        for i, insight in enumerate(result.insights, 1):
            icon = {
                'increasing': '📈',
                'decreasing': '📉',
                'emerging': '🆕',
                'fading': '👋',
                'stable': '➡️',
                'insufficient_data': '❓'
            }.get(insight.trend_type, '•')
            
            lines.append(f"  {icon} {insight.description}")
            lines.append(f"     Evidence: {insight.evidence}")
            lines.append(f"     Reflection: {insight.advice}")
            lines.append("")
    
    # Behavior shifts
    if result.behavior_shifts:
        lines.append("BEHAVIOR SHIFTS:")
        lines.append("-" * 40)
        for shift in result.behavior_shifts:
            lines.append(f"  • {shift}")
        lines.append("")
    
    lines.append("=" * 60)
    lines.append("")
    lines.append("Trends show patterns, but you decide what they mean.")
    lines.append("Use these insights to become more intentional.")
    
    return "\n".join(lines)
