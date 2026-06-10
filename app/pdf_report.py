"""
pdf_report.py — BioRAG PDF Report Generator
Generates a polished multi-page PDF from real query result data using ReportLab.
Returns bytes (io.BytesIO) — no disk write.
"""

import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)

W, H = A4

# ── Palette ───────────────────────────────────────────────────────────────────
INK       = colors.HexColor("#0f0e0c")
INK2      = colors.HexColor("#2a2825")
INK3      = colors.HexColor("#5a5751")
INK4      = colors.HexColor("#9a958e")
TEAL      = colors.HexColor("#007a6e")
TEAL_L    = colors.HexColor("#e0f4f1")
BLUE      = colors.HexColor("#1a4f8c")
BLUE_L    = colors.HexColor("#e8f0fb")
AMBER     = colors.HexColor("#b8730a")
AMBER_L   = colors.HexColor("#fef6e4")
RED       = colors.HexColor("#c0392b")
RED_L     = colors.HexColor("#fdf0ee")
GREEN     = colors.HexColor("#166534")
GREEN_L   = colors.HexColor("#dcfce7")
PURPLE    = colors.HexColor("#534AB7")
PURPLE_L  = colors.HexColor("#EEEDFE")
CREAM     = colors.HexColor("#f7f4ef")
CREAM2    = colors.HexColor("#efe9df")
BORDER    = colors.HexColor("#d8d2c8")
WHITE     = colors.white


# ── Styles ────────────────────────────────────────────────────────────────────
def S(name, **kw):
    defaults = dict(fontName="Helvetica", fontSize=11, leading=16,
                    textColor=INK2, spaceAfter=0, spaceBefore=0)
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

STYLES = {
    "h1":        S("h1",  fontName="Helvetica-Bold", fontSize=26, leading=32, textColor=INK, spaceAfter=4),
    "h2":        S("h2",  fontName="Helvetica-Bold", fontSize=16, leading=22, textColor=INK, spaceAfter=6),
    "h3":        S("h3",  fontName="Helvetica-Bold", fontSize=12, leading=17, textColor=INK2, spaceAfter=4),
    "label":     S("label", fontName="Helvetica-Bold", fontSize=8,  leading=11, textColor=TEAL, spaceAfter=6, letterSpacing=1.0),
    "body":      S("body",  fontSize=11, leading=18, textColor=INK2, spaceAfter=6, alignment=TA_JUSTIFY),
    "small":     S("small", fontSize=9,  leading=14, textColor=INK4),
    "mono":      S("mono",  fontName="Courier", fontSize=9, leading=14, textColor=INK3),
    "mono_hl":   S("mono_hl",  fontName="Courier", fontSize=9, leading=14, textColor=GREEN),
    "mono_warn": S("mono_warn", fontName="Courier", fontSize=9, leading=14, textColor=AMBER),
    "center":    S("center",    fontSize=11, leading=17, textColor=INK3, alignment=TA_CENTER),
    "cover_sub": S("cover_sub", fontSize=13, leading=20, textColor=INK3, alignment=TA_CENTER),
    "answer":    S("answer",    fontSize=11, leading=19, textColor=INK2, spaceAfter=8, alignment=TA_JUSTIFY),
}


# ── Header / footer ───────────────────────────────────────────────────────────
def _hf(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    if doc.page > 1:
        canvas.line(15*mm, H - 14*mm, W - 15*mm, H - 14*mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(INK4)
        canvas.drawString(15*mm, H - 11*mm, "BioRAG v2.0  —  Query Report  |  Gemini Integration")
        canvas.drawRightString(W - 15*mm, H - 11*mm, f"Page {doc.page}")
    canvas.line(15*mm, 12*mm, W - 15*mm, 12*mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(INK4)
    canvas.drawString(15*mm, 8*mm, "PG Final Project  ·  Data Science & Bioinformatics  ·  Agentic RAG Pipeline")
    canvas.drawRightString(W - 15*mm, 8*mm, datetime.now().strftime("%B %Y"))
    canvas.restoreState()


# ── Helper builders ────────────────────────────────────────────────────────────
def _section_label(text):
    return [
        Spacer(1, 3*mm),
        Paragraph(text.upper(), STYLES["label"]),
        HRFlowable(width="100%", thickness=0.5, color=BORDER),
        Spacer(1, 3*mm),
    ]


def _colored_band(text, fg, bg, left_accent=None):
    style = ParagraphStyle("band", fontName="Helvetica-Bold", fontSize=10,
                           leading=14, textColor=fg)
    data = [[Paragraph(text, style)]]
    t = Table(data, colWidths=[W - 36*mm])
    ts_cmds = [
        ("BACKGROUND",    (0, 0), (-1, -1), bg),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 0.5, fg),
    ]
    if left_accent:
        ts_cmds.append(("LINEBEFORE", (0, 0), (0, -1), 3, left_accent))
    t.setStyle(TableStyle(ts_cmds))
    return t


def _metric_row(metrics):
    data = [
        [Paragraph(v, ParagraphStyle("mv", fontName="Helvetica-Bold",
                   fontSize=20, leading=24, textColor=c)) for v, l, c in metrics],
        [Paragraph(l, ParagraphStyle("ml", fontName="Helvetica",
                   fontSize=9, leading=12, textColor=INK4)) for v, l, c in metrics],
    ]
    t = Table(data, colWidths=[W / 4 - 9*mm] * len(metrics))
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), CREAM),
        ("TOPPADDING",    (0, 0), (-1, 0),  10),
        ("BOTTOMPADDING", (0, 0), (-1, 0),  4),
        ("TOPPADDING",    (0, 1), (-1, 1),  0),
        ("BOTTOMPADDING", (0, 1), (-1, 1),  10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEBEFORE",    (1, 0), (-1, -1), 0.5, BORDER),
    ]))
    return t


def _log_block(lines):
    """Render a terminal-style log block. lines = list of (text, kind) where kind in '', 'hl', 'wn'."""
    items = []
    for line, kind in lines:
        if kind == "hl":
            st = STYLES["mono_hl"]
        elif kind == "wn":
            st = STYLES["mono_warn"]
        else:
            st = STYLES["mono"]
        items.append(Paragraph(f"› {line}", st))

    t = Table([[i] for i in items], colWidths=[W - 36*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), INK),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 0.5, INK2),
    ]))
    for i, (_, kind) in enumerate(lines):
        if kind == "hl":
            t.setStyle(TableStyle([("TEXTCOLOR", (0, i), (0, i), colors.HexColor("#4dcc8a"))]))
        elif kind == "wn":
            t.setStyle(TableStyle([("TEXTCOLOR", (0, i), (0, i), colors.HexColor("#fbbf24"))]))
        else:
            t.setStyle(TableStyle([("TEXTCOLOR", (0, i), (0, i), colors.HexColor("#8a9ab8"))]))
    return t


def _ragas_bar(label, pct, color):
    bar_full  = W - 36*mm - 52*mm - 20*mm
    filled_pt = int(bar_full * pct / 100)
    empty_pt  = int(bar_full) - filled_pt

    lbl = Paragraph(label, ParagraphStyle("rl", fontName="Helvetica",
                    fontSize=10, leading=14, textColor=INK3))
    val = Paragraph(
        f"<font color='#{color.hexval()[2:]}'><b>{pct}%</b></font>",
        ParagraphStyle("rv", fontName="Helvetica-Bold", fontSize=11, leading=14),
    )

    fill_t = Table([[""]], colWidths=[filled_pt if filled_pt > 0 else 0.1], rowHeights=[6])
    fill_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), color),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))

    row = Table([[lbl, fill_t, val]], colWidths=[52*mm, bar_full, 18*mm])
    row.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("LINEBELOW",     (0, 0), (-1, 0),  0.5, CREAM2),
    ]))
    return row


def _pills_row(pills):
    """pills = list of (text, fg_color, bg_color)"""
    cells = [
        Paragraph(text, ParagraphStyle("p", fontName="Helvetica-Bold",
                  fontSize=8, leading=11, textColor=fg))
        for text, fg, _ in pills
    ]
    t = Table([cells], colWidths=[40*mm] * len(pills))
    style_cmds = [
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEBEFORE",    (1, 0), (-1, -1), 0.5, BORDER),
    ]
    for i, (_, _, bg) in enumerate(pills):
        style_cmds.append(("BACKGROUND", (i, 0), (i, 0), bg))
    t.setStyle(TableStyle(style_cmds))
    return t


def _reasoning_block(steps):
    """steps = list of strings (reasoning_steps from agent)."""
    story = []
    for i, step in enumerate(steps):
        num_p   = Paragraph(str(i + 1), ParagraphStyle(
            "tn", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=TEAL))
        step_p  = Paragraph(step, ParagraphStyle(
            "td", fontName="Helvetica", fontSize=10, leading=15, textColor=INK3))

        inner = Table([[step_p]], colWidths=[W - 36*mm - 22*mm])
        inner.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
        outer = Table([[num_p, inner]], colWidths=[18*mm, W - 36*mm - 20*mm])
        outer.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING",   (0, 0), (0, -1), 0),
            ("RIGHTPADDING",  (0, 0), (0, -1), 4),
            ("LEFTPADDING",   (1, 0), (1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        story += [outer, Spacer(1, 8),
                  HRFlowable(width="100%", thickness=0.5, color=CREAM2),
                  Spacer(1, 6)]
    return story


# ── Main public function ──────────────────────────────────────────────────────
def generate_pdf_report(data: dict) -> bytes:
    """
    Build and return a PDF report as raw bytes.

    Expected keys in `data`:
        query               str
        answer              str
        sources             list[str]
        reasoning_steps     list[str] | None
        self_corrections    int
        pubmed_articles_used int
        local_docs_used     int
        latency_seconds     float
        fallback            bool
        blocked             bool
        guardrail_warning   str | None
        ragas_scores        dict | None  — keys: faithfulness, answer_relevancy,
                                                  context_recall, context_precision
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=22*mm, bottomMargin=22*mm,
    )
    story = []

    query            = data.get("query", "—")
    answer           = data.get("answer", "No answer returned.")
    sources          = data.get("sources") or []
    steps            = data.get("reasoning_steps") or []
    self_corr        = data.get("self_corrections", 0)
    pubmed_used      = data.get("pubmed_articles_used", 0)
    local_used       = data.get("local_docs_used", 0)
    latency          = data.get("latency_seconds", 0)
    fallback         = data.get("fallback", False)
    blocked          = data.get("blocked", False)
    gw               = data.get("guardrail_warning")
    ragas            = data.get("ragas_scores") or {}

    # ── Cover ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 28*mm))
    story.append(Paragraph("BioRAG", STYLES["h1"]))
    story.append(Paragraph("Query Report — Full Pipeline Output", STYLES["cover_sub"]))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="35%", thickness=1.5, color=TEAL, hAlign="LEFT"))
    story.append(Spacer(1, 8*mm))

    status_txt = "Blocked" if blocked else ("Failover" if fallback else "Completed")
    cover_meta = [
        ["LLM Backend",    "Google Gemini"],
        ["Agent Framework","LangGraph (ReAct loop)"],
        ["Vector Store",   "ChromaDB + PubMedBERT embeddings"],
        ["Reranker",       "FlashRank cross-encoder (ms-marco-MiniLM-L-12-v2)"],
        ["External APIs",  "PubMed Entrez  ·  UniProt REST  ·  Open Targets GraphQL"],
        ["Guardrails",     "Input injection check  +  Output hallucination verifier"],
        ["Status",         status_txt],
        ["Generated",      datetime.now().strftime("%B %d, %Y  ·  %H:%M")],
    ]
    ct = Table(cover_meta, colWidths=[52*mm, 108*mm])
    ct.setStyle(TableStyle([
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",      (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 0), (-1, -1), 10),
        ("TEXTCOLOR",     (0, 0), (0, -1), INK4),
        ("TEXTCOLOR",     (1, 0), (1, -1), INK2),
        ("ROWBACKGROUNDS",(0, 0), (-1, -1), [CREAM, WHITE]),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEBELOW",     (0, 0), (-1, -2), 0.5, CREAM2),
    ]))
    story.append(ct)
    story.append(PageBreak())

    # ── Query + metrics ───────────────────────────────────────────────────────
    story += _section_label("Query")
    story.append(_colored_band(f'"{query}"', BLUE, BLUE_L, left_accent=BLUE))
    story.append(Spacer(1, 6*mm))

    story += _section_label("Pipeline run metrics")
    story.append(_metric_row([
        (f"{latency}s",   "Total latency",      TEAL),
        (str(self_corr),  "Self-corrections",   AMBER if self_corr > 0 else INK3),
        (str(pubmed_used),"PubMed articles",    BLUE),
        (str(local_used), "Local chunks used",  INK3),
    ]))
    story.append(Spacer(1, 3*mm))

    pills = []
    if blocked:
        pills.append(("Blocked",       RED,    RED_L))
    elif fallback:
        pills.append(("Failover mode", AMBER,  AMBER_L))
    else:
        pills.append(("Completed",     GREEN,  GREEN_L))

    if gw:
        pills.append(("Guardrail warn", AMBER, AMBER_L))
    else:
        pills.append(("Grounded output", TEAL, TEAL_L))

    if self_corr > 0:
        pills.append((f"{self_corr} self-correction{'s' if self_corr>1 else ''}", AMBER, AMBER_L))
    pills.append(("Gemini backend", PURPLE, PURPLE_L))

    story.append(_pills_row(pills))
    story.append(PageBreak())

    # ── Answer ────────────────────────────────────────────────────────────────
    story += _section_label("Agent answer")

    if gw:
        story.append(Paragraph(f"⚠ Guardrail warning: {gw}",
                               ParagraphStyle("gw_warn", fontName="Helvetica-Bold",
                                              fontSize=10, leading=14, textColor=AMBER,
                                              backColor=AMBER_L, leftIndent=6)))
        story.append(Spacer(1, 4*mm))

    # Render each paragraph of the answer
    for line in answer.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 2*mm))
            continue
        if line.startswith("### "):
            story.append(Paragraph(line.replace("### ", ""), STYLES["h3"]))
        elif "**" in line:
            html = []
            in_bold = False
            for seg in line.split("**"):
                if not seg:
                    in_bold = not in_bold
                    continue
                if in_bold:
                    html.append(f"<b>{seg}</b>")
                else:
                    html.append(seg)
                in_bold = not in_bold
            story.append(Paragraph(
                "".join(html),
                ParagraphStyle("bold_inline", fontName="Helvetica",
                               fontSize=11, leading=16, textColor=INK2)
            ))
        elif line.startswith("• ") or line.startswith("- "):
            body = line[2:]
            story.append(Paragraph(
                f"• {body}",
                ParagraphStyle("bullet", fontName="Helvetica", fontSize=10,
                               leading=16, textColor=INK2, leftIndent=8,
                               spaceAfter=3, alignment=TA_JUSTIFY)
            ))
        else:
            story.append(Paragraph(line, STYLES["answer"]))

    story.append(Spacer(1, 4*mm))

    # ── Sources ───────────────────────────────────────────────────────────────
    if sources:
        story += _section_label("Sources cited")
        for src in sources:
            if isinstance(src, dict):
                title = src.get("title", "")[:60]
                url   = src.get("url", "")
                snipped = src.get("snippet", "")
            else:
                title = str(src)[:60]
                url   = str(src)
                snipped = ""
            display = title or url[:60]
            sid_p  = Paragraph(display, ParagraphStyle(
                "sid", fontName="Helvetica-Bold", fontSize=9,
                leading=13, textColor=TEAL))
            surl_p = Paragraph(url or snipped, ParagraphStyle(
                "surl", fontName="Helvetica", fontSize=8,
                leading=12, textColor=BLUE))
            row_t = Table([[sid_p, surl_p]],
                          colWidths=[40*mm, W - 36*mm - 42*mm])
            row_t.setStyle(TableStyle([
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",    (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ]))
            story.append(row_t)
            story.append(HRFlowable(width="100%", thickness=0.5, color=CREAM2))
            story.append(Spacer(1, 3*mm))
        story.append(PageBreak())

    # ── Reasoning trace ───────────────────────────────────────────────────────
    if steps:
        story += _section_label("Agent reasoning trace")
        story += _reasoning_block(steps)
        story.append(PageBreak())

    # ── RAGAS scores ──────────────────────────────────────────────────────────
    if ragas:
        story += _section_label("RAGAS evaluation scores")
        story.append(Paragraph(
            "RAGAS scores computed for this query/answer pair using retrieved chunks as context.",
            STYLES["body"]
        ))
        story.append(Spacer(1, 3*mm))

        ragas_display = [
            ("Faithfulness",      int(ragas.get("faithfulness", 0) * 100),      TEAL),
            ("Answer Relevancy",  int(ragas.get("answer_relevancy", 0) * 100),  GREEN),
            ("Context Recall",    int(ragas.get("context_recall", 0) * 100),    BLUE),
            ("Context Precision", int(ragas.get("context_precision", 0) * 100), TEAL),
        ]

        descs = [
            "Answer claims are verifiable in retrieved context",
            "Response directly addresses the query asked",
            "Relevant evidence was successfully retrieved",
            "Retrieved chunks were focused and low-noise",
        ]

        for (label, pct, color), desc in zip(ragas_display, descs):
            story.append(_ragas_bar(label, pct, color))
            story.append(Paragraph(desc, ParagraphStyle(
                "rd", fontName="Helvetica", fontSize=9, leading=13,
                textColor=INK4, leftIndent=4, spaceAfter=4)))

        story.append(Spacer(1, 5*mm))
        avg = round(sum(p for _, p, _ in ragas_display) / len(ragas_display))
        avg_color = GREEN if avg >= 80 else AMBER if avg >= 60 else RED
        avg_data = [[
            Paragraph("Overall RAGAS score", ParagraphStyle(
                "ol", fontName="Helvetica", fontSize=11, leading=14, textColor=INK3)),
            Paragraph(
                f"<font color='#{avg_color.hexval()[2:]}'><b>{avg}%</b></font>",
                ParagraphStyle("ov", fontName="Helvetica-Bold", fontSize=22,
                               leading=26, alignment=TA_CENTER)),
            Paragraph(
                "Excellent" if avg >= 80 else "Good" if avg >= 60 else "Needs work",
                ParagraphStyle("og", fontName="Helvetica-Bold", fontSize=10,
                               leading=14, textColor=avg_color, alignment=TA_CENTER)),
        ]]
        avg_t = Table(avg_data, colWidths=[70*mm, 40*mm, 50*mm])
        avg_t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), CREAM),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING",   (0, 0), (-1, -1), 12),
            ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
            ("LINEBEFORE",    (1, 0), (-1, -1), 0.5, BORDER),
        ]))
        story.append(avg_t)

    # ── Footer note ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        "Generated by BioRAG v2.0 with Gemini as the LLM backend. "
        "To reproduce: set GEMINI_API_KEY in .env and POST to /query.",
        STYLES["small"]
    ))

    doc.build(story, onFirstPage=_hf, onLaterPages=_hf)
    buf.seek(0)
    return buf.read()
