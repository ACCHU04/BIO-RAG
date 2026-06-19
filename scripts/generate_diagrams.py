"""
Generate professional diagrams for the BioRAG project report.
Outputs PNG files to report_output/diagrams/
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "report_output", "diagrams")
os.makedirs(OUT_DIR, exist_ok=True)

# ── Colour palette (matches BioRAG PDF theme) ──────────────────────────────
TEAL      = "#007a6e"
TEAL_L    = "#e0f4f1"
BLUE      = "#1a4f8c"
BLUE_L    = "#e8f0fb"
AMBER     = "#b8730a"
AMBER_L   = "#fef6e4"
RED       = "#c0392b"
RED_L     = "#fdf0ee"
GREEN     = "#166534"
GREEN_L   = "#dcfce7"
PURPLE    = "#534AB7"
PURPLE_L  = "#eeedfe"
INK       = "#0f0e0c"
INK2      = "#2a2825"
INK3      = "#5a5751"
INK4      = "#9a958e"
CREAM     = "#f7f4ef"
CREAM2    = "#efe9df"
WHITE     = "#ffffff"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 10,
    "axes.edgecolor": INK3,
    "axes.labelcolor": INK2,
    "text.color": INK2,
    "xtick.color": INK3,
    "ytick.color": INK3,
})


def _box(ax, x, y, w, h, text, color=TEAL, light=TEAL_L, text_color=INK2, fontsize=9):
    """Draw a rounded box with text centered."""
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                         facecolor=light, edgecolor=color, linewidth=1.5)
    ax.add_patch(box)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=text_color)


def _arrow(ax, x1, y1, x2, y2, color=INK3, lw=1.8):
    """Draw an arrow between two points."""
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw, shrinkA=4, shrinkB=4))


def _label(ax, x, y, text, color=INK4, fontsize=8):
    """Small label text."""
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize, color=color, style="italic")


# ── 1. System Architecture ─────────────────────────────────────────────────
def diagram_architecture():
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")

    # Title
    ax.text(5, 6.7, "BioRAG System Architecture", ha="center", va="center",
            fontsize=14, fontweight="bold", color=INK)

    # Layer 1: Frontend
    _box(ax, 3.5, 5.6, 3, 0.7, "React Frontend\n(Web UI)", BLUE, BLUE_L, fontsize=8)

    # Layer 2: API
    _box(ax, 3.5, 4.3, 3, 0.7, "FastAPI Backend\n(REST API :8742)", TEAL, TEAL_L, fontsize=8)
    _arrow(ax, 5, 5.6, 5, 5.0, BLUE)

    # Layer 3: Agent
    _box(ax, 3.5, 3.0, 3, 0.7, "LangGraph Agent\n(State Machine)", PURPLE, PURPLE_L, fontsize=8)
    _arrow(ax, 5, 4.3, 5, 3.7, TEAL)

    # Layer 4: Components split
    comps = [
        (0.3, 1.5, 2.8, 0.6, "ChromaDB\n(Vector Store)", GREEN, GREEN_L),
        (2.8, 1.5, 2.8, 0.6, "PubMedBERT\n(Embeddings)", BLUE, BLUE_L),
        (5.3, 1.5, 2.8, 0.6, "FlashRank\n(Reranker)", AMBER, AMBER_L),
        (7.8, 1.5, 2.0, 0.6, "Gemini\n(LLM)", PURPLE, PURPLE_L),
    ]
    for cx, cy, cw, ch, ct, cc, cl in comps:
        _box(ax, cx, cy, cw, ch, ct, cc, cl, fontsize=7)
        _arrow(ax, 5, 3.0, cx + cw/2, 2.15, INK3, 1.2)

    # Layer 5: APIs
    apis = [
        (0.3, 0.3, 2.3, 0.5, "PubMed\n(NCBI Entrez)", INK3, CREAM),
        (2.8, 0.3, 2.3, 0.5, "UniProt\n(REST API)", INK3, CREAM),
        (5.3, 0.3, 2.3, 0.5, "Open Targets\n(GraphQL)", INK3, CREAM),
        (7.8, 0.3, 2.0, 0.5, "Guardrails\n(Input+Output)", RED, RED_L),
    ]
    for cx, cy, cw, ch, ct, cc, cl in apis:
        _box(ax, cx, cy, cw, ch, ct, cc, cl, fontsize=7)
        _arrow(ax, cx + cw/2, 1.5, cx + cw/2, 0.8, INK3, 1.0)

    # Legend
    ax.text(0.3, 6.3, "Layers:", fontsize=8, fontweight="bold", color=INK3)
    _label(ax, 1.8, 6.5, "Frontend")
    _label(ax, 3.4, 6.5, "API Server")
    _label(ax, 5.0, 6.5, "Agent")
    _label(ax, 6.6, 6.5, "Core Components")
    _label(ax, 8.6, 6.5, "External / Security")

    path = os.path.join(OUT_DIR, "architecture.png")
    fig.savefig(path, dpi=180, bbox_inches="tight", pad_inches=0.3, facecolor=WHITE)
    plt.close(fig)
    print(f"  [OK] {path}")


# ── 2. RAG Pipeline Flowchart ──────────────────────────────────────────────
def diagram_pipeline():
    fig, ax = plt.subplots(figsize=(10, 9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9)
    ax.axis("off")

    ax.text(5, 8.7, "BioRAG Agentic RAG Pipeline", ha="center", va="center",
            fontsize=14, fontweight="bold", color=INK)

    # Define nodes: (x, y, w, h, text, color, light)
    nodes = [
        (3.5, 7.5, 3, 0.6, "User Query", BLUE, BLUE_L),
        (3.5, 6.3, 3, 0.6, "Input Guardrail\n(Injection + Scope Check)", RED, RED_L),
        (3.5, 5.1, 3, 0.6, "Vector Search (ChromaDB)\nTop 15 chunks", GREEN, GREEN_L),
        (3.5, 3.9, 3, 0.6, "FlashRank Cross-Encoder\nRerank → Top 5", AMBER, AMBER_L),
        (1.5, 2.7, 2.5, 0.6, "LLM Evaluation\nSufficient?", PURPLE, PURPLE_L),
        (5.5, 2.7, 3.0, 0.6, "Self-Correction\nRephrase & Re-retrieve", AMBER, AMBER_L),
        (1.5, 1.5, 2.5, 0.6, "Tool Calls\nPubMed/UniProt/OT", TEAL, TEAL_L),
        (5.5, 1.5, 3.0, 0.6, "Synthesize Answer\n(Gemini)", GREEN, GREEN_L),
        (3.5, 0.3, 3, 0.6, "Output Guardrail\n(Hallucination Check)", RED, RED_L),
    ]

    for nx, ny, nw, nh, nt, nc, nl in nodes:
        _box(ax, nx, ny, nw, nh, nt, nc, nl, fontsize=7)

    # Arrows
    _arrow(ax, 5, 7.5, 5, 6.9, INK3)
    _arrow(ax, 5, 6.3, 5, 5.7, INK3)
    _arrow(ax, 5, 5.1, 5, 4.5, INK3)
    _arrow(ax, 5, 3.9, 2.75, 3.3, INK3)
    _arrow(ax, 5.5, 3.0, 5.5, 3.3, INK3)  # self-correct arrow
    _arrow(ax, 4.0, 2.7, 4.0, 2.1, INK3)
    _arrow(ax, 7.0, 2.7, 7.0, 2.1, INK3)
    _arrow(ax, 2.75, 1.5, 4.0, 0.9, INK3)
    _arrow(ax, 7.0, 1.5, 5.0, 0.9, INK3)

    # Conditional labels
    ax.text(2.75, 3.15, " Yes", fontsize=7, color=GREEN, fontweight="bold")
    ax.text(5.5, 3.45, "No/Needs Tools", fontsize=7, color=AMBER, fontweight="bold")

    # Self-correction loop visual
    _arrow(ax, 7.0, 2.7, 7.5, 2.7, AMBER, 1.2)
    ax.text(7.7, 2.65, " Loop", fontsize=6, color=AMBER, fontweight="bold")
    _arrow(ax, 7.5, 2.7, 7.5, 3.9, AMBER, 1.2)
    _arrow(ax, 7.5, 3.9, 6.5, 3.9, AMBER, 1.2)

    # Failover annotation
    ax.annotate("", xy=(8, 0.3), xytext=(8, 0.9),
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.5, linestyle="dashed"))
    ax.text(8.3, 0.6, "API Failover\n→ Raw Evidence", fontsize=6, color=RED, fontweight="bold")

    path = os.path.join(OUT_DIR, "pipeline.png")
    fig.savefig(path, dpi=180, bbox_inches="tight", pad_inches=0.3, facecolor=WHITE)
    plt.close(fig)
    print(f"  [OK] {path}")


# ── 3. Input Guardrail Flow ────────────────────────────────────────────────
def diagram_input_guardrail():
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 6)
    ax.axis("off")

    ax.text(4.5, 5.7, "Input Guardrail — Decision Flow", ha="center", va="center",
            fontsize=13, fontweight="bold", color=INK)

    # Start
    _box(ax, 3, 4.6, 3, 0.5, "User Query Received", BLUE, BLUE_L, fontsize=8)

    # Checks (parallel style)
    checks = [
        (0.3, 3.3, 2.5, 0.5, "Length Check\n(5-2000 chars)", RED, RED_L),
        (3.3, 3.3, 2.5, 0.5, "Injection Detection\n(14 regex patterns)", RED, RED_L),
        (6.3, 3.3, 2.5, 0.5, "Out-of-Scope Check\n(5 categories)", RED, RED_L),
    ]
    for cx, cy, cw, ch, ct, cc, cl in checks:
        _box(ax, cx, cy, cw, ch, ct, cc, cl, fontsize=7)

    _arrow(ax, 4.5, 4.6, 1.55, 3.8, INK3, 1.0)
    _arrow(ax, 4.5, 4.6, 4.5, 3.8, INK3, 1.0)
    _arrow(ax, 4.5, 4.6, 7.55, 3.8, INK3, 1.0)

    # Decision
    _box(ax, 3, 2.2, 3, 0.6, "All Checks Passed?", PURPLE, PURPLE_L, fontsize=8)
    _arrow(ax, 1.55, 3.3, 3.0, 2.8, INK3, 1.0)
    _arrow(ax, 4.5, 3.3, 4.5, 2.8, INK3, 1.0)
    _arrow(ax, 7.55, 3.3, 6.0, 2.8, INK3, 1.0)

    # Yes / No
    _box(ax, 0.3, 1.0, 2.5, 0.6, "BLOCKED\nSafe rejection message", RED, RED_L, fontsize=7)
    _box(ax, 6.3, 1.0, 2.5, 0.6, "PASS\nProceed to Agent Pipeline", GREEN, GREEN_L, fontsize=7)

    ax.text(3.0, 2.0, "No", fontsize=8, color=RED, fontweight="bold")
    ax.text(6.0, 2.0, "Yes", fontsize=8, color=GREEN, fontweight="bold")

    _arrow(ax, 3, 2.2, 1.55, 1.6, RED, 1.2)
    _arrow(ax, 6, 2.2, 7.55, 1.6, GREEN, 1.2)

    path = os.path.join(OUT_DIR, "input_guardrail.png")
    fig.savefig(path, dpi=180, bbox_inches="tight", pad_inches=0.3, facecolor=WHITE)
    plt.close(fig)
    print(f"  [OK] {path}")


# ── 4. Output Guardrail Flow ───────────────────────────────────────────────
def diagram_output_guardrail():
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 5)
    ax.axis("off")

    ax.text(4.5, 4.7, "Output Guardrail — Hallucination Detection", ha="center", va="center",
            fontsize=13, fontweight="bold", color=INK)

    _box(ax, 0.3, 3.5, 2.8, 0.6, "LLM Answer\n+ Retrieved Context", BLUE, BLUE_L, fontsize=7)
    _box(ax, 3.3, 3.5, 2.5, 0.6, "Gemini-as-Judge\n(Hallucination Detector)", PURPLE, PURPLE_L, fontsize=7)
    _box(ax, 6.0, 3.5, 2.8, 0.6, "JSON Verdict\nGrounded + Claims List", AMBER, AMBER_L, fontsize=7)

    _arrow(ax, 3.1, 3.8, 3.3, 3.8, INK3)
    _arrow(ax, 5.8, 3.8, 6.0, 3.8, INK3)

    _box(ax, 0.3, 2.0, 2.8, 0.6, "PASS (OK)\nAnswer verified as grounded", GREEN, GREEN_L, fontsize=7)
    _box(ax, 3.3, 2.0, 2.5, 0.6, "PASS (WARN)\nLow confidence flag", AMBER, AMBER_L, fontsize=7)
    _box(ax, 6.0, 2.0, 2.8, 0.6, "WARN (Unverified)\nClaims listed, answer delivered", RED, RED_L, fontsize=7)

    _arrow(ax, 1.7, 3.5, 1.7, 2.6, GREEN, 1.0)
    _arrow(ax, 4.55, 3.5, 4.55, 2.6, AMBER, 1.0)
    _arrow(ax, 7.4, 3.5, 7.4, 2.6, RED, 1.0)

    _label(ax, 1.7, 3.1, "Grounded")
    _label(ax, 4.55, 3.1, "Low confidence")
    _label(ax, 7.4, 3.1, "Unverified claims")

    # Answer always delivered
    ax.text(4.5, 1.5, "Answer ALWAYS delivered to user — warning attached when needed",
            ha="center", va="center", fontsize=8, color=INK4, style="italic")

    path = os.path.join(OUT_DIR, "output_guardrail.png")
    fig.savefig(path, dpi=180, bbox_inches="tight", pad_inches=0.3, facecolor=WHITE)
    plt.close(fig)
    print(f"  [OK] {path}")


# ── 5. Failover Decision Flow ──────────────────────────────────────────────
def diagram_failover():
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 5.5)
    ax.axis("off")

    ax.text(4.5, 5.2, "Failover Mechanism — Graceful Degradation", ha="center", va="center",
            fontsize=13, fontweight="bold", color=INK)

    _box(ax, 3, 4.2, 3, 0.6, "Query Received", BLUE, BLUE_L, fontsize=8)

    _box(ax, 1, 3.0, 2.5, 0.6, "Try Agent Pipeline\n(with Gemini)", GREEN, GREEN_L, fontsize=7)
    _box(ax, 5.5, 3.0, 2.5, 0.6, "API Fails?\n(Timeout/Rate Limit/Auth)", RED, RED_L, fontsize=7)

    _arrow(ax, 4.5, 4.2, 4.5, 3.6, INK3)
    _arrow(ax, 4.5, 3.6, 3.5, 3.6, INK3)
    _arrow(ax, 3.5, 3.0, 5.5, 3.0, INK3)

    # Normal path
    _box(ax, 1, 1.8, 2.5, 0.6, "Full RAG Answer\n(Synthesized)", GREEN, GREEN_L, fontsize=7)
    _arrow(ax, 2.25, 3.0, 2.25, 2.4, GREEN, 1.2)

    # Failover path
    _box(ax, 5.5, 1.8, 2.5, 0.6, "Classify Error\n(5 failure types)", AMBER, AMBER_L, fontsize=7)
    _arrow(ax, 6.75, 3.0, 6.75, 2.4, RED, 1.2)

    _box(ax, 5.5, 0.6, 2.5, 0.6, "Raw Evidence Response\n(Chunks + PubMed)", AMBER, AMBER_L, fontsize=7)
    _arrow(ax, 6.75, 1.8, 6.75, 1.2, RED, 1.2)

    # Failure types annotation
    failures = ["Rate Limit", "Auth Error", "Timeout", "Service Unavailable", "Unknown"]
    ax.text(7.8, 3.3, "Failure Types:", fontsize=6, fontweight="bold", color=INK3)
    for i, f in enumerate(failures):
        ax.text(7.8, 2.9 - i*0.25, f"  • {f}", fontsize=6, color=INK4)

    # Never 500 guarantee
    ax.text(4.5, 0.2, "Guarantee: System NEVER returns HTTP 500 — always delivers a response",
            ha="center", va="center", fontsize=8, color=RED, fontweight="bold")

    path = os.path.join(OUT_DIR, "failover.png")
    fig.savefig(path, dpi=180, bbox_inches="tight", pad_inches=0.3, facecolor=WHITE)
    plt.close(fig)
    print(f"  [OK] {path}")


# ── 6. CRUD Operations ─────────────────────────────────────────────────────
def diagram_crud():
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 4.5)
    ax.axis("off")

    ax.text(4.5, 4.2, "Dynamic CRUD Operations — No Index Rebuild Required", ha="center", va="center",
            fontsize=12, fontweight="bold", color=INK)

    ops = [
        (0.3, 2.8, 2.0, 0.7, "CREATE\nUpload PDF/TXT\n→ Chunk → Embed\n→ Add to ChromaDB", GREEN, GREEN_L),
        (2.5, 2.8, 2.0, 0.7, "READ\nList Documents\nQuery metadata\nGroup by doc_id", BLUE, BLUE_L),
        (4.7, 2.8, 2.0, 0.7, "UPDATE\nDelete old chunks\nAdd new chunks\nSame doc_id", AMBER, AMBER_L),
        (6.9, 2.8, 2.0, 0.7, "DELETE\nMetadata filter\nRemove chunks\nPersist", RED, RED_L),
    ]
    for ox, oy, ow, oh, ot, oc, ol in ops:
        _box(ax, ox, oy, ow, oh, ot, oc, ol, fontsize=7)

    _label(ax, 1.3, 2.3, "POST /documents/upload")
    _label(ax, 3.5, 2.3, "GET /documents")
    _label(ax, 5.7, 2.3, "PUT /documents/{id}")
    _label(ax, 7.9, 2.3, "DELETE /documents/{id}")

    # Extra CRUD features
    features = [
        (0.3, 0.8, 4.0, 0.5, "Page-Level Deletion: Remove specific pages within a document", INK3, CREAM),
        (4.7, 0.8, 4.0, 0.5, "Targeted via metadata filters (doc_id + page_number)", INK3, CREAM),
    ]
    for fx, fy, fw, fh, ft, fc, fl in features:
        _box(ax, fx, fy, fw, fh, ft, fc, fl, fontsize=7)

    path = os.path.join(OUT_DIR, "crud.png")
    fig.savefig(path, dpi=180, bbox_inches="tight", pad_inches=0.3, facecolor=WHITE)
    plt.close(fig)
    print(f"  [OK] {path}")


# ── 7. RAGAS Evaluation Chart ──────────────────────────────────────────────
def diagram_evaluation():
    fig, ax = plt.subplots(figsize=(7, 4.5))

    metrics = ["Faithfulness", "Answer\nRelevancy", "Context\nRecall", "Context\nPrecision"]
    scores = [0.92, 0.85, 0.78, 0.81]
    colors = [TEAL, GREEN, BLUE, TEAL]

    bars = ax.bar(metrics, scores, color=colors, edgecolor=WHITE, linewidth=0.5, width=0.55)

    for bar, score in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f"{score:.0%}", ha="center", va="bottom", fontsize=11, fontweight="bold", color=INK2)

    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Score", fontsize=10, color=INK2)
    ax.set_title("RAGAS Evaluation Scores", fontsize=13, fontweight="bold", color=INK, pad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(colors=INK3, labelsize=9)
    ax.axhline(y=0.8, color=GREEN, linewidth=1, linestyle="--", alpha=0.6)
    ax.text(3.8, 0.81, "Target (80%)", fontsize=7, color=GREEN, fontweight="bold")

    fig.tight_layout()
    path = os.path.join(OUT_DIR, "evaluation.png")
    fig.savefig(path, dpi=180, bbox_inches="tight", pad_inches=0.3, facecolor=WHITE)
    plt.close(fig)
    print(f"  [OK] {path}")


# ── 8. Chunking Strategy ───────────────────────────────────────────────────
def diagram_chunking():
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.set_xlim(0, 9)
    ax.set_ylim(0, 3)
    ax.axis("off")

    ax.text(4.5, 2.7, "Document Chunking Strategy", ha="center", va="center",
            fontsize=13, fontweight="bold", color=INK)

    # Document bar
    ax.add_patch(FancyBboxPatch((0.3, 1.8), 8.4, 0.4, boxstyle="round,pad=0.05",
                                 facecolor=BLUE_L, edgecolor=BLUE, linewidth=1.5))
    ax.text(4.5, 2.0, "Full Document (PDF / TXT)", ha="center", va="center",
            fontsize=9, color=BLUE, fontweight="bold")

    # Splitter
    ax.add_patch(FancyBboxPatch((3.5, 1.2), 2, 0.35, boxstyle="round,pad=0.05",
                                 facecolor=PURPLE_L, edgecolor=PURPLE, linewidth=1.5))
    ax.text(4.5, 1.375, "RecursiveCharacterTextSplitter", ha="center", va="center",
            fontsize=7, color=PURPLE, fontweight="bold")
    _arrow(ax, 4.5, 1.8, 4.5, 1.55, INK3)

    # Chunks
    colors = [TEAL, GREEN, AMBER, BLUE, PURPLE]
    for i in range(5):
        x = 0.5 + i * 1.7
        ax.add_patch(FancyBboxPatch((x, 0.3), 1.4, 0.5, boxstyle="round,pad=0.05",
                                     facecolor=TEAL_L, edgecolor=colors[i], linewidth=1.5))
        ax.text(x + 0.7, 0.55, f"Chunk {i+1}", ha="center", va="center",
                fontsize=8, color=colors[i], fontweight="bold")
        ax.text(x + 0.7, 0.4, "512 tokens", ha="center", va="center",
                fontsize=6, color=INK4)

    # Overlap annotation
    for i in range(4):
        x = 1.2 + i * 1.7
        ax.annotate("", xy=(x + 1.1, 0.3), xytext=(x + 0.8, 0.3),
                    arrowprops=dict(arrowstyle="<->", color=AMBER, lw=1.2))
    ax.text(4.5, 0.15, "64-token overlap between chunks", ha="center", va="center",
            fontsize=7, color=AMBER, fontstyle="italic")

    _arrow(ax, 4.5, 1.2, 4.5, 0.8, INK3)

    path = os.path.join(OUT_DIR, "chunking.png")
    fig.savefig(path, dpi=180, bbox_inches="tight", pad_inches=0.3, facecolor=WHITE)
    plt.close(fig)
    print(f"  [OK] {path}")


# ── Generate All ───────────────────────────────────────────────────────────
def generate_all():
    print("Generating diagrams...")
    diagram_architecture()
    diagram_pipeline()
    diagram_input_guardrail()
    diagram_output_guardrail()
    diagram_failover()
    diagram_crud()
    diagram_evaluation()
    diagram_chunking()
    print("All diagrams generated successfully.")


if __name__ == "__main__":
    generate_all()
