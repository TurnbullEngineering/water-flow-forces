"""Engineering diagrams for the Water Flow Forces Calculator."""

from decimal import Decimal
from typing import Literal

import matplotlib.figure
import matplotlib.patches
import matplotlib.pyplot as plt


def _force_arrow_length(force: Decimal, maximum_force: Decimal) -> float:
    """Return a readable, bounded arrow length that reflects relative load."""
    if force <= 0 or maximum_force <= 0:
        return 0.0
    return 1.6 + 2.8 * float(force / maximum_force)


def draw_column_diagram(
    water_depth: Decimal,
    column_diameter: float,
    debris_mat_depth: Decimal,
    F1: Decimal,
    F1a: Decimal,
    F1b: Decimal,
    F2: Decimal,
    F3: Decimal,
    L1: Decimal,
    L1a: Decimal,
    L1b: Decimal,
    L2: Decimal,
    L3: Decimal,
    Fd2: Decimal = Decimal("0"),
    Ld2: Decimal = Decimal("0"),
    pile_diameter: float = 0.0,
    scour_depth: float = 0.0,
    combination: Literal["log_impact", "debris"] = "debris",
) -> matplotlib.figure.Figure:
    """Draw a dimensioned elevation diagram of the water-flow design actions.

    Force arrows are scaled relative to the largest displayed force, while their
    labels retain the exact design value and application elevation.
    """
    fig, ax = plt.subplots(figsize=(13, 8))
    fig.patch.set_facecolor("white")

    water_y = float(water_depth)
    # The elevation is a continuous member.  The pile_diameter argument remains
    # in the public signature for compatibility with calculation inputs, but the
    # diagram uses the column diameter above and below the NGL.
    foundation_diameter = max(float(column_diameter), 0.6)
    actual_scour = max(0.0, float(scour_depth))
    pile_depth = actual_scour + 1.5
    top_of_column = water_y + 1.5
    structure_width = foundation_diameter
    left = -structure_width / 2

    # Ground and water establish the datum before the load actions are drawn.
    ax.axhspan(-pile_depth - 0.3, 0, color="#f4f1ec", zorder=0)
    ax.axhline(0, color="#5f5b55", linewidth=1.8, zorder=3)
    ax.text(-5.6, 0.14, "Ground level", color="#4b4742", fontsize=10)
    ax.axhspan(0, water_y, color="#dbeefe", alpha=0.7, zorder=0)
    ax.axhline(water_y, color="#2274a5", linestyle=(0, (5, 3)), linewidth=1.6, zorder=3)
    ax.text(
        -5.6,
        water_y + 0.16,
        "Water level",
        color="#17618c",
        fontsize=10,
        weight="bold",
    )
    ax.annotate(
        "FLOW",
        xy=(-3.35, water_y - 0.42),
        xytext=(-5.45, water_y - 0.42),
        va="center",
        ha="left",
        color="#17618c",
        fontsize=9,
        weight="bold",
        arrowprops=dict(arrowstyle="-|>", color="#17618c", lw=1.4),
    )

    # Above-ground column.
    column = matplotlib.patches.Rectangle(
        (left, 0),
        column_diameter,
        top_of_column,
        facecolor="#6b7280",
        edgecolor="#374151",
        alpha=0.58,
        linewidth=1.2,
        zorder=2,
    )
    ax.add_patch(column)

    # Debris is visibly separate from water and is capped at the water surface.
    debris_height = min(max(0.0, float(debris_mat_depth)), water_y)
    debris_bottom = water_y - debris_height
    debris_width = structure_width + 2.8
    if combination == "debris" and debris_height:
        debris = matplotlib.patches.Rectangle(
            (-debris_width / 2, debris_bottom),
            debris_width,
            debris_height,
            facecolor="#b7791f",
            edgecolor="#8a5915",
            alpha=0.32,
            linewidth=1.2,
            hatch="//",
            zorder=2.5,
        )
        ax.add_patch(debris)
        ax.text(
            -debris_width / 2 - 0.25,
            debris_bottom + debris_height / 2,
            "Debris mat",
            ha="right",
            va="center",
            fontsize=10,
            color="#71450e",
            weight="bold",
        )

    # Scoured pile and its exposed zone.
    if actual_scour > 0:
        pile = matplotlib.patches.Rectangle(
            (-foundation_diameter / 2, -pile_depth),
            foundation_diameter,
            pile_depth,
            facecolor="#6b7280",
            edgecolor="#374151",
            alpha=0.58,
            linewidth=1.2,
            zorder=2,
        )
        ax.add_patch(pile)

    # Loads: use a neutral structural diagram with a single high-contrast action colour.
    if combination == "log_impact":
        actions = [
            ("F1", "Total water-flow drag", F1, float(L1), "#c2410c", "-", 0.0),
            ("F3", "Log impact", F3, float(L3), "#c2410c", "-", 0.0),
        ]
        title = "COMBINATION 1 — WATER DRAG + LOG IMPACT"
    else:
        actions = [
            ("F1a", "Clear-water drag", F1a, float(L1a), "#c2410c", "-", 0.0),
            ("F2", "Debris drag", F2, float(L2), "#c2410c", "-", 0.0),
        ]
        title = "COMBINATION 2 — CLEAR-WATER DRAG + DEBRIS"
    if Fd2 > 0:
        actions.append(("Fd2", "Scoured-pile drag", Fd2, float(Ld2), "#c2410c", "-", 0.0))
    maximum_force = max((force for _, _, force, _, _, _, _ in actions), default=Decimal("0"))
    arrow_start = structure_width / 2 + 0.55

    for identifier, description, force, elevation, color, line_style, display_offset in actions:
        arrow_length = _force_arrow_length(force, maximum_force)
        if arrow_length == 0:
            continue
        ax.annotate(
            "",
            xy=(arrow_start + arrow_length, elevation + display_offset),
            xytext=(arrow_start, elevation + display_offset),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                linestyle=line_style,
                lw=2.6,
                mutation_scale=16,
            ),
            zorder=4,
        )
        ax.text(
            arrow_start + arrow_length + 0.2,
            elevation + display_offset,
            f"{identifier} = {float(force):,.1f} kN\n{description.upper()}  @ L = {elevation:.3f} m",
            va="center",
            ha="left",
            fontsize=10,
            color="#292524",
            zorder=5,
        )

    # Dimension lines live to the left of the structure so they never compete with loads.
    dimension_x = -structure_width / 2 - 1.5
    ax.annotate("", xy=(dimension_x, 0), xytext=(dimension_x, water_y), arrowprops=dict(arrowstyle="<->", color="#292524", lw=1.4))
    ax.text(
        dimension_x - 0.25,
        water_y / 2,
        f"WATER DEPTH\n{water_y:.3f} m",
        ha="right",
        va="center",
        fontsize=10,
    )
    ax.annotate("", xy=(left, water_y - 0.5), xytext=(-left, water_y - 0.5), arrowprops=dict(arrowstyle="<->", color="#292524", lw=1.2))
    ax.text(0, water_y - 0.7, f"FOUNDATION Ø {foundation_diameter:.3f} m", ha="center", va="top", fontsize=10)

    if actual_scour > 0:
        scour_x = dimension_x - 1.65
        ax.annotate("", xy=(scour_x, -actual_scour), xytext=(scour_x, 0), arrowprops=dict(arrowstyle="<->", color="#292524", lw=1.4))
        ax.text(
            scour_x - 0.25,
            -actual_scour / 2,
            f"SCOUR DEPTH\n{actual_scour:.3f} m",
            ha="right",
            va="center",
            fontsize=10,
        )

    min_y = min(-1.1, -pile_depth - 0.45)
    ax.set_xlim(-6.2, 10.7)
    ax.set_ylim(min_y, top_of_column + 0.6)
    ax.set_ylabel("LEVEL (m)", labelpad=12)
    ax.set_xticks([])
    ax.set_title(title, loc="left", fontsize=16, weight="bold", pad=14)
    ax.grid(axis="y", linestyle="--", alpha=0.28)
    ax.spines[["top", "right", "bottom"]].set_visible(False)
    fig.tight_layout()

    return fig
