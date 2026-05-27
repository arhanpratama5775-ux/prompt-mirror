"""
Analyzer for AI conversation patterns.
Extracts insights from user prompts.
"""

import re
from collections import Counter
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from .parser import Conversation, Message


@dataclass
class TopicCluster:
    """A cluster of related prompts."""
    name: str
    count: int
    percentage: float
    keywords: List[str]
    sample_prompts: List[str]


@dataclass
class TimePattern:
    """Pattern in prompt timing."""
    period: str  # 'morning', 'afternoon', 'evening', 'night'
    count: int
    avg_length: float
    dominant_topics: List[str]


@dataclass
class PromptPattern:
    """Detected pattern in prompts."""
    pattern_type: str
    description: str
    evidence: str
    reflection_question: str


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    total_conversations: int
    total_user_prompts: int
    total_words: int
    date_range: Tuple[Optional[datetime], Optional[datetime]]

    topics: List[TopicCluster]
    time_patterns: List[TimePattern]
    patterns: List[PromptPattern]

    question_types: Dict[str, int]  # 'how', 'what', 'why', etc.
    avg_prompt_length: float

    reflection_questions: List[str]


class PromptAnalyzer:
    """Analyze patterns in AI conversations."""

    # Topic keywords mapping
    # NOTE: Order matters! Topics are checked in order, first match wins.
    # Put more specific topics before general ones.
    # Keywords are unique per topic to avoid ambiguity.
    TOPIC_KEYWORDS = {
        "Coding & Programming": [
            "code", "function", "error", "bug", "debug", "python", "javascript",
            "api", "database", "server", "react", "node", "git", "deploy",
            "algorithm", "variable", "class", "method", "loop", "array",
            "typescript", "css", "html", "sql", "json", "framework", "library",
            "programming", "developer", "syntax", "compile", "runtime"
        ],
        "Writing & Content": [
            "write", "article", "blog", "email", "letter", "content",
            "copywriting", "headline", "caption", "post", "draft", "edit",
            "paragraph", "sentence", "rewrite", "proofread", "tone", "voice",
            "manuscript", "ghostwrite", "newsletter", "press release"
        ],
        "Learning & Research": [
            "explain", "learn", "understand", "teach", "course", "study",
            "research", "topic", "subject", "concept", "theory", "definition",
            "summary", "overview", "introduction", "tutorial", "guide",
            "education", "academic", "lecture"
        ],
        "Decision Making": [
            "should", "choose", "decide", "option", "better", "compare",
            "recommendation", "advice", "opinion", "pros", "cons", "vs",
            "alternative", "best", "worst", "worth", "consider",
            "trade-off", "evaluate"
        ],
        "Creative Projects": [
            "idea", "creative", "design", "brainstorm", "imagine",
            "art", "story", "character", "plot", "scene", "visual", "aesthetic",
            "fiction", "narrative", "worldbuilding", "artistic"
        ],
        "Career & Work": [
            "job", "career", "interview", "resume", "salary", "promotion",
            "boss", "colleague", "meeting", "project",
            "skill", "portfolio", "cover letter", "professional",
            "workplace", "employment", "freelance"
        ],
        "Personal Life": [
            "relationship", "friend", "family", "partner", "dating", "marriage",
            "parent", "child", "health", "exercise", "habit", "routine",
            "goal", "life", "happiness", "stress", "anxiety",
            "wellness", "self-care", "parenting"
        ],
        "Problem Solving": [
            "problem", "solve", "fix", "issue", "trouble", "help", "stuck",
            "solution", "workaround", "resolve", "overcome", "challenge",
            "obstacle", "difficult", "struggle"
        ],
        "Data & Analysis": [
            "data", "analyze", "chart", "graph", "statistics", "trend",
            "report", "metrics", "kpi", "insight", "correlation",
            "dataset", "visualization", "analytics"
        ],
        "Planning & Organization": [
            "plan", "schedule", "organize", "task", "todo",
            "calendar", "timeline", "roadmap", "strategy", "priority",
            "productivity", "time management", "checklist"
        ]
    }

    # Question type patterns
    # BUGFIX: Made all question patterns consistent.
    # Previously, "can" required "?" but "should", "could", "would" did not.
    # This caused non-questions like "I should probably learn Python" to be
    # counted as "should" questions, inflating the "Decision Outsourcing" metric.
    # Now all question words follow the same pattern:
    #   - Standalone question words (how/what/why/when/where/which/who) match broadly
    #     because they almost always start questions in AI conversations.
    #   - Modal verbs (can/should/could/would) require "?" to avoid matching
    #     statements like "I should..." or "It could..."
    QUESTION_PATTERNS = {
        "how": r"\bhow\b",
        "what": r"\bwhat\b",
        "why": r"\bwhy\b",
        "when": r"\bwhen\b",
        "where": r"\bwhere\b",
        "which": r"\bwhich\b",
        "who": r"\bwho\b",
        "can": r"\bcan\b.*\?",
        "should": r"\bshould\b.*\?",
        "could": r"\bcould\b.*\?",
        "would": r"\bwould\b.*\?",
        "is/are": r"\b(is|are)\b.*\?"
    }

    def analyze(self, conversations: List[Conversation]) -> AnalysisResult:
        """Perform full analysis on conversations."""
        # Extract all user prompts
        user_prompts = self._extract_user_prompts(conversations)

        # Basic stats
        total_words = sum(len(p.split()) for p in user_prompts)
        date_range = self._get_date_range(conversations)

        # Topic analysis
        topics = self._analyze_topics(user_prompts)

        # Time patterns
        time_patterns = self._analyze_time_patterns(conversations)

        # Question types
        question_types = self._analyze_question_types(user_prompts)

        # Detected patterns
        patterns = self._detect_patterns(user_prompts, topics, question_types)

        # Generate reflection questions
        reflection_questions = self._generate_reflection_questions(topics, patterns)

        return AnalysisResult(
            total_conversations=len(conversations),
            total_user_prompts=len(user_prompts),
            total_words=total_words,
            date_range=date_range,
            topics=topics,
            time_patterns=time_patterns,
            patterns=patterns,
            question_types=question_types,
            avg_prompt_length=total_words / len(user_prompts) if user_prompts else 0,
            reflection_questions=reflection_questions
        )

    def _extract_user_prompts(self, conversations: List[Conversation]) -> List[str]:
        """Extract all user prompts from conversations."""
        prompts = []
        for conv in conversations:
            for msg in conv.messages:
                if msg.role == "user" and msg.content.strip():
                    prompts.append(msg.content.strip())
        return prompts

    def _get_date_range(self, conversations: List[Conversation]) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get the date range of conversations."""
        dates = []
        for conv in conversations:
            for msg in conv.messages:
                if msg.timestamp:
                    dates.append(msg.timestamp)

        if not dates:
            return (None, None)

        return (min(dates), max(dates))

    def _analyze_topics(self, prompts: List[str]) -> List[TopicCluster]:
        """Analyze topic distribution in prompts.
        
        Each prompt is counted only once - matched to the first topic 
        that has a keyword match. This prevents percentage inflation.
        Uses word boundary matching to avoid false positives.
        """
        topic_scores = {topic: 0 for topic in self.TOPIC_KEYWORDS}
        topic_prompts = {topic: [] for topic in self.TOPIC_KEYWORDS}
        # NOTE: matched_count was previously used for percentage calculation but
        # was replaced by total_prompts (BUGFIX round 1). Removed dead variable.
        
        # Pre-compile regex patterns for each keyword (word boundary matching)
        # This prevents false positives like "class" matching "classic"
        keyword_patterns = {}
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            for keyword in keywords:
                # Use word boundary to match whole words only
                pattern = r'\b' + re.escape(keyword) + r'\b'
                keyword_patterns[(topic, keyword)] = re.compile(pattern, re.IGNORECASE)

        for prompt in prompts:
            matched = False

            # Try each topic in order, first match wins
            for topic, keywords in self.TOPIC_KEYWORDS.items():
                if matched:
                    break  # Already matched to a topic, stop checking
                for keyword in keywords:
                    pattern = keyword_patterns[(topic, keyword)]
                    if pattern.search(prompt):
                        topic_scores[topic] += 1
                        if len(topic_prompts[topic]) < 5:
                            topic_prompts[topic].append(prompt[:100] + "..." if len(prompt) > 100 else prompt)
                        matched = True
                        break  # Found match for this prompt

        # BUGFIX: Calculate percentage based on TOTAL prompts, not matched_count
        # Previously: dividing by matched_count inflated percentages
        # E.g., 100 prompts, 60 matched, 30 coding → showed 50% instead of 30%
        total_prompts = len(prompts) if prompts else 1

        topics = []
        # Sort by count (desc), then by topic name (asc) for deterministic ordering
        # This ensures consistent results when counts are equal
        sorted_topics = sorted(
            topic_scores.items(), 
            key=lambda x: (-x[1], x[0])  # -count for desc, name for asc
        )
        for topic, count in sorted_topics:
            if count > 0:
                topics.append(TopicCluster(
                    name=topic,
                    count=count,
                    percentage=(count / total_prompts) * 100,  # Fixed: use total_prompts
                    keywords=self.TOPIC_KEYWORDS[topic][:5],
                    sample_prompts=topic_prompts[topic][:3]
                ))

        return topics

    def _analyze_time_patterns(self, conversations: List[Conversation]) -> List[TimePattern]:
        """Analyze when prompts are sent.
        
        Note: Uses the timestamp's local hour (already converted if timezone was specified).
        If timestamps are in UTC and no timezone conversion was done, times will be UTC.
        """
        period_counts = {
            "morning (6-12)": [],
            "afternoon (12-18)": [],
            "evening (18-24)": [],
            "night (0-6)": []
        }

        for conv in conversations:
            for msg in conv.messages:
                if msg.role == "user" and msg.timestamp:
                    # Use the hour from the timestamp (already in local time if converted)
                    hour = msg.timestamp.hour
                    length = len(msg.content.split())

                    if 6 <= hour < 12:
                        period_counts["morning (6-12)"].append(length)
                    elif 12 <= hour < 18:
                        period_counts["afternoon (12-18)"].append(length)
                    elif 18 <= hour < 24:
                        period_counts["evening (18-24)"].append(length)
                    else:
                        period_counts["night (0-6)"].append(length)

        patterns = []
        for period, lengths in period_counts.items():
            if lengths:
                patterns.append(TimePattern(
                    period=period,
                    count=len(lengths),
                    avg_length=sum(lengths) / len(lengths),
                    dominant_topics=[]  # Would need more complex analysis
                ))

        return sorted(patterns, key=lambda p: p.count, reverse=True)

    def _analyze_question_types(self, prompts: List[str]) -> Dict[str, int]:
        """Analyze types of questions asked.
        
        Note: A single prompt can match multiple question types.
        E.g., "What should I do?" matches both 'what' and 'should'.
        This is intentional to show overall question patterns.
        """
        question_types = {qtype: 0 for qtype in self.QUESTION_PATTERNS}

        for prompt in prompts:
            prompt_lower = prompt.lower()
            for qtype, pattern in self.QUESTION_PATTERNS.items():
                if re.search(pattern, prompt_lower):
                    question_types[qtype] += 1

        # Sort by count
        return dict(sorted(question_types.items(), key=lambda x: x[1], reverse=True))

    def _detect_patterns(self, prompts: List[str], topics: List[TopicCluster],
                         question_types: Dict[str, int]) -> List[PromptPattern]:
        """Detect interesting patterns in prompts."""
        patterns = []
        total_prompts = len(prompts)

        # Pattern 1: "How" vs "Why" ratio
        how_count = question_types.get("how", 0)
        why_count = question_types.get("why", 0)

        if how_count > 0 and why_count > 0:
            ratio = how_count / why_count  # Safe: why_count > 0 already checked
            if ratio > 2:
                patterns.append(PromptPattern(
                    pattern_type="Question Balance",
                    description=f"You ask 'how' questions {ratio:.1f}x more than 'why' questions",
                    evidence=f"{how_count} 'how' vs {why_count} 'why' questions",
                    reflection_question="Are you focusing on execution over understanding?"
                ))

        # Pattern 2: Dominant topic
        if topics and topics[0].percentage > 40:
            patterns.append(PromptPattern(
                pattern_type="Topic Concentration",
                description=f"Over 40% of your prompts are about {topics[0].name}",
                evidence=f"{topics[0].count} prompts ({topics[0].percentage:.1f}%)",
                reflection_question=f"Is {topics[0].name} your main priority right now?"
            ))

        # Pattern 3: Missing topics
        # BUGFIX: Also detect topics with 0 prompts (absent from topics list entirely)
        # These are the most extreme gaps and should be reflected on!
        matched_topic_names = {t.name for t in topics}
        all_topic_names = set(self.TOPIC_KEYWORDS.keys())
        absent_topics = all_topic_names - matched_topic_names  # Topics with 0 prompts
        
        important_topics = {"Personal Life", "Career & Work", "Learning & Research"}
        
        # Topics with very low engagement (< 5%)
        low_topics = [t for t in topics if t.percentage < 5 and t.name in important_topics]
        
        # Topics with NO engagement (0 prompts) - most extreme case!
        absent_important = [name for name in absent_topics if name in important_topics]
        
        if absent_important:
            # Prioritize showing completely absent topics - this is more significant
            patterns.append(PromptPattern(
                pattern_type="Topic Gaps",
                description=f"No prompts at all about {', '.join(absent_important[:2])}",
                evidence=f"0% of your prompts touch these areas",
                reflection_question="Is this intentional? What does this say about your priorities?"
            ))
        elif low_topics:
            patterns.append(PromptPattern(
                pattern_type="Topic Gaps",
                description=f"Low engagement with {', '.join(t.name for t in low_topics[:2])}",
                evidence=f"Each under 5% of total prompts",
                reflection_question="Is this intentional or something you're avoiding?"
            ))

        # Pattern 4: Opinion-seeking (fixed: use total_prompts, not sum of matches)
        should_count = question_types.get("should", 0)
        if should_count > 0 and total_prompts > 0:
            should_pct = (should_count / total_prompts) * 100
            if should_pct > 15:
                patterns.append(PromptPattern(
                    pattern_type="Decision Outsourcing",
                    description=f"You ask 'should' questions frequently ({should_pct:.1f}% of prompts)",
                    evidence=f"{should_count} 'should' questions out of {total_prompts} prompts",
                    reflection_question="Are you outsourcing decisions you could make yourself?"
                ))

        return patterns

    def _generate_reflection_questions(self, topics: List[TopicCluster],
                                        patterns: List[PromptPattern]) -> List[str]:
        """Generate personalized reflection questions, removing duplicates."""
        questions = []
        seen_questions = set()  # Track duplicates
        
        def add_question(q: str):
            """Add question if not duplicate."""
            if q not in seen_questions:
                questions.append(q)
                seen_questions.add(q)

        # Based on topics
        if topics:
            top_topic = topics[0]
            # BUGFIX: Only append "+" for counts > 1, "1+ prompts" sounds weird
            count_str = f"{top_topic.count}+" if top_topic.count > 1 else str(top_topic.count)
            add_question(
                f"You've spent {count_str} prompts on {top_topic.name.lower()}. "
                f"Is this aligned with your priorities?"
            )

            # BUGFIX: Use .1f to avoid showing "0%" for very small but non-zero
            # percentages (e.g., 0.4% → "0%" was confusing, now shows "0.4%")
            neglected = [t for t in topics if t.percentage < 5]
            if neglected:
                add_question(
                    f"Only {neglected[0].percentage:.1f}% of prompts about "
                    f"{neglected[0].name.lower()}. Intentional?"
                )

        # Based on patterns
        for pattern in patterns[:2]:
            add_question(pattern.reflection_question)

        # General reflection
        add_question("What would you ask if AI didn't exist?")
        add_question("What did you learn this month that you still remember?")

        return questions[:5]  # Max 5 questions
