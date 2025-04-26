import streamlit as st
import pandas as pd
from decimal import Decimal, getcontext
from io import BytesIO
import matplotlib.pyplot as plt

getcontext().prec = 28


def Cd(V: Decimal, y: Decimal) -> Decimal:
    """
    Compute the drag coefficient C_d for pier-debris blockage based on V²y.

    Source:
      • Figure 16.6.4(A) “Pier Debris C_d”
      • AS 5100.2:2017 - Bridge Design Part 2: Design Loads

    This uses the following piecewise-linear definition:

      V²y range    | C_d
      -------------|------
      V²y <= 40     | 3.4
      40 -> 60      | 3.4 → 2.8
      60 -> 85      | 2.8 → 2.35
      85 -> 100     | 2.35 → 2.20
      100 -> 130    | 2.20 → 1.95
      130 -> 260    | 1.95 → 1.60
      V²y >= 260    | 1.6

    The slopes in each interior segment connect the endpoints exactly.

    Parameters
    ----------
    V : Decimal
        Approach-flow velocity in m/s.
    y : Decimal
        Mean flow depth in m.

    Returns
    -------
    Decimal
        Dimensionless drag coefficient, C_d.
    """

    V2y = V**2 * y

    if V2y <= 40:
        return Decimal("3.4")
    elif V2y <= 60:
        return Decimal("3.4") - Decimal("0.03") * (V2y - 40)
    elif V2y <= 85:
        return Decimal("2.8") - Decimal("0.018") * (V2y - 60)
    elif V2y <= 100:
        return Decimal("2.35") - Decimal("0.01") * (V2y - 85)
    elif V2y <= 130:
        return Decimal("2.2") - Decimal("0.00833") * (V2y - 100)
    elif V2y <= 260:
        return Decimal("1.95") - Decimal("0.00423") * (V2y - 130)
    else:
        return Decimal("1.4")


def calculate_forces(
    column_diameter,
    water_depth,
    water_velocity,
    debris_mat_depth,
    cd,
    log_mass,
    stopping_distance,
    load_factor,
):
    column_diameter = Decimal(str(column_diameter))
    water_depth = Decimal(str(water_depth))
    water_velocity = Decimal(str(water_velocity))
    debris_mat_depth = Decimal(str(debris_mat_depth))
    cd = Decimal(str(cd))
    log_mass = Decimal(str(log_mass))
    stopping_distance = Decimal(str(stopping_distance))
    load_factor = Decimal(str(load_factor))

    # Calculate wetted area (Ad) for F1
    Ad = water_depth * column_diameter

    # Calculate debris mat area (Adeb) for F2
    # Ensure debris mat depth doesn't exceed water depth
    effective_debris_depth = min(debris_mat_depth, water_depth)
    debris_span = Decimal("20.0")  # m
    Adeb = effective_debris_depth * debris_span

    # F1 - Water Flow Force
    F1 = Decimal("0.5") * cd * (water_velocity**2) * Ad * load_factor
    L1 = water_depth / Decimal("2")

    # F2 - Debris Force
    C_debris = Cd(water_velocity, water_depth)
    F2 = Decimal("0.5") * C_debris * (water_velocity**2) * Adeb * load_factor
    L2 = water_depth - (effective_debris_depth / Decimal("2"))

    # F3 - Log Impact Force
    acceleration = (water_velocity**2) / (Decimal("2") * stopping_distance)
    F3 = log_mass * acceleration * load_factor
    L3 = water_depth

    F3 = F3 / Decimal("1000")

    return F1, L1, F2, L2, F3, L3


def draw_column_diagram(
    water_depth,
    column_height,
    column_diameter,
    debris_mat_depth,
    F1,
    F2,
    F3,
    L1,
    L2,
    L3,
):
    fig, ax = plt.subplots(figsize=(10, 8))

    # Ground
    ground_level = 0
    ax.axhline(y=ground_level, color="brown", linestyle="-", linewidth=2)

    # Column
    column_bottom = ground_level
    column_x = 5  # Center position
    rect = plt.Rectangle(
        (column_x - column_diameter / 2, column_bottom),
        column_diameter,
        column_height,
        color="gray",
        alpha=0.5,
    )
    ax.add_patch(rect)

    # Water level
    water_y = ground_level + float(water_depth)
    ax.axhline(y=water_y, color="blue", linestyle="--", alpha=0.5)
    ax.text(0.5, water_y, "Water Level", verticalalignment="bottom")

    # Debris mat
    debris_y = water_y - float(debris_mat_depth)
    debris_width = 4  # Visual width for debris
    rect_debris = plt.Rectangle(
        (column_x - debris_width / 2, debris_y),
        debris_width,
        float(debris_mat_depth),
        color="brown",
        alpha=0.3,
    )
    ax.add_patch(rect_debris)
    ax.text(
        column_x - debris_width / 2 - 0.5,
        debris_y + float(debris_mat_depth) / 2,
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
        f"F1 = {float(F1):.1f} kN",
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
        f"F2 = {float(F2):.1f} kN",
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
        f"F3 = {float(F3):.1f} kN",
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

    ax.annotate(
        "",
        xy=(column_x - column_diameter / 2 - 2, ground_level),
        xytext=(
            column_x - column_diameter / 2 - 2,
            ground_level + float(column_height),
        ),
        arrowprops=dict(arrowstyle="<->"),
    )
    ax.text(
        column_x - column_diameter / 2 - 2.5,
        ground_level + float(column_height) / 2,
        f"Column Height\n{float(column_height):.1f} m",
        verticalalignment="center",
    )

    ax.annotate(
        "",
        xy=(column_x - column_diameter / 2, ground_level - 0.5),
        xytext=(column_x + column_diameter / 2, ground_level - 0.5),
        arrowprops=dict(arrowstyle="<->"),
    )
    ax.text(
        column_x,
        ground_level - 1,
        f"Diameter\n{float(column_diameter):.1f} m",
        horizontalalignment="center",
    )

    # Set limits and labels
    ax.set_xlim(0, 10)
    ax.set_ylim(ground_level - 1.5, max(float(column_height), float(water_depth)) + 1)
    ax.set_xlabel("Width (m)")
    ax.set_ylabel("Height (m)")
    ax.set_title("Column Forces Diagram")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.set_aspect("equal")

    return fig


def process_dataframe(df: pd.DataFrame, inputs):
    df.columns = df.columns.str.replace("\n", " ").str.strip()

    VELOCITY_COL = "PMF Event Peak Velocity"
    DEPTH_COL = "PMF Event Peak Flood Depth"

    missing_cols = []
    if VELOCITY_COL not in df.columns:
        missing_cols.append(VELOCITY_COL)
    if DEPTH_COL not in df.columns:
        missing_cols.append(DEPTH_COL)

    if missing_cols:
        raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

    results = []

    for idx, row in df.iterrows():
        water_depth = row[DEPTH_COL]
        water_velocity = row[VELOCITY_COL]

        F1, L1, F2, L2, F3, L3 = calculate_forces(
            inputs["column_diameter"],
            water_depth,
            water_velocity,
            inputs["debris_mat_depth"],
            inputs["cd"],
            inputs["log_mass"],
            inputs["stopping_distance"],
            inputs["load_factor"],
        )

        results.append(
            {
                "F1": float(F1),
                "L1": float(L1),
                "F2": float(F2),
                "L2": float(L2),
                "F3": float(F3),
                "L3": float(L3),
                "F1+F2": float(F1 + F2),
                "F1+F3": float(F1 + F3),
            }
        )

    results_df = pd.DataFrame(results)
    combined_df = pd.concat([df, results_df], axis=1)

    object_columns = combined_df.select_dtypes(include=["object"]).columns
    for col in object_columns:
        combined_df[col] = combined_df[col].astype(str)

    numeric_cols = ["F1", "L1", "F2", "L2", "F3", "L3", "F1+F2", "F1+F3"]
    for col in numeric_cols:
        combined_df[col] = combined_df[col].astype(float)

    return combined_df


def main():
    st.title("Water Flow Forces Calculator")

    st.sidebar.image("gc-icon.jpeg")
    st.sidebar.header("Structure Parameters")

    inputs = {}
    inputs["column_height"] = st.sidebar.number_input(
        "Column Height (m)",
        min_value=0.1,
        max_value=30.0,
        value=8.0,
        step=0.1,
        help="Default: 8.0m",
    )

    inputs["column_diameter"] = st.sidebar.number_input(
        "Column Diameter (m)",
        min_value=0.1,
        max_value=10.0,
        value=2.5,
        step=0.1,
        help="Default: 2.5m",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Preview Parameters (will be overridden by Excel data)")

    preview_depth = st.sidebar.number_input(
        "Water Depth (m) - Preview Only",
        min_value=0.1,
        max_value=20.0,
        value=8.0,
        step=0.1,
        help="Will be replaced by 'PMF Event Peak Flood Depth' from Excel",
    )

    preview_velocity = st.sidebar.number_input(
        "Water Velocity (m/s) - Preview Only",
        min_value=0.1,
        max_value=10.0,
        value=3.0,
        step=0.1,
        help="Will be replaced by 'PMF Event Peak Velocity' from Excel",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Additional Parameters")

    max_debris_depth = min(10.0, preview_depth)  # Limit by water depth
    default_debris_depth = min(3.0, max_debris_depth)  # Adjust default if needed

    inputs["debris_mat_depth"] = st.sidebar.number_input(
        "Debris Mat Depth (m)",
        min_value=0.1,
        max_value=max_debris_depth,
        value=default_debris_depth,
        step=0.1,
        help="Depth of debris mat for force calculation (limited by water depth)",
    )

    inputs["cd"] = st.sidebar.number_input(
        "Water Drag Coefficient on Column (Cd)",
        min_value=0.1,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="Default: 0.7 (semi-circular)",
    )

    inputs["log_mass"] = st.sidebar.number_input(
        "Log Mass (kg)",
        min_value=100,
        max_value=20000,
        value=10000,
        step=100,
        help="Default: 10000kg (10 tons)",
    )

    inputs["stopping_distance"] = st.sidebar.number_input(
        "Stopping Distance (m)",
        min_value=0.001,
        max_value=1.0,
        value=0.025,
        step=0.001,
        format="%.3f",
        help="Default: 0.025m (25mm)",
    )

    inputs["load_factor"] = st.sidebar.number_input(
        "Load Factor",
        min_value=0.1,
        max_value=3.0,
        value=1.3,
        step=0.1,
        help="Safety factor applied to all forces (Default: 1.3)",
    )

    st.header("Preview Calculation")
    st.info(
        "This preview uses the water depth and velocity values from the sliders. "
        "These values will be replaced by the Excel columns when processing the file."
    )

    preview_F1, preview_L1, preview_F2, preview_L2, preview_F3, preview_L3 = (
        calculate_forces(
            inputs["column_diameter"],
            preview_depth,
            preview_velocity,
            inputs["debris_mat_depth"],
            inputs["cd"],
            inputs["log_mass"],
            inputs["stopping_distance"],
            inputs["load_factor"],
        )
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Forces")
        st.write(f"**F1 (Water Flow):** {preview_F1:.1f} kN")
        st.write(f"**F2 (Debris):** {preview_F2:.1f} kN")
        st.write(f"**F3 (Log Impact):** {preview_F3:.1f} kN")

    with col2:
        st.subheader("Locations")
        st.write(f"**L1:** {preview_L1:.1f} m")
        st.write(f"**L2:** {preview_L2:.1f} m")
        st.write(f"**L3:** {preview_L3:.1f} m")

    st.subheader("Load Combinations")
    st.write(f"**F1 (Water Flow) + F2 (Debris):** {preview_F1 + preview_F2:.1f} kN")
    st.write(f"**F1 (Water Flow) + F3 (Log Impact):** {preview_F1 + preview_F3:.1f} kN")

    # Draw and display the diagram
    st.subheader("Force Diagram")
    fig = draw_column_diagram(
        water_depth=preview_depth,
        column_height=inputs["column_height"],
        column_diameter=inputs["column_diameter"],
        debris_mat_depth=inputs["debris_mat_depth"],
        F1=preview_F1,
        F2=preview_F2,
        F3=preview_F3,
        L1=preview_L1,
        L2=preview_L2,
        L3=preview_L3,
    )
    st.pyplot(fig)

    st.markdown("---")
    st.header("Excel Processing")
    st.markdown(
        """
        Upload an Excel file with the following required columns:
        - **PMF Event Peak Flood Depth**: Will replace the preview water depth
        - **PMF Event Peak Velocity**: Will replace the preview water velocity
        
        Other parameters (including debris mat depth) will use the values from the sliders.
        """
    )

    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            st.success("File uploaded successfully!")

            if st.button("Process Excel File"):
                try:
                    result_df = process_dataframe(df, inputs)

                    st.subheader("Results Preview")
                    try:
                        st.dataframe(result_df)
                    except Exception:
                        st.error(
                            "Error displaying results. Converting problematic columns to string type..."
                        )
                        # Convert all object columns to string type
                        object_columns = result_df.select_dtypes(
                            include=["object"]
                        ).columns
                        for col in object_columns:
                            result_df[col] = result_df[col].astype(str)
                        st.dataframe(result_df)

                    output = BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        result_df.to_excel(writer, index=False)
                    output.seek(0)

                    st.download_button(
                        label="Download Results as Excel",
                        data=output,
                        file_name=f"forces_results_{uploaded_file.name}",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                except ValueError as e:
                    st.error(f"Error processing file: {str(e)}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}")

        except Exception as e:
            st.error(f"Error reading file: {str(e)}")


if __name__ == "__main__":
    main()
