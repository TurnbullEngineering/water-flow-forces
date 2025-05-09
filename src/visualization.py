"""Visualization functions for the Water Flow Forces Calculator."""

from decimal import Decimal
import matplotlib.pyplot as plt
import matplotlib.patches
import matplotlib.figure


def draw_column_diagram(
    water_depth: Decimal,
    column_diameter: float,
    debris_mat_depth: Decimal,
    F1: Decimal,
    F2: Decimal,
    F3: Decimal,
    L1: Decimal,
    L2: Decimal,
    L3: Decimal,
    Fd2: Decimal = Decimal("0"),
    Ld2: Decimal = Decimal("0"),
    pile_diameter: float = 0.0,
    scour_depth: float = 0.0,
) -> matplotlib.figure.Figure:
    """
    Draw the column forces diagram with proper handling of Decimal values.

    Parameters
    ----------
    water_depth : Decimal
        Depth of water from ground level
    column_diameter : float
        Diameter of the pier/column
    debris_mat_depth : Decimal
        Depth of debris mat
    F1 : Decimal
        Water Flow Force on pier (kN)
    F2 : Decimal
        Debris Force (kN)
    F3 : Decimal
        Log Impact Force (kN)
    L1 : Decimal
        Height of F1 application (m)
    L2 : Decimal
        Height of F2 application (m)
    L3 : Decimal
        Height of F3 application (m)
    Fd2 : Decimal, optional
        Water Flow Force on pile (kN)
    Ld2 : Decimal, optional
        Height of Fd2 application (m)
    pile_diameter : float, optional
        Diameter of the pile
    scour_depth : float, optional
        Depth of scour below ground level

    Returns
    -------
    matplotlib.figure.Figure
        The generated figure containing the diagram
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    # Ground
    ground_level = 0
    ax.axhline(y=ground_level, color="brown", linestyle="-", linewidth=2)

    # Calculate actual column height first
    actual_column_height = float(water_depth) + 1.5

    # Column
    column_bottom = ground_level
    column_x = 5  # Center position
    rect = matplotlib.patches.Rectangle(
        (column_x - column_diameter / 2, column_bottom),
        column_diameter,
        actual_column_height,  # Use actual height derived from water level
        color="gray",
        alpha=0.5,
    )
    ax.add_patch(rect)

    # Water level
    water_y = ground_level + float(water_depth)
    ax.axhline(y=water_y, color="blue", linestyle="--", alpha=0.5)
    ax.text(0.5, water_y, "Water Level", verticalalignment="bottom")

    # Debris mat
    debris_y = max(
        ground_level, water_y - float(debris_mat_depth)
    )  # Don't go below ground
    debris_height = float(debris_mat_depth)
    if debris_y + debris_height < water_y:
        debris_height = water_y - debris_y  # Adjust height to not exceed water level

    debris_width = 4  # Visual width for debris
    rect_debris = matplotlib.patches.Rectangle(
        (column_x - debris_width / 2, debris_y),
        debris_width,
        debris_height,
        color="brown",
        alpha=0.3,
    )
    ax.add_patch(rect_debris)
    ax.text(
        column_x - debris_width / 2 - 0.5,
        debris_y + debris_height / 2,
        "Debris Mat",
        verticalalignment="center",
        rotation=90,
    )

    # Forces
    arrow_props = dict(width=0.5, head_width=0.3, head_length=0.3, fc="red", ec="red")
    # F1 at L1
    ax.arrow(
        column_x + column_diameter / 2 + 1,
        ground_level + float(L1),
        2,
        0,
        **arrow_props,
    )
    ax.text(
        column_x + column_diameter / 2 + 3.5,
        ground_level + float(L1),
        f"F1 = {float(F1):.1f} kN @ L1 = {float(L1):.1f} m",
        verticalalignment="center",
    )

    # F2 at L2
    ax.arrow(
        column_x + column_diameter / 2 + 1,
        ground_level + float(L2),
        2,
        0,
        **arrow_props,
    )
    ax.text(
        column_x + column_diameter / 2 + 3.5,
        ground_level + float(L2),
        f"F2 = {float(F2):.1f} kN @ L2 = {float(L2):.1f} m",
        verticalalignment="center",
    )

    # F3 at L3
    ax.arrow(
        column_x + column_diameter / 2 + 1,
        ground_level + float(L3),
        2,
        0,
        **arrow_props,
    )
    ax.text(
        column_x + column_diameter / 2 + 3.5,
        ground_level + float(L3),
        f"F3 = {float(F3):.1f} kN @ L3 = {float(L3):.1f} m",
        verticalalignment="center",
    )

    # Dimensions
    ax.annotate(
        "",
        xy=(column_x - column_diameter / 2 - 0.5, ground_level),
        xytext=(column_x - column_diameter / 2 - 0.5, water_y),
        arrowprops=dict(arrowstyle="<->"),
    )
    ax.text(
        column_x - column_diameter / 2 - 1,
        (ground_level + water_y) / 2,
        f"Water Depth\n{float(water_depth):.1f} m",
        verticalalignment="center",
    )

    # Pier diameter indicator (above ground)
    ax.annotate(
        "",
        xy=(column_x - column_diameter / 2, water_y - 0.5),
        xytext=(column_x + column_diameter / 2, water_y - 0.5),
        arrowprops=dict(arrowstyle="<->"),
    )
    ax.text(
        column_x,
        water_y - 1,
        f"Pier Diameter\n{float(column_diameter):.1f} m",
        horizontalalignment="center",
    )

    # Initialize variables used later for ylim
    actual_scour = 0.0
    pile_depth = 0.0

    # Draw pile and scour
    if pile_diameter > 0:
        # Scour depth as provided
        actual_scour = float(scour_depth)
        # Pile extends 1.5m below scour depth
        pile_depth = actual_scour + 1.5

        # Draw scour indicator
        ax.annotate(
            "",
            xy=(column_x - pile_diameter / 2 - 3, ground_level - actual_scour),
            xytext=(column_x - pile_diameter / 2 - 3, ground_level),
            arrowprops=dict(arrowstyle="<->"),
        )
        ax.text(
            column_x - pile_diameter / 2 - 3.5,
            ground_level - actual_scour / 2,
            f"Scour\nDepth\n{actual_scour:.1f} m",
            verticalalignment="center",
        )

        # Pile
        pile_rect = matplotlib.patches.Rectangle(
            (column_x - pile_diameter / 2, ground_level - pile_depth),
            pile_diameter,
            pile_depth,
            color="darkgray",
            alpha=0.5,
        )
        ax.add_patch(pile_rect)

        # Fd2 at Ld2 (below ground)
        if float(Fd2) > 0:
            ax.arrow(
                column_x + pile_diameter / 2 + 1,
                ground_level + float(Ld2),  # Ld2 is negative
                2,
                0,
                **arrow_props,
            )
            ax.text(
                column_x + pile_diameter / 2 + 3.5,
                ground_level + float(Ld2),
                f"Fd2 = {float(Fd2):.1f} kN @ Ld2 = {float(Ld2):.1f} m",
                verticalalignment="center",
            )

        # Pile diameter indicator (below ground)
        ax.annotate(
            "",
            xy=(column_x - pile_diameter / 2, ground_level - 0.5),
            xytext=(column_x + pile_diameter / 2, ground_level - 0.5),
            arrowprops=dict(arrowstyle="<->"),
        )
        ax.text(
            column_x,
            ground_level - 1,
            f"Pile Diameter\n{float(pile_diameter):.1f} m",
            horizontalalignment="center",
        )

    # Set limits and labels with adjusted ylim for pile
    ax.set_xlim(0, 10)
    min_y = min(ground_level - 1.5, ground_level - pile_depth - 0.5)
    ax.set_ylim(min_y, actual_column_height + 0.5)
    ax.set_xlabel("Width (m)")
    ax.set_ylabel("Height (m)")
    ax.set_title("Column Forces Diagram")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.set_aspect("equal")

    return fig
