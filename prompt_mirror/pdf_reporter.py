"""
PDF Reporter for generating PDF reports from analysis results.
Creates beautiful, shareable PDF reports.
"""

import os
import html
from datetime import datetime
from typing import Optional

from .analyzer import AnalysisResult, TopicCluster, TimePattern, PromptPattern

# Handle reportlab import gracefully
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

# BUGFIX: Register CJK fonts for PDF to support Chinese/Japanese/Korean text
# Without this, non-Latin characters would show as garbled text or cause errors
_CJK_FONT_PATHS = [
    ('NotoSansSC', '/usr/share/fonts/truetype/chinese/NotoSansSC[wght].ttf'),
    ('NotoSansCJK', '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'),
    ('WenQuanYi', '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'),
]

_CJK_FONT_REGISTERED = False

if HAS_REPORTLAB:
    for font_name, font_path in _CJK_FONT_PATHS:
        try:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                _CJK_FONT_REGISTERED = True
                break
        except Exception:
            continue


def _escape_pdf_text(text: str, max_length: int = 200) -> str:
    """
    Escape HTML special characters and truncate long text for PDF.
    
    ReportLab Paragraph interprets HTML, so we need to escape:
    - < and > to prevent HTML tag interpretation
    - & to prevent entity interpretation
    
    Also truncates text to prevent table overflow.
    """
    if not text:
        return ""
    
    # Escape HTML characters
    escaped = html.escape(str(text))
    
    # Truncate if too long
    if len(escaped) > max_length:
        escaped = escaped[:max_length - 3] + "..."
    
    return escaped


class PDFReporter:
    """Generate PDF reports from analysis results."""

    def __init__(self):
        if not HAS_REPORTLAB:
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Install it with: pip install reportlab"
            )

    def generate(self, result: AnalysisResult, output_path: str) -> str:
        """Generate a PDF report and save to output path."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )

        styles = getSampleStyleSheet()
        
        # Custom styles
        # BUGFIX: Use CJK font if available, fallback to Helvetica
        # NOTE: NotoSansSC registered via TTFont does NOT have an automatic bold
        # variant in reportlab. We must register bold weight separately.
        # For now, we use the same font and rely on reportlab's <b> tag
        # (in Paragraph objects) for artificial bold. But for TableStyle FONTNAME,
        # we need a real bold font. So we register bold separately if possible.
        base_font = 'NotoSansSC' if _CJK_FONT_REGISTERED else 'Helvetica'
        base_font_bold = 'Helvetica-Bold'  # Always use Helvetica-Bold for tables
        # For Paragraph objects, <b> tags will handle emphasis regardless of font

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName=base_font_bold,
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=30,
            textColor=colors.HexColor('#2d3436')
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontName=base_font,
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#636e72'),
            spaceAfter=20
        )

        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontName=base_font_bold,
            fontSize=14,
            textColor=colors.HexColor('#6C63FF'),
            spaceBefore=15,
            spaceAfter=10
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontName=base_font,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#2d3436')
        )

        story = []

        # Title
        story.append(Paragraph("Your Mirror Report", title_style))
        story.append(Paragraph("A reflection of your AI conversation patterns", subtitle_style))
        story.append(Spacer(1, 20))

        # Overview Section
        story.append(Paragraph("Overview", section_style))
        
        overview_data = [
            ['Metric', 'Value'],
            ['Total Conversations', str(result.total_conversations)],
            ['Total Prompts by You', str(result.total_user_prompts)],
            ['Total Words', f'{result.total_words:,}'],
            ['Average Prompt Length', f'{result.avg_prompt_length:.1f} words'],
        ]

        if result.date_range[0] and result.date_range[1]:
            start = result.date_range[0].strftime("%B %Y")
            end = result.date_range[1].strftime("%B %Y")
            overview_data.append(['Date Range', f'{start} - {end}'])

        overview_table = Table(overview_data, colWidths=[3*inch, 3*inch])
        overview_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6C63FF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), base_font_bold),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (0, 1), (-1, -1), base_font),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dfe6e9')),
        ]))

        story.append(overview_table)
        story.append(Spacer(1, 25))

        # Topics Section
        if result.topics:
            story.append(Paragraph("Your Top Topics", section_style))

            topic_data = [['#', 'Topic', 'Prompts', '%']]
            for i, topic in enumerate(result.topics[:10], 1):
                topic_data.append([
                    str(i),
                    _escape_pdf_text(topic.name, max_length=30),  # Truncate long names
                    str(topic.count),
                    f'{topic.percentage:.0f}%'
                ])

            topic_table = Table(topic_data, colWidths=[0.5*inch, 3*inch, 1*inch, 1*inch])
            topic_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00b894')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), base_font_bold),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dfe6e9')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ]))

            story.append(topic_table)
            story.append(Spacer(1, 25))

        # Time Patterns Section
        if result.time_patterns:
            story.append(Paragraph("When You Ask", section_style))

            time_data = [['Period', 'Prompts', 'Avg Length']]
            for tp in result.time_patterns:
                time_data.append([
                    tp.period,
                    str(tp.count),
                    f'{tp.avg_length:.1f} words'
                ])

            time_table = Table(time_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch])
            time_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#fdcb6e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2d3436')),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), base_font_bold),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), base_font),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dfe6e9')),
            ]))

            story.append(time_table)
            story.append(Spacer(1, 25))

        # Question Types Section
        if result.question_types:
            story.append(Paragraph("Question Types", section_style))

            qtypes = [(k, v) for k, v in result.question_types.items() if v > 0]
            qtypes = sorted(qtypes, key=lambda x: x[1], reverse=True)[:10]

            q_data = [['Question Type', 'Count']]
            for qtype, count in qtypes:
                q_data.append([qtype.title(), str(count)])

            q_table = Table(q_data, colWidths=[3*inch, 2*inch])
            q_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e17055')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), base_font_bold),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('FONTNAME', (0, 1), (-1, -1), base_font),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dfe6e9')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff5f2')]),
            ]))

            story.append(q_table)
            story.append(Spacer(1, 25))

        # Patterns Section
        if result.patterns:
            story.append(Paragraph("Patterns Detected", section_style))

            for pattern in result.patterns:
                story.append(Paragraph(
                    f"<b>{_escape_pdf_text(pattern.pattern_type)}:</b> {_escape_pdf_text(pattern.description)}",
                    body_style
                ))
                story.append(Paragraph(
                    f"<i>Evidence: {_escape_pdf_text(pattern.evidence)}</i>",
                    ParagraphStyle('Evidence', parent=body_style, textColor=colors.HexColor('#636e72'), fontSize=9)
                ))
                story.append(Spacer(1, 8))

            story.append(Spacer(1, 15))

        # Reflection Questions Section
        if result.reflection_questions:
            story.append(Paragraph("Reflection Questions", section_style))

            for i, question in enumerate(result.reflection_questions, 1):
                story.append(Paragraph(
                    f"<b>{i}.</b> {_escape_pdf_text(question)}",
                    body_style
                ))
                story.append(Spacer(1, 6))

        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(
            "This is a mirror, not a judgment. Use these insights however you see fit.",
            ParagraphStyle('Footer', parent=body_style, alignment=TA_CENTER, textColor=colors.HexColor('#636e72'), fontSize=9)
        ))

        story.append(Spacer(1, 10))
        story.append(Paragraph(
            f"Generated by Prompt Mirror on {datetime.now().strftime('%Y-%m-%d')}",
            ParagraphStyle('FooterDate', parent=body_style, alignment=TA_CENTER, textColor=colors.HexColor('#b2bec3'), fontSize=8)
        ))

        # Build PDF
        doc.build(story)

        return output_path
