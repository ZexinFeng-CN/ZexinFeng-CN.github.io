"""Render the three-domain temporal cosine figure from representation_diagnostics CSVs.

Usage: python3 plot.py DATA_ROOT OUTPUT.svg
"""
from __future__ import annotations

import csv
import html
import sys
from pathlib import Path

VARIANTS = (
    ("full", "Copper-Policy", "#1976bc", "circle", ""),
    ("no_future", "w/o JE Pred.", "#e46432", "square", "6 4"),
    ("no_vision", "w/o Current-Frame Visual", "#18a66b", "triangle", ""),
    ("no_future_no_vision", "w/o JE Pred. & Visual", "#df9400", "diamond", "6 4"),
)
DOMAINS = (
    ("libero", "LIBERO", 0.6, (0.6, 0.8, 1.0)),
    ("robotwin", "RoboTwin", 0.5, (0.5, 0.75, 1.0)),
    ("realbot", "Real robot", 0.7, (0.7, 0.85, 1.0)),
)
HORIZONS = (1, 2, 4, 8, 16)


def shape(x: float, y: float, kind: str, color: str) -> str:
    if kind == "circle":
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}" stroke="white" stroke-width="1"/>'
    if kind == "square":
        return f'<rect x="{x-3.5:.1f}" y="{y-3.5:.1f}" width="7" height="7" fill="{color}" stroke="white" stroke-width="1"/>'
    if kind == "triangle":
        points = f"{x:.1f},{y-4.5:.1f} {x-4.5:.1f},{y+3.5:.1f} {x+4.5:.1f},{y+3.5:.1f}"
        return f'<polygon points="{points}" fill="{color}" stroke="white" stroke-width="1"/>'
    points = f"{x:.1f},{y-4.5:.1f} {x-4.5:.1f},{y:.1f} {x:.1f},{y+4.5:.1f} {x+4.5:.1f},{y:.1f}"
    return f'<polygon points="{points}" fill="{color}" stroke="white" stroke-width="1"/>'


def main(data_root: Path, output: Path) -> None:
    chunks = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="338" viewBox="0 0 1120 338" role="img" aria-labelledby="title desc">',
        '<title id="title">Temporal coherence across LIBERO, RoboTwin, and the real robot</title>',
        '<desc id="desc">Episode-level mean cosine similarity across horizons 1, 2, 4, 8, and 16, with approximate 95 percent confidence intervals, for Copper-Policy and three ablations.</desc>',
        '<rect width="1120" height="338" fill="white"/>',
        '<g font-family="Inter, Arial, sans-serif" fill="#0f1720">',
    ]
    legend_x = (58, 284, 510, 780)
    for x, (_, label, color, kind, dash) in zip(legend_x, VARIANTS):
        chunks.append(f'<line x1="{x}" y1="22" x2="{x+30}" y2="22" stroke="{color}" stroke-width="2.4"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')
        chunks.append(shape(x+15, 22, kind, color))
        chunks.append(f'<text x="{x+40}" y="27" font-size="13" fill="#27323d">{html.escape(label)}</text>')
    chunks.append('<text x="18" y="173" transform="rotate(-90 18 173)" text-anchor="middle" font-size="13">Temporal cosine ↑</text>')
    for domain_index, (folder, label, ymin, ticks) in enumerate(DOMAINS):
        with (data_root / folder / "temporal_metrics.csv").open(newline="", encoding="utf-8") as source:
            rows = list(csv.DictReader(source))
        by_key = {(row["variant"], int(row["horizon"])): row for row in rows}
        expected = {(variant, horizon) for variant, *_ in VARIANTS for horizon in HORIZONS}
        if not expected.issubset(by_key):
            raise ValueError(f"Missing variant/horizon rows in {folder}/temporal_metrics.csv")
        n = int(by_key[("full", 1)]["episodes"])
        x0 = (58, 410, 762)[domain_index]
        x1 = x0 + 290
        y0, y1 = 78, 269
        xs = [x0 + i * (x1-x0) / 4 for i in range(5)]
        ypos = lambda value: y1 - (value-ymin) / (1-ymin) * (y1-y0)
        chunks.append(f'<text x="{(x0+x1)/2:.1f}" y="62" text-anchor="middle" font-size="18" font-weight="600">{label} <tspan font-size="13" font-weight="400" fill="#677480">(n={n})</tspan></text>')
        for tick in ticks:
            yy = ypos(tick)
            chunks.append(f'<line x1="{x0}" y1="{yy:.1f}" x2="{x1}" y2="{yy:.1f}" stroke="#e4e8ed" stroke-width="1"/>')
            chunks.append(f'<text x="{x0-9}" y="{yy+4:.1f}" text-anchor="end" font-size="11" fill="#667380">{tick:.2f}</text>')
        chunks.append(f'<path d="M{x0} {y0}V{y1}H{x1}" fill="none" stroke="#667380" stroke-width="1"/>')
        for x, horizon in zip(xs, HORIZONS):
            chunks.append(f'<text x="{x:.1f}" y="{y1+20}" text-anchor="middle" font-size="11" fill="#465462">{horizon}</text>')
        chunks.append(f'<text x="{(x0+x1)/2:.1f}" y="{y1+43}" text-anchor="middle" font-size="13">Horizon Δ</text>')
        for variant, _, color, kind, dash in VARIANTS:
            values = [float(by_key[(variant, horizon)]["cosine_mean"]) for horizon in HORIZONS]
            cis = [float(by_key[(variant, horizon)]["cosine_ci95"]) for horizon in HORIZONS]
            points = " ".join(f"{x:.1f},{ypos(v):.1f}" for x, v in zip(xs, values))
            chunks.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"' + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')
            for x, value, ci in zip(xs, values, cis):
                top, bottom = ypos(value+ci), ypos(value-ci)
                chunks.append(f'<path d="M{x:.1f} {top:.1f}V{bottom:.1f}m-3 0h6m-6 {top-bottom:.1f}h6" fill="none" stroke="{color}" stroke-width="1" opacity=".75"/>')
                chunks.append(shape(x, ypos(value), kind, color))
    chunks.append('</g></svg>')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(chunks), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
