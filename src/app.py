"""Main application module for the Water Flow Forces Calculator."""

import streamlit as st
from datetime import datetime
from decimal import Decimal, getcontext
from io import BytesIO
import pandas as pd

from .constants import (
    EVENTS,
    DEFAULT_COLUMN_DIAMETER,
    DEFAULT_PILE_DIAMETER,
    DEFAULT_WATER_DEPTH,
    DEFAULT_WATER_VELOCITY,
    DEFAULT_SCOUR_DEPTH,
    DEFAULT_MIN_DEBRIS_DEPTH,
    DEFAULT_MAX_DEBRIS_DEPTH,
    DEFAULT_LOG_MASS,
    DEFAULT_STOPPING_DISTANCE,
    DEFAULT_LOAD_FACTOR,
    CALCULATOR_DESCRIPTION,
    ENGINEERING_ASSUMPTIONS,
    LEGAL_TERMS,
    CONTACT_INFO,
    TECHNICAL_ASSUMPTIONS,
    LegType,
    LEG_TYPE_NAMES,
    CD_VALUES,
    CD_PILE_VALUES,
)
from .calculations import calculate_forces, calculate_actual_debris_depth
from .visualization import draw_column_diagram
from .data_processing import process_dataframe
from .models import PierConfig, BoredPileConfig

# Set decimal precision
getcontext().prec = 28


def main():
    """Main function to run the Streamlit application."""
    st.title("Water Flow Forces Calculator")

    st.sidebar.image("gc-icon.jpeg")
    st.sidebar.header("Event Selection")

    # Event selection dropdown
    selected_event = st.sidebar.selectbox(
        "Select Event",
        EVENTS,
        index=1,  # Default to 1% AEP
        help="Choose the event to analyze",
    )

    st.sidebar.header("Structure Parameters")

    inputs = {
        "selected_event": selected_event
    }  # Dictionary to store all input parameters

    # Structure type selection
    leg_type = st.sidebar.selectbox(
        "Structure Type",
        list(LEG_TYPE_NAMES.keys()),
        format_func=lambda x: LEG_TYPE_NAMES[x],
        help="Choose the type of structure",
    )
    # Store leg type value as string for serialization
    inputs["leg_type"] = str(leg_type.value)

    # Show parameters based on structure type
    if leg_type == LegType.PIER:
        # Pier type inputs
        column_diameter = st.sidebar.number_input(
            "Column Diameter (m)",
            min_value=0.1,
            max_value=10.0,
            value=DEFAULT_COLUMN_DIAMETER,
            step=0.1,
            help=f"Default: {DEFAULT_COLUMN_DIAMETER}m",
        )
        inputs["column_diameter"] = str(column_diameter)
        # Create PierConfig with proper type annotation
        pier_config: PierConfig = {"diameter": Decimal(str(column_diameter))}
        leg_config = pier_config
    else:
        # Bored pile type inputs
        wetted_area = st.sidebar.number_input(
            "Wetted Area (m²)",
            min_value=0.1,
            max_value=100.0,
            value=20.0,
            step=0.1,
            help="Cross-sectional area exposed to water flow",
        )
        inputs["wetted_area"] = str(wetted_area)
        # Create BoredPileConfig with proper type annotation
        bored_config: BoredPileConfig = {"area": Decimal(str(wetted_area))}
        leg_config = bored_config

    # Use CD value based on leg type
    cd = st.sidebar.number_input(
        "Above Ground Water Drag Coefficient (Cd)",
        min_value=0.1,
        max_value=2.0,
        value=CD_VALUES[leg_type],
        step=0.1,
        help=f"Default: {CD_VALUES[leg_type]} for {LEG_TYPE_NAMES[leg_type]} above ground",
    )
    inputs["cd"] = str(cd)

    # Set default pile diameter based on leg type
    default_pile_diameter = (
        DEFAULT_COLUMN_DIAMETER if leg_type == LegType.PIER else DEFAULT_PILE_DIAMETER
    )
    pile_diameter = st.sidebar.number_input(
        "Below Ground Pile Diameter (m)",
        min_value=0.0,
        max_value=10.0,
        value=default_pile_diameter,
        step=0.1,
        help="Diameter of the pile below ground (required for below-ground forces)",
    )
    inputs["pile_diameter"] = str(pile_diameter)

    cd_pile = st.sidebar.number_input(
        "Below Ground Water Drag Coefficient (Cd)",
        min_value=0.0,
        max_value=2.0,
        value=CD_PILE_VALUES[leg_type],
        step=0.1,
        help=f"Default: {CD_PILE_VALUES[leg_type]} for {LEG_TYPE_NAMES[leg_type]} below ground",
    )
    inputs["cd_pile"] = str(cd_pile)

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Preview Parameters")
    st.sidebar.markdown("*(Will be overridden by Excel data)*")

    # Group preview parameters together
    preview_depth = st.sidebar.number_input(
        "Water Depth (m)",
        min_value=0.1,
        max_value=20.0,
        value=DEFAULT_WATER_DEPTH,
        step=0.1,
        help=f"Will be replaced by '{selected_event} Event Peak Flood Depth' from Excel",
    )

    preview_velocity = st.sidebar.number_input(
        "Water Velocity (m/s)",
        min_value=0.1,
        max_value=10.0,
        value=DEFAULT_WATER_VELOCITY,
        step=0.1,
        help=f"Will be replaced by '{selected_event} Event Peak Velocity' from Excel",
    )

    preview_scour_depth = st.sidebar.number_input(
        "Visualization Scour Depth (m)",
        min_value=0.0,
        max_value=20.0,
        value=DEFAULT_SCOUR_DEPTH,
        step=0.1,
        help="Depth below ground level shown in diagram (does not affect calculations)",
    )
    inputs["scour_depth"] = str(preview_scour_depth)  # Only used for diagram

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Additional Parameters")

    min_debris_depth = st.sidebar.number_input(
        "Min Debris Mat Depth (m)",
        min_value=0.1,
        max_value=10.0,
        value=DEFAULT_MIN_DEBRIS_DEPTH,
        step=0.1,
        help="Minimum depth of debris mat",
    )
    inputs["min_debris_depth"] = str(min_debris_depth)

    max_debris_depth = st.sidebar.number_input(
        "Max Debris Mat Depth (m)",
        min_value=min_debris_depth,
        max_value=10.0,
        value=DEFAULT_MAX_DEBRIS_DEPTH,
        step=0.1,
        help="Maximum depth of debris mat",
    )
    inputs["max_debris_depth"] = str(max_debris_depth)

    log_mass = st.sidebar.number_input(
        "Log Mass (kg)",
        min_value=100,
        max_value=20000,
        value=DEFAULT_LOG_MASS,
        step=100,
        help=f"Default: {DEFAULT_LOG_MASS}kg ({int(DEFAULT_LOG_MASS / 1000)} tons)",
    )
    inputs["log_mass"] = str(log_mass)

    stopping_distance = st.sidebar.number_input(
        "Stopping Distance (m)",
        min_value=0.001,
        max_value=1.0,
        value=DEFAULT_STOPPING_DISTANCE,
        step=0.001,
        format="%.3f",
        help=f"Default: {DEFAULT_STOPPING_DISTANCE}m ({int(DEFAULT_STOPPING_DISTANCE * 1000)}mm)",
    )
    inputs["stopping_distance"] = str(stopping_distance)

    load_factor = st.sidebar.number_input(
        "Load Factor",
        min_value=0.1,
        max_value=3.0,
        value=DEFAULT_LOAD_FACTOR,
        step=0.1,
        help=f"Safety factor applied to all forces (Default: {DEFAULT_LOAD_FACTOR})",
    )
    inputs["load_factor"] = str(load_factor)

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

    preview_scour_depth = Decimal(str(inputs["scour_depth"]))
    decimal_pile_diameter = Decimal(str(inputs["pile_diameter"]))

    forces = calculate_forces(
        leg_type=leg_type,
        leg_config=leg_config,
        water_depth=decimal_preview_depth,
        water_velocity=decimal_preview_velocity,
        debris_mat_depth=actual_debris_depth,  # Already a Decimal
        cd_pier=Decimal(str(inputs["cd"])),
        log_mass=Decimal(str(inputs["log_mass"])),
        stopping_distance=Decimal(str(inputs["stopping_distance"])),
        load_factor=Decimal(str(inputs["load_factor"])),
        pile_diameter=decimal_pile_diameter,
        cd_pile=Decimal(str(inputs["cd_pile"])),
        scour_depth=preview_scour_depth,
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Forces")
        st.write(f"**F1 (Water Flow on Pier):** {float(forces['F1']):.1f} kN per pier")
        st.write(f"**F2 (Debris):** {float(forces['F2']):.1f} kN")
        st.write(f"**F3 (Log Impact):** {float(forces['F3']):.1f} kN")
        st.write(
            f"**Fd2 (Water Flow on Pile ):** {float(forces['Fd2']):.1f} kN per pile"
        )

    with col2:
        st.subheader("Locations")
        st.write(f"**L1:** {float(forces['L1']):.1f} m")
        st.write(f"**L2:** {float(forces['L2']):.1f} m")
        st.write(f"**L3:** {float(forces['L3']):.1f} m")
        st.write(f"**Ld2:** {float(forces['Ld2']):.1f} m")

    st.subheader("Load Combinations")
    st.write("All combinations include Fd2 (Water Flow on Pile below ground)")
    st.write("**Combination 1: F1 (Water Flow) + F2 (Debris) + Fd2**")
    st.write("**Combination 2: F1 (Water Flow) + F3 (Log Impact) + Fd2**")
    st.write("*(Note: F2 and F3 do not occur simultaneously)*")

    # Show structure type illustration
    st.subheader("Structure Configuration")
    if leg_type == LegType.PIER:
        st.image("pier-type.png", caption="Pier Type Configuration")
    else:
        st.image("bored-pile.png", caption="Bored Pile Configuration")

    # Draw and display the forces diagram
    st.subheader("Force Diagram")
    # Get column diameter for diagram - for PIER use diameter, for BORED_PILE use pile diameter
    vis_column_diameter = (
        float(inputs["column_diameter"])
        if leg_type == LegType.PIER
        else float(inputs["pile_diameter"])
    )
    fig = draw_column_diagram(
        water_depth=decimal_preview_depth,  # Use Decimal value directly
        column_diameter=vis_column_diameter,
        debris_mat_depth=actual_debris_depth,  # Already a Decimal
        F1=forces["F1"],
        F2=forces["F2"],
        F3=forces["F3"],
        L1=forces["L1"],
        L2=forces["L2"],
        L3=forces["L3"],
        Fd2=forces["Fd2"],
        Ld2=forces["Ld2"],
        pile_diameter=float(inputs["pile_diameter"]),
        scour_depth=float(inputs["scour_depth"]),
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
        f"""
        Upload Excel files with the following required columns:
        - **{selected_event} Event Peak Flood Depth**: Will replace the preview water depth
        - **{selected_event} Event Peak Velocity**: Will replace the preview water velocity
        - **{selected_event} Event Scour**: Will be used for pile force calculations
        
        Other parameters will use the values from the sliders.
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
        type_specific_params = (
            {"Column Diameter (m)": inputs["column_diameter"]}
            if leg_type == LegType.PIER
            else {"Wetted Area (m²)": inputs["wetted_area"]}
        )

        params_df = pd.DataFrame(
            {
                "Parameter": [
                    "Selected Event",
                    "Structure Type",
                    *type_specific_params.keys(),
                    "Water Drag Coefficient (Cd)",
                    "Debris Span (m)",
                    "Log Mass (kg)",
                    "Stopping Distance (m)",
                    "Load Factor",
                    "Pile Diameter (m)",
                    "Pile Drag Coefficient (Cd)",
                ],
                "Value": [
                    inputs["selected_event"],
                    LEG_TYPE_NAMES[leg_type],
                    *type_specific_params.values(),
                    str(Decimal(str(inputs["cd"]))),
                    "20.0",  # Debris span is hard-coded
                    str(Decimal(str(inputs["log_mass"]))),
                    str(Decimal(str(inputs["stopping_distance"]))),
                    str(Decimal(str(inputs["load_factor"]))),
                    str(Decimal(str(inputs["pile_diameter"]))),
                    str(Decimal(str(inputs["cd_pile"]))),
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
