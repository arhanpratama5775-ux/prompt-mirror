"""
Visualizer for generating charts from analysis results.
Creates PNG charts for topic distribution, time patterns, question types, and trends.
"""

import os
from pathlib import Path
from typing import Optional, List

from .analyzer import AnalysisResult
from .trend_analyzer import TrendAnalysisResult

# Handle matplotlib import gracefully
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

# Handle Chinese font support - try multiple common paths
_CHINESE_FONT_PATHS = [
    '/usr/share/fonts/truetype/chinese/NotoSansSC[wght].ttf',  # Linux (Debian/Ubuntu)
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',  # Linux (alternative)
    '/System/Library/Fonts/PingFang.ttc',  # macOS
    'C:\\Windows\\Fonts\\msyh.ttc',  # Windows (Microsoft YaHei)
]

if HAS_MATPLOTLIB:
    try:
        import matplotlib.font_manager as fm
        for font_path in _CHINESE_FONT_PATHS:
            if os.path.exists(font_path):
                fm.fontManager.addfont(font_path)
                plt.rcParams['font.sans-serif'] = ['Noto Sans SC', 'DejaVu Sans', 'sans-serif']
                plt.rcParams['axes.unicode_minus'] = False
                break
    except Exception:
        # Font loading failed - charts will use default font
        pass


class MirrorVisualizer:
    """Generate charts from analysis results."""

    def __init__(self):
        if not HAS_MATPLOTLIB:
            raise ImportError(
                "matplotlib is required for visualization. "
                "Install it with: pip install matplotlib"
            )

    def generate_all(self, result: AnalysisResult, output_dir: str) -> list:
        """
        Generate all charts and save to output directory.
        
        Returns list of generated file paths.
        """
        os.makedirs(output_dir, exist_ok=True)
        generated = []

        # Topic distribution
        if result.topics:
            path = self._generate_topic_chart(result, output_dir)
            if path:
                generated.append(path)

        # Time patterns
        if result.time_patterns:
            path = self._generate_time_chart(result, output_dir)
            if path:
                generated.append(path)

        # Question types
        if result.question_types:
            path = self._generate_question_chart(result, output_dir)
            if path:
                generated.append(path)

        return generated

    def _generate_topic_chart(self, result: AnalysisResult, output_dir: str) -> str:
        """Generate pie chart for topic distribution."""
        fig, ax = plt.subplots(figsize=(10, 6))

        labels = [t.name for t in result.topics[:8]]
        sizes = [t.percentage for t in result.topics[:8]]
        
        # Colors
        colors = plt.cm.Set3(range(len(labels)))

        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            sizes, 
            labels=labels, 
            autopct='%1.0f%%',
            colors=colors,
            startangle=90,
            pctdistance=0.85
        )

        # Style
        plt.setp(autotexts, size=9)
        plt.setp(texts, size=10)
        
        ax.set_title('Your Topic Distribution', fontsize=14, fontweight='bold')

        plt.tight_layout()
        
        output_path = os.path.join(output_dir, 'topics.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        return output_path

    def _generate_time_chart(self, result: AnalysisResult, output_dir: str) -> str:
        """Generate bar chart for time patterns."""
        fig, ax = plt.subplots(figsize=(10, 5))

        periods = [tp.period for tp in result.time_patterns]
        counts = [tp.count for tp in result.time_patterns]

        # Colors based on time of day
        color_map = {
            'morning': '#FFD93D',
            'afternoon': '#FF8B3D', 
            'evening': '#6C63FF',
            'night': '#2D3436'
        }
        colors = [color_map.get(p.split()[0], '#74b9ff') for p in periods]

        bars = ax.barh(periods, counts, color=colors, edgecolor='white', height=0.6)

        # Add count labels
        for bar, count in zip(bars, counts):
            ax.text(
                bar.get_width() + max(counts) * 0.02, 
                bar.get_y() + bar.get_height()/2,
                f'{count}',
                va='center',
                fontsize=10
            )

        ax.set_xlabel('Number of Prompts', fontsize=11)
        ax.set_title('When You Ask AI', fontsize=14, fontweight='bold')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()

        output_path = os.path.join(output_dir, 'time_patterns.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        return output_path

    def _generate_question_chart(self, result: AnalysisResult, output_dir: str) -> Optional[str]:
        """Generate bar chart for question types. Returns None if no data."""
        fig, ax = plt.subplots(figsize=(10, 5))

        # Filter to only show question types with counts > 0
        qtypes = [(k, v) for k, v in result.question_types.items() if v > 0]
        qtypes = sorted(qtypes, key=lambda x: x[1], reverse=True)[:10]

        if not qtypes:
            plt.close()
            return None

        labels = [k for k, v in qtypes]
        counts = [v for k, v in qtypes]

        colors = plt.cm.viridis([i/len(labels) for i in range(len(labels))])

        bars = ax.bar(labels, counts, color=colors, edgecolor='white')

        # Add count labels on top
        for bar, count in zip(bars, counts):
            ax.text(
                bar.get_x() + bar.get_width()/2,
                bar.get_height() + max(counts) * 0.02,
                str(count),
                ha='center',
                fontsize=9
            )

        ax.set_xlabel('Question Type', fontsize=11)
        ax.set_ylabel('Count', fontsize=11)
        ax.set_title('How You Ask Questions', fontsize=14, fontweight='bold')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        output_path = os.path.join(output_dir, 'question_types.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        return output_path

    def generate_summary_image(self, result: AnalysisResult, output_path: str) -> str:
        """Generate a single summary image with all charts."""
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        # Topic pie chart
        ax = axes[0]
        if result.topics:
            labels = [t.name.split()[0] for t in result.topics[:5]]  # First word only
            sizes = [t.percentage for t in result.topics[:5]]
            colors = plt.cm.Set3(range(len(labels)))
            ax.pie(sizes, labels=labels, autopct='%1.0f%%', colors=colors, startangle=90)
        ax.set_title('Topics', fontsize=12, fontweight='bold')

        # Time bar chart
        ax = axes[1]
        if result.time_patterns:
            periods = [tp.period.split()[0] for tp in result.time_patterns]
            counts = [tp.count for tp in result.time_patterns]
            ax.bar(periods, counts, color='#6C63FF')
            ax.set_ylabel('Prompts')
        ax.set_title('When You Ask', fontsize=12, fontweight='bold')

        # Question types
        ax = axes[2]
        if result.question_types:
            qtypes = [(k, v) for k, v in result.question_types.items() if v > 0][:5]
            if qtypes:
                labels = [k for k, v in qtypes]
                counts = [v for k, v in qtypes]
                ax.barh(labels, counts, color='#74b9ff')
        ax.set_title('Question Types', fontsize=12, fontweight='bold')

        plt.suptitle('Your AI Conversation Mirror', fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        return output_path

    def generate_trend_charts(self, trend_result: TrendAnalysisResult, output_dir: str) -> List[str]:
        """Generate charts for trend analysis."""
        os.makedirs(output_dir, exist_ok=True)
        generated = []

        if not trend_result.monthly_stats:
            return generated

        # Monthly activity chart
        path = self._generate_activity_trend_chart(trend_result, output_dir)
        if path:
            generated.append(path)

        # Topic evolution chart
        path = self._generate_topic_evolution_chart(trend_result, output_dir)
        if path:
            generated.append(path)

        return generated

    def _generate_activity_trend_chart(self, trend_result: TrendAnalysisResult, output_dir: str) -> Optional[str]:
        """Generate line chart showing activity over time."""
        if len(trend_result.monthly_stats) < 2:
            return None

        fig, ax = plt.subplots(figsize=(12, 5))

        # BUGFIX: Use consistent month format with calendar.month_abbr
        # Previously used {stat.month:02d}/{stat.year} which was inconsistent
        # with _generate_topic_evolution_chart that used month_abbr
        months = [f"{calendar.month_abbr[stat.month]} {stat.year}" for stat in trend_result.monthly_stats]
        prompts = [stat.total_prompts for stat in trend_result.monthly_stats]
        words = [stat.total_words / 100 for stat in trend_result.monthly_stats]  # Scale down using float division

        x = range(len(months))
        
        # Plot prompts
        line1 = ax.plot(x, prompts, 'o-', color='#6C63FF', linewidth=2, markersize=8, label='Prompts')
        ax.set_xlabel('Month', fontsize=11)
        ax.set_ylabel('Number of Prompts', fontsize=11, color='#6C63FF')
        ax.tick_params(axis='y', labelcolor='#6C63FF')

        # Plot words on secondary axis
        ax2 = ax.twinx()
        line2 = ax2.plot(x, words, 's--', color='#00b894', linewidth=2, markersize=6, label='Words (×100)')
        ax2.set_ylabel('Words (×100)', fontsize=11, color='#00b894')
        ax2.tick_params(axis='y', labelcolor='#00b894')

        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45, ha='right')
        ax.set_title('Your AI Activity Over Time', fontsize=14, fontweight='bold')
        
        # Combined legend
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='upper left')

        ax.spines['top'].set_visible(False)
        ax2.spines['top'].set_visible(False)

        plt.tight_layout()
        output_path = os.path.join(output_dir, 'activity_trend.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        return output_path

    def _generate_topic_evolution_chart(self, trend_result: TrendAnalysisResult, output_dir: str) -> Optional[str]:
        """Generate stacked area chart showing topic evolution."""
        if not trend_result.topic_changes or len(trend_result.monthly_stats) < 2:
            return None

        fig, ax = plt.subplots(figsize=(12, 6))

        # BUGFIX: Use same month format as trend_analyzer._month_name()
        # trend_analyzer uses "Jan 2025" format, not "01/2025"
        import calendar
        months = [f"{calendar.month_abbr[stat.month]} {stat.year}" for stat in trend_result.monthly_stats]
        x = range(len(months))

        # Get top 5 topics by total count
        top_topics = trend_result.topic_changes[:5]
        
        # Color palette
        colors = ['#6C63FF', '#00b894', '#fdcb6e', '#e17055', '#74b9ff']

        # Plot each topic as stacked area
        bottom = [0] * len(months)
        for i, topic_data in enumerate(top_topics):
            topic_name = topic_data['topic']
            trajectory = topic_data['trajectory']
            
            # Match trajectory to months (now formats match!)
            counts = []
            for month_name in months:
                found = False
                for t in trajectory:
                    if t['month'] == month_name:
                        counts.append(t['count'])
                        found = True
                        break
                if not found:
                    counts.append(0)
            
            ax.bar(x, counts, bottom=bottom, label=topic_name[:15], color=colors[i % len(colors)], alpha=0.8)
            bottom = [b + c for b, c in zip(bottom, counts)]

        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45, ha='right')
        ax.set_xlabel('Month', fontsize=11)
        ax.set_ylabel('Number of Prompts', fontsize=11)
        ax.set_title('How Your Topics Evolved Over Time', fontsize=14, fontweight='bold')
        ax.legend(loc='upper left', framealpha=0.9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        plt.tight_layout()
        output_path = os.path.join(output_dir, 'topic_evolution.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        return output_path
