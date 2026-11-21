"""Создаёт architecture.png по узлам из architecture.drawio.

Для самостоятельного пересоздания: python tools/render_architecture.py
"""

from pathlib import Path
from xml.etree import ElementTree as ET

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
TREE = ET.parse(ROOT / "architecture.drawio")
CELLS = {cell.get("id"): cell for cell in TREE.findall(".//mxCell")}

COLORS = {
    "source": ("#DBEAFE", "#2563EB", "#1E3A8A"),
    "broker": ("#DBEAFE", "#2563EB", "#1E3A8A"),
    "processor": ("#EDE9FE", "#7C3AED", "#5B21B6"),
    "raw": ("#CFFAFE", "#0891B2", "#155E75"),
    "batch": ("#DCFCE7", "#16A34A", "#166534"),
    "daily": ("#FFEDD5", "#EA580C", "#9A3412"),
    "live": ("#CFFAFE", "#0891B2", "#155E75"),
    "monitor": ("#FFEDD5", "#EA580C", "#9A3412"),
    "errors": ("#FEE2E2", "#DC2626", "#991B1B"),
}


def geom(cell_id):
    g = CELLS[cell_id].find("mxGeometry")
    return tuple(float(g.get(item)) for item in ("x", "y", "width", "height"))


def value(cell_id):
    return CELLS[cell_id].get("value", "")


fig, ax = plt.subplots(figsize=(18, 8.15), dpi=140)
fig.patch.set_facecolor("white")
ax.set_xlim(0, 1710)
ax.set_ylim(775, 0)
ax.axis("off")


def label(x, y, text, *, size=11, color="#334155", weight="normal",
          ha="center", va="center", zorder=5):
    ax.text(x, y, text, ha=ha, va=va, fontsize=size,
            family="DejaVu Sans", color=color, weight=weight, zorder=zorder)


def arrow(points, *, color="#64748B", text="", text_pos=None, size=9.5):
    for p1, p2 in zip(points, points[1:]):
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=color,
                lw=2.2, solid_capstyle="round", zorder=1)
    ax.add_patch(FancyArrowPatch(points[-2], points[-1], arrowstyle="-|>",
                                 mutation_scale=19, lw=0, color=color, zorder=2))
    if text and text_pos:
        label(*text_pos, text, size=size, color=color, weight="bold")


label(45, 45, value("title"), size=20.5, weight="bold", color="#172554", ha="left")
label(47, 91, value("subtitle"), size=11.5, color="#475569", ha="left")

# Draw arrows first so that their endings are visually tucked under the cards.
arrow([(245, 297.5), (305, 297.5)], text=value("e1"), text_pos=(275, 220), size=8.2)
arrow([(525, 297.5), (595, 297.5)], text=value("e2"), text_pos=(560, 220), size=8.4)
arrow([(815, 297.5), (900, 297.5)], text=value("e3"), text_pos=(860, 220), size=8.4)
arrow([(1005, 250), (1005, 172), (1185, 172)], color="#16A34A",
      text=value("e4"), text_pos=(1070, 140), size=8.2)
arrow([(1395, 167.5), (1460, 167.5)], color="#16A34A",
      text=value("e5"), text_pos=(1428, 99), size=8.3)
arrow([(705, 345), (705, 387), (1150, 387), (1185, 442)], color="#7C3AED",
      text=value("e6"), text_pos=(1018, 368), size=8.4)
arrow([(1395, 442.5), (1460, 442.5)], text=value("e7"), text_pos=(1430, 365), size=8.5)
arrow([(790, 345), (790, 554), (900, 554)], color="#DC2626",
      text=value("e8"), text_pos=(792, 480), size=8.3)

for name, (fill, stroke, ink) in COLORS.items():
    x, y, w, h = geom(name)
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=11",
                                fc=fill, ec=stroke, lw=2.3, zorder=3))
    label(x + w / 2, y + h / 2, value(name), size=8.6, color=ink,
          weight="bold", zorder=4)

ax.add_patch(FancyBboxPatch((40, 615), 1630, 42,
                            boxstyle="round,pad=0,rounding_size=7",
                            fc="#F8FAFC", ec="#CBD5E1", lw=1.2, zorder=3))
label(855, 636, value("note1"), size=11, color="#334155", zorder=4)

label(45, 705, "Легенда:", size=11, weight="bold", ha="left")
for index, (text, fill, border) in enumerate([
    ("Источник / брокер", "#DBEAFE", "#2563EB"),
    ("Streaming", "#EDE9FE", "#7C3AED"),
    ("Хранение", "#CFFAFE", "#0891B2"),
    ("Batch", "#DCFCE7", "#16A34A"),
    ("Результаты", "#FFEDD5", "#EA580C"),
    ("Ошибки", "#FEE2E2", "#DC2626"),
]):
    x = [150, 375, 560, 745, 930, 1115][index]
    width = 210 if index == 0 else 170
    ax.add_patch(FancyBboxPatch((x, 688), width, 35,
                                boxstyle="round,pad=0,rounding_size=6",
                                fc=fill, ec=border, lw=1.5))
    label(x + width / 2, 705.5, text, size=9.7)

fig.savefig(ROOT / "architecture.png", bbox_inches="tight", pad_inches=0.14,
            dpi=140, facecolor="white")
plt.close(fig)
