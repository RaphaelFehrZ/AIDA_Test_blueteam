"""
LaTeX / CSV export service for assessment findings.

Produces a set of files compatible with the
template-security-code-review report template:
  findings/<id>-<slug>/final.tex
  findings-collected-fa.tex
"""
from __future__ import annotations

import csv
import io
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# Severity mapping
# ---------------------------------------------------------------------------

# CRITICAL is folded into HIGH (template has only High/Medium/Low/Info buckets)
SEVERITY_BUCKETS = {
    "CRITICAL": "HIGH",
    "HIGH": "HIGH",
    "MEDIUM": "MEDIUM",
    "LOW": "LOW",
    "INFO": "INFO",
}

# bucket -> (env, counter, lst_style, letter, sort_key)
SEVERITY_MAP = {
    "HIGH":   ("finding1", "fcOne",   "myStyleH", "H", 0),
    "MEDIUM": ("finding2", "fcTwo",   "myStyleM", "M", 1),
    "LOW":    ("finding3", "fcThree", "myStyleL", "L", 2),
    "INFO":   ("finding4", "fcFour",  "myStyleH", "I", 3),
}


def _bucket_for(severity: str | None) -> str:
    if not severity:
        return "INFO"
    return SEVERITY_BUCKETS.get(severity.upper(), "INFO")


# ---------------------------------------------------------------------------
# Escaping / slugifying
# ---------------------------------------------------------------------------

# Order matters: backslash is processed first via a sentinel so that the
# "{}" we emit for \textbackslash{} doesn't get re-escaped by the {/} rules.
_BACKSLASH_SENTINEL = "\x00BSL\x00"

_LATEX_SPECIAL_MAP = [
    ("&", r"\&"),
    ("%", r"\%"),
    ("$", r"\$"),
    ("#", r"\#"),
    ("_", r"\_"),
    ("{", r"\{"),
    ("}", r"\}"),
    ("~", r"\textasciitilde{}"),
    ("^", r"\textasciicircum{}"),
]


def escape_latex(text: str | None) -> str:
    """Escape LaTeX special characters in prose fields.

    Do NOT apply inside lstlisting blocks — evidence should be verbatim.
    """
    if text is None:
        return ""
    out = text.replace("\\", _BACKSLASH_SENTINEL)
    for needle, repl in _LATEX_SPECIAL_MAP:
        out = out.replace(needle, repl)
    return out.replace(_BACKSLASH_SENTINEL, r"\textbackslash{}")


def slugify(text: str, fallback: str = "finding") -> str:
    """Turn a title into a filesystem-safe slug (ascii, kebab-case)."""
    if not text:
        return fallback
    normalized = unicodedata.normalize("NFKD", text)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
    slug = re.sub(r"-+", "-", slug)
    return slug or fallback


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

@dataclass
class RenderedFinding:
    id_lower: str   # e.g. "fh01"
    id_upper: str   # e.g. "FH01"
    slug: str
    severity_bucket: str
    relative_dir: str   # "findings/fh01-stored-xss"
    final_tex_path: str  # "findings/fh01-stored-xss/final.tex"
    final_tex_content: str


def _split_bullet_lines(text: str | None) -> List[str]:
    """Split a free-text field into a list of bullets.

    Rules: lines that begin with '-', '*', '•' are treated as bullets with the
    marker stripped; otherwise non-empty lines become separate bullets.
    """
    if not text:
        return []
    items: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^[-*\u2022]\s*", "", line)
        items.append(line)
    return items


def _fmt_itemize(lines: Sequence[str]) -> str:
    if not lines:
        return "  \\item ~"
    return "\n".join(f"  \\item {escape_latex(line)}" for line in lines)


def _summary_and_body(card) -> Tuple[str, str]:
    """Pick the one-paragraph summary and multi-paragraph body.

    - Summary: first non-empty paragraph of technical_analysis, else notes, else title.
    - Body: remaining paragraphs of technical_analysis + notes (if not already used).
    """
    analysis = (card.technical_analysis or "").strip()
    notes = (card.notes or "").strip()

    paragraphs: List[str] = []
    if analysis:
        paragraphs.extend(p.strip() for p in re.split(r"\n\s*\n", analysis) if p.strip())
    if notes:
        paragraphs.extend(p.strip() for p in re.split(r"\n\s*\n", notes) if p.strip())

    if not paragraphs:
        summary = (card.title or "Finding").strip()
        body = ""
    else:
        summary = paragraphs[0]
        body_parts = paragraphs[1:]
        body = "\n\n".join(body_parts)
    return summary, body


def render_finding(
    card,
    id_upper: str,
    added_date: str | None = None,
) -> RenderedFinding:
    """Render a single Card into the report's finding skeleton."""
    bucket = _bucket_for(card.severity)
    env, counter, lst_style, letter, _ = SEVERITY_MAP[bucket]

    title = (card.title or "Untitled Finding").strip()
    slug = slugify(title)
    id_lower = id_upper.lower()

    summary, body = _summary_and_body(card)
    evidence = (card.proof or card.context or "").rstrip()
    risks = _split_bullet_lines(getattr(card, "risks", None)) or _split_bullet_lines(card.context)
    recs = _split_bullet_lines(getattr(card, "recommendations", None))

    # If no dedicated risks/recs fields exist on the model, fall back gracefully
    if not risks:
        risks = ["Risk not documented."]
    if not recs:
        recs = ["Recommendation not documented."]

    added = added_date or (card.created_at.date().isoformat()
                           if getattr(card, "created_at", None) else date.today().isoformat())

    body_block = ""
    if body:
        # Escape the body as prose
        escaped_body = "\n\n".join(escape_latex(p) for p in re.split(r"\n\s*\n", body) if p.strip())
        body_block = f"\n{escaped_body}\n"

    lst_header = f"\\begin{{lstlisting}}[style={lst_style}]" if lst_style else "\\begin{lstlisting}"

    content = (
        f"\\begin{{{env}}}[{escape_latex(title)}]\n"
        f"  \\label{{fnd:{id_lower}:{slug}}}\n"
        f"  {escape_latex(summary)}\n"
        f"  \\flabel{{{id_upper}}}\n"
        f"  \\fadded{{{added}}}\n"
        f"\\end{{{env}}}\n"
        f"\\stepcounter{{{counter}}}\n"
        f"{body_block}\n"
        f"\\evidence\n\n"
        f"{lst_header}\n"
        f"{evidence}\n"
        f"\\end{{lstlisting}}\n\n"
        f"\\risks\n"
        f"\\begin{{itemize}}\n"
        f"{_fmt_itemize(risks)}\n"
        f"\\end{{itemize}}\n\n"
        f"\\recommendations\n"
        f"\\begin{{itemize}}\n"
        f"{_fmt_itemize(recs)}\n"
        f"\\end{{itemize}}\n"
    )

    rel_dir = f"findings/{id_lower}-{slug}"
    return RenderedFinding(
        id_lower=id_lower,
        id_upper=id_upper,
        slug=slug,
        severity_bucket=bucket,
        relative_dir=rel_dir,
        final_tex_path=f"{rel_dir}/final.tex",
        final_tex_content=content,
    )


def render_collected(findings: Sequence[RenderedFinding]) -> str:
    """Render findings-collected-fa.tex in severity order (High→Info)."""
    lines = []
    for f in findings:
        lines.append(f"\\input{{../{f.relative_dir}/final.tex}} \\newpage")
    return "\n".join(lines) + ("\n" if lines else "")


def build_latex_bundle(cards: Iterable) -> List[Tuple[str, str]]:
    """Build the list of (path, content) pairs for a ZIP bundle.

    Only cards with card_type == 'finding' are included.
    """
    # Keep findings only, group by severity bucket, then number per bucket
    findings_cards = [c for c in cards if (c.card_type or "").lower() == "finding"]

    bucketed: dict[str, list] = {"HIGH": [], "MEDIUM": [], "LOW": [], "INFO": []}
    for c in findings_cards:
        bucketed[_bucket_for(c.severity)].append(c)

    rendered: List[RenderedFinding] = []
    for bucket in ("HIGH", "MEDIUM", "LOW", "INFO"):
        letter = SEVERITY_MAP[bucket][3]
        # Sort inside bucket by cvss_score desc then created_at asc for stability
        bucket_cards = sorted(
            bucketed[bucket],
            key=lambda c: (
                -(c.cvss_score or 0.0),
                getattr(c, "created_at", None) or 0,
            ),
        )
        for idx, card in enumerate(bucket_cards, start=1):
            id_upper = f"F{letter}{idx:02d}"
            rendered.append(render_finding(card, id_upper))

    files: List[Tuple[str, str]] = []
    for f in rendered:
        files.append((f.final_tex_path, f.final_tex_content))
    files.append(("findings-collected-fa.tex", render_collected(rendered)))
    return files


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------

CSV_COLUMNS = [
    "id",
    "card_type",
    "section_number",
    "title",
    "severity",
    "status",
    "cvss_score",
    "cvss_vector",
    "target_service",
    "technical_analysis",
    "proof",
    "context",
    "notes",
    "flag",
    "flag_status",
    "points",
    "challenge_category",
    "created_at",
    "updated_at",
]


def build_csv(cards: Iterable) -> str:
    """Render all cards as a CSV string."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for c in cards:
        row = {col: getattr(c, col, None) for col in CSV_COLUMNS}
        # Normalize datetimes
        for key in ("created_at", "updated_at"):
            v = row.get(key)
            if v is not None and hasattr(v, "isoformat"):
                row[key] = v.isoformat()
        writer.writerow(row)
    return buf.getvalue()
