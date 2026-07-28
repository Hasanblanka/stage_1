"""Create a two-page English PDF summary for Stage 1."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = REPO_ROOT / "output" / "pdf" / "polygraf_ner_stage1_report.pdf"
BEFORE_PATH = REPO_ROOT / "artifacts" / "stage1" / "before_cleanup_stats.json"
AFTER_PATH = REPO_ROOT / "artifacts" / "stage1" / "after_cleanup_stats.json"
SUMMARY_PATH = REPO_ROOT / "artifacts" / "stage1" / "cleanup_summary.json"

FONT_REGULAR = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")

NAVY = colors.HexColor("#17324D")
TEAL = colors.HexColor("#15808D")
PALE_TEAL = colors.HexColor("#EAF5F6")
PALE_BLUE = colors.HexColor("#EFF4F8")
PALE_GRAY = colors.HexColor("#F6F7F9")
TEXT = colors.HexColor("#18242E")
MUTED = colors.HexColor("#66747F")
WHITE = colors.white


def load_json(path: Path) -> dict[str, Any]:
    """Read a JSON file with UTF-8 encoding."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def register_fonts() -> None:
    """Register the fonts used by the report."""
    if not FONT_REGULAR.exists() or not FONT_BOLD.exists():
        raise FileNotFoundError("Arial font files were not found.")
    pdfmetrics.registerFont(TTFont("Arial", str(FONT_REGULAR)))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(FONT_BOLD)))


def build_styles() -> dict[str, ParagraphStyle]:
    """Create compact text styles for the report."""
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleAz",
            parent=base["Title"],
            fontName="Arial-Bold",
            fontSize=22,
            leading=27,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=3 * mm,
        ),
        "subtitle": ParagraphStyle(
            "SubtitleAz",
            parent=base["Normal"],
            fontName="Arial",
            fontSize=9,
            leading=12,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceAfter=5 * mm,
        ),
        "h1": ParagraphStyle(
            "HeadingAz",
            parent=base["Heading1"],
            fontName="Arial-Bold",
            fontSize=14,
            leading=17,
            textColor=NAVY,
            spaceBefore=2 * mm,
            spaceAfter=3 * mm,
        ),
        "body": ParagraphStyle(
            "BodyAz",
            parent=base["BodyText"],
            fontName="Arial",
            fontSize=8.8,
            leading=12.2,
            textColor=TEXT,
            spaceAfter=2 * mm,
        ),
        "bullet": ParagraphStyle(
            "BulletAz",
            parent=base["BodyText"],
            fontName="Arial",
            fontSize=8.6,
            leading=11.7,
            textColor=TEXT,
            leftIndent=5 * mm,
            firstLineIndent=-3 * mm,
            spaceAfter=1.2 * mm,
        ),
        "small": ParagraphStyle(
            "SmallAz",
            parent=base["BodyText"],
            fontName="Arial",
            fontSize=7.2,
            leading=9.5,
            textColor=MUTED,
        ),
        "table": ParagraphStyle(
            "TableAz",
            parent=base["BodyText"],
            fontName="Arial",
            fontSize=7.7,
            leading=9.5,
            textColor=TEXT,
        ),
        "table_head": ParagraphStyle(
            "TableHeadAz",
            parent=base["BodyText"],
            fontName="Arial-Bold",
            fontSize=7.7,
            leading=9.5,
            textColor=WHITE,
        ),
        "card_value": ParagraphStyle(
            "CardValueAz",
            parent=base["Normal"],
            fontName="Arial-Bold",
            fontSize=18,
            leading=21,
            alignment=TA_CENTER,
            textColor=NAVY,
        ),
        "card_label": ParagraphStyle(
            "CardLabelAz",
            parent=base["Normal"],
            fontName="Arial",
            fontSize=7,
            leading=8.5,
            alignment=TA_CENTER,
            textColor=MUTED,
        ),
        "note": ParagraphStyle(
            "NoteAz",
            parent=base["BodyText"],
            fontName="Arial",
            fontSize=8,
            leading=11,
            textColor=NAVY,
            backColor=PALE_TEAL,
            borderColor=TEAL,
            borderWidth=0.6,
            borderPadding=6,
            spaceBefore=2 * mm,
            spaceAfter=2 * mm,
        ),
    }


def make_table(
    rows: list[list[Any]],
    widths: list[float],
    styles: dict[str, ParagraphStyle],
) -> Table:
    """Create a table with a header and alternating row backgrounds."""
    formatted: list[list[Any]] = []
    for row_index, row in enumerate(rows):
        style = styles["table_head"] if row_index == 0 else styles["table"]
        formatted.append([Paragraph(str(cell), style) for cell in row])

    table = Table(formatted, colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, PALE_GRAY]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D4DCE2")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def make_cards(
    values: list[tuple[str, str]], styles: dict[str, ParagraphStyle]
) -> Table:
    """Display key metrics as comparison cards."""
    cells = [
        [
            Paragraph(value, styles["card_value"]),
            Spacer(1, 1 * mm),
            Paragraph(label, styles["card_label"]),
        ]
        for value, label in values
    ]
    table = Table([cells], colWidths=[43.5 * mm] * len(cells))
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CAD6DF")),
                ("INNERGRID", (0, 0), (-1, -1), 0.6, WHITE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def draw_page(canvas: Any, doc: Any) -> None:
    """Draw the page header, footer, and number."""
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 9 * mm, width, 9 * mm, fill=1, stroke=0)
    canvas.setFont("Arial-Bold", 7)
    canvas.setFillColor(WHITE)
    canvas.drawString(18 * mm, height - 5.8 * mm, "POLYGRAF - STAGE 1 DATASET SUMMARY")
    canvas.setFont("Arial", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 9 * mm, "Raw and cleaned data comparison")
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"Page {doc.page}/2")
    canvas.restoreState()


def build_pdf() -> None:
    """Read the statistics and create a two-page PDF."""
    register_fonts()
    styles = build_styles()
    before = load_json(BEFORE_PATH)
    after = load_json(AFTER_PATH)
    summary = load_json(SUMMARY_PATH)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Polygraf NER - Stage 1 Dataset Summary",
        author="Hasan Yusifzade",
        subject="Dataset comparison before and after cleanup",
    )

    story: list[Any] = [
        Paragraph("Stage 1 - Dataset Cleanup Summary", styles["title"]),
        Paragraph(
            f"Report date: {date.today().strftime('%d.%m.%Y')} - "
            "Final Stage 1 manual QA results",
            styles["subtitle"],
        ),
        Paragraph("1. Before and after", styles["h1"]),
        make_cards(
            [
                (str(before["records_total"]), "BEFORE: RECORDS"),
                (str(after["records_total"]), "AFTER: RECORDS"),
                (str(before["spans_total"]), "BEFORE: SPANS"),
                (str(after["spans_total"]), "AFTER: SPANS"),
            ],
            styles,
        ),
        Spacer(1, 4 * mm),
    ]

    overview_rows = [
        ["Metric", "Before", "After"],
        ["Records", before["records_total"], after["records_total"]],
        ["Spans", before["spans_total"], after["spans_total"]],
        [
            "Invalid labels",
            before.get("unknown_label_counts", {}).get("COMPANY", 0),
            sum(after.get("unknown_label_counts", {}).values()),
        ],
        [
            "Automatic errors",
            before["severity_counts"].get("error", 0),
            after["severity_counts"].get("error", 0),
        ],
        [
            "Automatic warnings",
            before["severity_counts"].get("warning", 0),
            after["severity_counts"].get("warning", 0),
        ],
    ]
    story.extend(
        [
            make_table(overview_rows, [90 * mm, 42 * mm, 42 * mm], styles),
            Spacer(1, 4 * mm),
            Paragraph("Label distribution", styles["h1"]),
        ]
    )

    label_order = [
        "PERSON",
        "ORGANIZATION",
        "LOCATION",
        "TIMEDATE",
        "PRODUCT",
        "WORKOFART",
        "JOB",
        "AMOUNT",
        "COMPANY",
    ]
    before_labels = {
        **before["label_counts"],
        **before.get("unknown_label_counts", {}),
    }
    after_labels = {
        **after["label_counts"],
        **after.get("unknown_label_counts", {}),
    }
    label_rows = [["Label", "Before", "After", "Difference"]]
    for label in label_order:
        old = before_labels.get(label, 0)
        new = after_labels.get(label, 0)
        label_rows.append([label, old, new, f"{new - old:+d}"])
    story.extend(
        [
            make_table(label_rows, [78 * mm, 32 * mm, 32 * mm, 32 * mm], styles),
            Spacer(1, 3 * mm),
            Paragraph(
                "Note: automatic audit findings are not a count of all semantic errors. "
                "The initial 43 findings included 8 errors and 35 warnings.",
                styles["note"],
            ),
            PageBreak(),
            Paragraph("2. Cleanup actions", styles["h1"]),
        ]
    )

    cleanings = [
        "Split multi-word person names were merged into single spans.",
        "Incorrect labels were fixed, especially <b>COMPANY</b>, "
        "<b>AMOUNT/TIMEDATE</b>, and "
        "<b>PRODUCT/WORKOFART/ORGANIZATION</b> confusions.",
        "Extra words, punctuation, and possessive markers were removed from span boundaries.",
        "Missing entities were added; unsupported <b>JOB</b> labels on generic "
        "departments, teams, and fields were removed.",
        "Ten records were removed only from the processed data because severe OCR, "
        "encoding, or nonsensical text prevented reliable annotation.",
    ]
    story.extend(
        [Paragraph(f"• {item}", styles["bullet"]) for item in cleanings]
    )
    story.extend(
        [
            Spacer(1, 3 * mm),
            Paragraph("Cleanup result", styles["h1"]),
            make_cards(
                [
                    (str(summary["records_changed"]), "CHANGED"),
                    (str(summary["records_unchanged"]), "UNCHANGED"),
                    (str(summary["records_removed"]), "REMOVED"),
                    ("0", "STRUCTURAL ERRORS"),
                ],
                styles,
            ),
            Spacer(1, 4 * mm),
        ]
    )

    result_rows = [
        ["Check", "Result"],
        ["Raw data", "Unchanged and stored separately"],
        ["Processed data", "90 records in JSONL and Parquet"],
        ["Reproducibility", "Rebuilt from the correction manifest and script"],
        ["Remaining 17 warnings", "Reviewed across 12 records and accepted"],
        ["Manual QA", "All 90 retained records reviewed; queue retained locally"],
    ]
    story.extend(
        [
            make_table(result_rows, [58 * mm, 116 * mm], styles),
            Spacer(1, 4 * mm),
            Paragraph(
                "<b>Status:</b> Cleanup, second manual QA, and policy 1.0 are "
                "complete. Publishing the clean dataset in a separate public "
                "Hugging Face repository with the full dataset card remains.",
                styles["note"],
            ),
            Spacer(1, 2 * mm),
            Paragraph(
                "Source revision: "
                f"{summary['source_revision']}<br/>"
                "Removed record IDs: "
                + ", ".join(str(item) for item in summary["removed_ids"]),
                styles["small"],
            ),
        ]
    )

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    print(f"PDF created: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
