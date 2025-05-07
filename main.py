import streamlit as st
import pandas as pd
import numpy as np
from decimal import Decimal, getcontext
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib.figure
import matplotlib.patches
from datetime import datetime

getcontext().prec = 28

# Terms and descriptions
CALCULATOR_DESCRIPTION = """
The Water Flow Forces Calculator, developed by Turnbull Engineering Pty Ltd, estimates design forces on transmission tower footings in accordance with AS 5100.2 Section 16 - Forces Resulting from Water Flow.
"""

ENGINEERING_ASSUMPTIONS = """
The tool applies reasonable engineering assumptions, including (but not limited to) a default load factor of 1.3 for the PMF peak flood, reflecting considerations such as climate change, limited redundancy, and inspection/maintenance constraints.
"""

LEGAL_TERMS = """
By using this tool, you acknowledge that you are appropriately qualified to interpret its outputs. Turnbull Engineering Pty Ltd reserves the right to update, modify, or discontinue the software and documentation without notice.
"""

CONTACT_INFO = """
The embedded sheet outlines key assumptions and design input parameters used in the calculations. For bespoke scenarios or custom refinements, please contact Marco.Liang@Turnbullengineering.com.au.
"""

TECHNICAL_ASSUMPTIONS = [
    "Scour protection is assumed; scour depth is excluded from force calculations.",
    "Wetted area is calculated as the product of water depth and column diameter.",
    "Debris width is assumed to be 20 m.",
    "For water depths less than the minimum debris depth, the minimum depth is adopted per AS 5100.2.",
    "Default load factor is 1.3, actual load factor used for calculations is a parameter.",
]


def Cd(V: Decimal, y: Decimal) -> Decimal:
    """
    Compute the drag coefficient C_d for pier-debris blockage based on V²y.

    Source:
      • Figure 16.6.4(A) "Pier Debris C_d"
      • AS 5100.2:2017 - Bridge Design Part 2: Design Loads

    This uses the following piecewise-linear definition:

      V²y range    | C_d
      -------------|------
      V²y <= 40     | 3.4
      40 -> 60      | 3.4 → 2.8
      60 -> 85      | 2.8 → 2.35
      85 -> 100     | 2.35 → 2.20
      100 -> 130    | 2.20 → 1.95
      130 -> 260    | 1.95 → 1.40
      V²y >= 260    | 1.40

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


def calculate_actual_debris_depth(
    water_depth: Decimal, min_debris_depth: Decimal, max_debris_depth: Decimal
) -> Decimal:
    """
    Calculate actual debris depth based on water depth and constraints.

    Parameters
    ----------
    water_depth : Decimal
        The depth of water
    min_debris_depth : Decimal
        Minimum allowed debris depth
    max_debris_depth : Decimal
        Maximum allowed debris depth

    Returns
    -------
    Decimal
        The actual debris depth constrained by min and max values
    """
    return min(max_debris_depth, max(min_debris_depth, water_depth))


def calculate_forces(
    column_diameter: Decimal,
    water_depth: Decimal,
    water_velocity: Decimal,
    debris_mat_depth: Decimal,
    cd: Decimal,
    log_mass: Decimal,
    stopping_distance: Decimal,
    load_factor: Decimal,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal]:
    """Calculate forces using Decimal for consistent precision.

    All parameters must be Decimal instances for maximum precision.
    """

    # Calculate wetted area (Ad) for F1
    Ad = water_depth * column_diameter

    # Calculate debris mat area (Adeb) for F2
    # Ensure debris mat depth doesn't exceed water depth
    effective_debris_depth = min(debris_mat_depth, water_depth)  # Already Decimal
    debris_span = Decimal("20.0")  # m, ensure consistent decimal usage
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
    F3 = log_mass * acceleration * load_factor / Decimal("1000")  # Convert to kN
    L3 = water_depth

    return F1, L1, F2, L2, F3, L3


def draw_column_diagram(
    water_depth: Decimal,
    column_height: float,
    column_diameter: float,
    debris_mat_depth: Decimal,
    F1: Decimal,
    F2: Decimal,
    F3: Decimal,
    L1: Decimal,
    L2: Decimal,
    L3: Decimal,
) -> matplotlib.figure.Figure:
    """Draw the column forces diagram with proper handling of Decimal values."""
    fig, ax = plt.subplots(figsize=(10, 8))

    # Ground
    ground_level = 0
    ax.axhline(y=ground_level, color="brown", linestyle="-", linewidth=2)

    # Column
    column_bottom = ground_level
    column_x = 5  # Center position
    rect = matplotlib.patches.Rectangle(
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


def process_dataframe(df: pd.DataFrame, inputs: dict) -> pd.DataFrame:
    """Process the input dataframe and calculate forces using Decimal for precision."""
    df.columns = df.columns.str.replace("\n", " ").str.strip()

    VELOCITY_COL = "PMF Event Peak Velocity"
    DEPTH_COL = "PMF Event Peak Flood Depth"

    missing_cols = []
    if VELOCITY_COL not in df.columns:
        missing_cols.append(VELOCITY_COL)
    if DEPTH_COL not in df.columns:
        missing_cols.append(DEPTH_COL)

    df[VELOCITY_COL] = pd.to_numeric(df[VELOCITY_COL], errors="coerce")
    df[DEPTH_COL] = pd.to_numeric(df[DEPTH_COL], errors="coerce")

    if missing_cols:
        raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

    results = []

    def is_invalid_value(val):
        if pd.isna(val) or val == np.nan:
            return True
        return False

    for idx, row in df.iterrows():
        water_depth = row[DEPTH_COL]
        water_velocity = row[VELOCITY_COL]

        # If either value is invalid, output N/A for all results
        if is_invalid_value(water_depth) or is_invalid_value(water_velocity):
            print(type(water_depth), type(water_velocity))
            print(water_depth, water_velocity)
            print("Invalid values detected, skipping row.")
            results.append(
                {
                    "F1": "N/A",
                    "L1": "N/A",
                    "F2": "N/A",
                    "L2": "N/A",
                    "F3": "N/A",
                    "L3": "N/A",
                }
            )
            continue

        # Convert all inputs to Decimal for consistent precision
        decimal_water_depth = Decimal(str(water_depth))
        decimal_water_velocity = Decimal(str(water_velocity))

        actual_debris_depth = calculate_actual_debris_depth(
            decimal_water_depth,
            Decimal(str(inputs["min_debris_depth"])),
            Decimal(str(inputs["max_debris_depth"])),
        )

        F1, L1, F2, L2, F3, L3 = calculate_forces(
            Decimal(str(inputs["column_diameter"])),
            decimal_water_depth,
            decimal_water_velocity,
            actual_debris_depth,  # Already a Decimal
            Decimal(str(inputs["cd"])),
            Decimal(str(inputs["log_mass"])),
            Decimal(str(inputs["stopping_distance"])),
            Decimal(str(inputs["load_factor"])),
        )

        results.append(
            {
                "F1": float(F1),
                "L1": float(L1),
                "F2": float(F2),
                "L2": float(L2),
                "F3": float(F3),
                "L3": float(L3),
            }
        )

    results_df = pd.DataFrame(results)
    combined_df = pd.concat([df, results_df], axis=1)
    combined_df.replace(
        to_replace=[np.inf, -np.inf, np.nan],
        value="N/A",
        inplace=True,
    )

    object_columns = combined_df.select_dtypes(include=["object"]).columns
    for col in object_columns:
        combined_df[col] = combined_df[col].astype(str)

    # Skip converting columns with N/A values to float

    return combined_df


def main():
    st.title("Water Flow Forces Calculator")

    st.sidebar.image("gc-icon.jpeg")
    st.sidebar.header("Structure Parameters")

    inputs = {}  # Dictionary to store all input parameters
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

    inputs["min_debris_depth"] = st.sidebar.number_input(
        "Min Debris Mat Depth (m)",
        min_value=0.1,
        max_value=10.0,
        value=1.2,
        step=0.1,
        help="Minimum depth of debris mat",
    )

    inputs["max_debris_depth"] = st.sidebar.number_input(
        "Max Debris Mat Depth (m)",
        min_value=inputs["min_debris_depth"],
        max_value=10.0,
        value=3.0,
        step=0.1,
        help="Maximum depth of debris mat",
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

    # Convert preview values to Decimal for consistent precision
    decimal_preview_depth = Decimal(str(preview_depth))
    decimal_preview_velocity = Decimal(str(preview_velocity))

    actual_debris_depth = calculate_actual_debris_depth(
        decimal_preview_depth,
        Decimal(str(inputs["min_debris_depth"])),
        Decimal(str(inputs["max_debris_depth"])),
    )

    preview_F1, preview_L1, preview_F2, preview_L2, preview_F3, preview_L3 = (
        calculate_forces(
            Decimal(str(inputs["column_diameter"])),
            decimal_preview_depth,
            decimal_preview_velocity,
            actual_debris_depth,  # Already a Decimal
            Decimal(str(inputs["cd"])),
            Decimal(str(inputs["log_mass"])),
            Decimal(str(inputs["stopping_distance"])),
            Decimal(str(inputs["load_factor"])),
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
    st.write("**F1 (Water Flow) + F2 (Debris)**")
    st.write("**F1 (Water Flow) + F3 (Log Impact)**")

    # Draw and display the diagram
    st.subheader("Force Diagram")
    fig = draw_column_diagram(
        water_depth=decimal_preview_depth,  # Use Decimal value directly
        column_height=inputs["column_height"],
        column_diameter=inputs["column_diameter"],
        debris_mat_depth=actual_debris_depth,  # Already a Decimal
        F1=preview_F1,
        F2=preview_F2,
        F3=preview_F3,
        L1=preview_L1,
        L2=preview_L2,
        L3=preview_L3,
    )
    st.pyplot(fig)

    st.markdown("---")
    st.header("Terms and Conditions")
    st.markdown(CALCULATOR_DESCRIPTION)
    st.markdown(ENGINEERING_ASSUMPTIONS)
    st.markdown(LEGAL_TERMS)
    st.markdown(CONTACT_INFO)

    st.header("Technical Assumptions")
    for assumption in TECHNICAL_ASSUMPTIONS:
        st.markdown(f"- {assumption}")

    st.markdown("---")
    st.header("Excel Processing")
    st.markdown(
        """
        Upload Excel files with the following required columns:
        - **PMF Event Peak Flood Depth**: Will replace the preview water depth
        - **PMF Event Peak Velocity**: Will replace the preview water velocity
        
        Other parameters (including debris mat depth) will use the values from the sliders.
        All files will be processed automatically and available for download as a zip file.
        """
    )

    uploaded_files = st.file_uploader(
        "Upload Excel files", type=["xlsx"], accept_multiple_files=True
    )

    if not uploaded_files:
        return

    from zipfile import ZipFile

    processed_files = []
    all_results_preview = []

    for uploaded_file in uploaded_files:
        try:
            df = pd.read_excel(uploaded_file)
        except Exception as e:
            st.error(f"Error reading file {uploaded_file.name}: {str(e)}")
            continue

        try:
            result_df = process_dataframe(df, inputs)
        except ValueError as e:
            st.error(f"Error processing file {uploaded_file.name}: {str(e)}")
            continue
        except Exception as e:
            st.error(
                f"An unexpected error occurred with file {uploaded_file.name}: {str(e)}"
            )
            continue

        # Create terms dataframe
        terms_df = pd.DataFrame(
            {
                "Terms": [
                    CALCULATOR_DESCRIPTION,
                    ENGINEERING_ASSUMPTIONS,
                    LEGAL_TERMS,
                    CONTACT_INFO,
                    "",
                    "Embedded Design Assumptions:",
                    *[f"- {assumption}" for assumption in TECHNICAL_ASSUMPTIONS],
                    "",
                ]
            }
        )

        # Create parameters dataframe with exact values
        params_df = pd.DataFrame(
            {
                "Parameter": [
                    "Column Diameter (m)",
                    "Min Debris Mat Depth (m)",
                    "Max Debris Mat Depth (m)",
                    "Debris Span (m)",
                    "Water Drag Coefficient (Cd)",
                    "Log Mass (kg)",
                    "Stopping Distance (m)",
                    "Load Factor",
                ],
                "Value": [
                    str(
                        Decimal(str(inputs["column_diameter"]))
                    ),  # Convert to exact decimal string
                    str(Decimal(str(inputs["min_debris_depth"]))),
                    str(Decimal(str(inputs["max_debris_depth"]))),
                    "20.0",  # Debris span is hard-coded
                    str(Decimal(str(inputs["cd"]))),
                    str(Decimal(str(inputs["log_mass"]))),
                    str(Decimal(str(inputs["stopping_distance"]))),
                    str(Decimal(str(inputs["load_factor"]))),
                ],
            }
        )

        # Create Excel file in memory
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            result_df.to_excel(writer, sheet_name="Results", index=False)
            terms_df.to_excel(writer, sheet_name="Input Parameters", index=False)
            params_df.to_excel(
                writer,
                sheet_name="Input Parameters",
                startrow=len(terms_df) + 1,
                index=False,
            )

        excel_buffer.seek(0)
        processed_files.append((f"forces_results_{uploaded_file.name}", excel_buffer))
        all_results_preview.append(result_df)

    if not processed_files:
        st.error("No files were successfully processed")
        return

    # Create zip file in memory
    zip_buffer = BytesIO()
    with ZipFile(zip_buffer, "w") as zip_file:
        for filename, excel_buffer in processed_files:
            zip_file.writestr(filename, excel_buffer.getvalue())

    zip_buffer.seek(0)

    # Show results preview
    st.success(f"Successfully processed {len(processed_files)} files")
    st.subheader("Results Preview")

    for i, result_df in enumerate(all_results_preview):
        st.write(f"**File {i + 1}:**")
        try:
            st.dataframe(result_df)
        except Exception:
            st.warning(
                f"Converting problematic columns to string type for File {i + 1}..."
            )
            object_columns = result_df.select_dtypes(include=["object"]).columns
            for col in object_columns:
                result_df[col] = result_df[col].astype(str)
            st.dataframe(result_df)

    # Download button for zip file
    st.download_button(
        label="Download All Results as Zip",
        data=zip_buffer,
        file_name=f"forces_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
        mime="application/zip",
    )


if __name__ == "__main__":
    main()
