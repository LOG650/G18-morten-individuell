# -*- coding: utf-8 -*-
"""
generer_figur_pooling.py
Lager Figur Vedlegg D: to-panels figur som viser forskjellen mellom
XGBoost global (pooling) og XGBoost individuell.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import numpy as np

OUTPUT = "figur_vedlegg_d_pooling.png"

# ── Farger (samme palett som eksisterende figurer) ──────────────────────────
C_GRAY   = "#aaaaaa"
C_HW     = "#5b9bd5"
C_IND    = "#9dc3e6"
C_ARIMA  = "#ed7d31"
C_GLOBAL = "#70ad47"
C_HIGHLIGHT = "#c00000"

fig = plt.figure(figsize=(14, 6))
fig.patch.set_facecolor("white")

# ── Panel A: Konseptuell treningsdiagram ────────────────────────────────────
ax1 = fig.add_axes([0.03, 0.08, 0.44, 0.82])
ax1.set_xlim(0, 10)
ax1.set_ylim(0, 10)
ax1.axis("off")
ax1.set_title("(A)  Treningsstrategi", fontsize=12, fontweight="bold", pad=10)

# ── Venstre side: Individuell ───────────────────────────────────────────────
ax1.text(1.5, 9.5, "XGBoost individuell", ha="center", fontsize=10,
         fontweight="bold", color="#1f4e79")

# Tegn 5 mini-SKU-blokker + "..." for å representere 105 separate modeller
sku_colors = [C_IND] * 5
sku_y = [8.2, 7.2, 6.2, 5.2, 4.2]
for i, (ypos, col) in enumerate(zip(sku_y, sku_colors)):
    rect = mpatches.FancyBboxPatch((0.3, ypos - 0.35), 2.4, 0.65,
                                   boxstyle="round,pad=0.05",
                                   facecolor=col, edgecolor="#2e75b6",
                                   linewidth=0.8, alpha=0.85)
    ax1.add_patch(rect)
    ax1.text(1.5, ypos, f"SKU {i+1}  |  24 rader", ha="center", va="center",
             fontsize=7.5, color="#1f4e79")

ax1.text(1.5, 3.55, "⋮", ha="center", fontsize=14, color="#555")
rect_last = mpatches.FancyBboxPatch((0.3, 2.75), 2.4, 0.65,
                                    boxstyle="round,pad=0.05",
                                    facecolor=C_IND, edgecolor="#2e75b6",
                                    linewidth=0.8, alpha=0.85)
ax1.add_patch(rect_last)
ax1.text(1.5, 3.08, "SKU 105  |  24 rader", ha="center", va="center",
         fontsize=7.5, color="#1f4e79")

# Piler ned til 105 modeller-boks
for ypos in sku_y + [3.08]:
    ax1.annotate("", xy=(1.5, 1.95), xytext=(1.5, ypos - 0.35),
                 arrowprops=dict(arrowstyle="-", color="#888", lw=0.6))

ax1.annotate("", xy=(1.5, 1.9), xytext=(1.5, 2.75),
             arrowprops=dict(arrowstyle="->", color="#555", lw=1.0))

result_ind = mpatches.FancyBboxPatch((0.2, 1.2), 2.6, 0.65,
                                     boxstyle="round,pad=0.07",
                                     facecolor="#dce6f1", edgecolor="#2e75b6",
                                     linewidth=1.2)
ax1.add_patch(result_ind)
ax1.text(1.5, 1.525, "105 separate modeller\n24 treningsrader/modell",
         ha="center", va="center", fontsize=7.5, color="#1f4e79", linespacing=1.4)

ax1.text(1.5, 0.65, "Median MAPE: 62,61 %", ha="center", fontsize=9,
         fontweight="bold", color=C_HIGHLIGHT,
         bbox=dict(boxstyle="round,pad=0.3", facecolor="#fce4ec",
                   edgecolor=C_HIGHLIGHT, linewidth=1.0))

# ── Skillelinje ─────────────────────────────────────────────────────────────
ax1.axvline(5.0, color="#cccccc", linewidth=1.2, linestyle="--")

# ── Høyre side: Global ───────────────────────────────────────────────────────
ax1.text(7.5, 9.5, "XGBoost global", ha="center", fontsize=10,
         fontweight="bold", color="#375623")

# Én stor poolet blokk
pool = mpatches.FancyBboxPatch((5.3, 3.6), 4.4, 5.15,
                               boxstyle="round,pad=0.1",
                               facecolor="#e2efda", edgecolor="#548235",
                               linewidth=1.4, alpha=0.9)
ax1.add_patch(pool)
ax1.text(7.5, 7.75, "Alle 105 SKU-er\npoolet", ha="center", va="center",
         fontsize=9.5, fontweight="bold", color="#375623", linespacing=1.5)
ax1.text(7.5, 6.7, "3 780 observasjoner\n(105 × 36 mnd)", ha="center",
         va="center", fontsize=8.5, color="#375623", linespacing=1.5)
ax1.text(7.5, 5.65, "→ ~2 520 brukbare\n   treningsrader", ha="center",
         va="center", fontsize=8.5, color="#375623", linespacing=1.5)
ax1.text(7.5, 4.55, "Lærer mønstre\npå tvers av produkter", ha="center",
         va="center", fontsize=8, color="#555", linespacing=1.5,
         style="italic")

ax1.annotate("", xy=(7.5, 1.95), xytext=(7.5, 3.6),
             arrowprops=dict(arrowstyle="->", color="#548235", lw=1.5))

result_gl = mpatches.FancyBboxPatch((5.5, 1.2), 4.0, 0.65,
                                    boxstyle="round,pad=0.07",
                                    facecolor="#e2efda", edgecolor="#548235",
                                    linewidth=1.2)
ax1.add_patch(result_gl)
ax1.text(7.5, 1.525, "1 global modell\n2 520 treningsrader totalt",
         ha="center", va="center", fontsize=7.5, color="#375623", linespacing=1.4)

ax1.text(7.5, 0.65, "Median MAPE: 52,19 %", ha="center", fontsize=9,
         fontweight="bold", color="#375623",
         bbox=dict(boxstyle="round,pad=0.3", facecolor="#e2efda",
                   edgecolor="#548235", linewidth=1.0))

# Dobbeltsidepil mellom MAPE-tall
ax1.annotate("", xy=(2.6, 0.65), xytext=(4.5, 0.65),
             arrowprops=dict(arrowstyle="<->", color="#888", lw=1.2))
ax1.text(3.55, 0.82, "10,4 pp", ha="center", fontsize=8, color="#555",
         fontweight="bold")

# ── Panel B: Søylediagram MAPE — kun XGBoost-variantene ─────────────────────
ax2 = fig.add_axes([0.54, 0.12, 0.44, 0.76])

labels     = ["XGBoost\n(individuell)", "XGBoost\n(global)"]
medians    = [62.61, 52.19]
colors     = [C_IND, C_GLOBAL]
edgecolors = ["#2e75b6", "#548235"]

bars = ax2.bar(labels, medians, color=colors, edgecolor=edgecolors,
               linewidth=1.2, width=0.45)

# Verdietiketter
for bar, val in zip(bars, medians):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.6,
             f"{val:.1f} %", ha="center", va="bottom", fontsize=12,
             fontweight="bold")

# Dobbeltpil mellom søylene med "−10,4 pp"
x_ind  = bars[0].get_x() + bars[0].get_width() / 2
x_glob = bars[1].get_x() + bars[1].get_width() / 2
y_ann  = 57.5

ax2.annotate("", xy=(x_glob, y_ann), xytext=(x_ind, y_ann),
             arrowprops=dict(arrowstyle="<->", color=C_HIGHLIGHT, lw=2.0))
ax2.text((x_ind + x_glob) / 2, y_ann + 1.2,
         "Pooling-effekt: −10,4 pp MAPE",
         ha="center", fontsize=9.5, color=C_HIGHLIGHT, fontweight="bold",
         bbox=dict(boxstyle="round,pad=0.3", facecolor="#fce4ec",
                   edgecolor=C_HIGHLIGHT, linewidth=0.9, alpha=0.95))

ax2.set_ylabel("Median MAPE (%)", fontsize=10)
ax2.set_ylim(0, 75)
ax2.set_title("(B)  Median MAPE — XGBoost individuell vs. global\n"
              "(alle 105 SKU-er, testperiode jan–des 2025)",
              fontsize=11, fontweight="bold")
ax2.tick_params(axis="x", labelsize=11)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.yaxis.grid(True, linestyle="--", alpha=0.4)
ax2.set_axisbelow(True)

# ── Felles tittel ────────────────────────────────────────────────────────────
fig.text(0.5, 0.985,
         "Figur D.1: XGBoost global versus XGBoost individuell — treningsstrategi og pooling-effekt",
         ha="center", va="top", fontsize=12, fontweight="bold")

plt.savefig(OUTPUT, dpi=150, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Lagret: {OUTPUT}")
