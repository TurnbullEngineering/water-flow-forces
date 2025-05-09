"""Main application module for the Water Flow Forces Calculator."""

import streamlit as st
from datetime import datetime
from decimal import Decimal, getcontext
from io import BytesIO
import pandas as pd

from .constants import (
    EVENTS,
    DEFAULT_COLUMN_DIAMETER,
    DEFAULT_CD,
    DEFAULT_PILE_DIAMETER,
    DEFAULT_CD_PILE,
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
)
from .calculations import calculate_forces, calculate_actual_debris_depth
from .visualization import draw_column_diagram
from .data_processing import process_dataframe

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

    # Structure parameters
    column_diameter = st.sidebar.number_input(
        "Column Diameter (m)",
        min_value=0.1,
        max_value=10.0,
        value=DEFAULT_COLUMN_DIAMETER,
        step=0.1,
        help=f"Default: {DEFAULT_COLUMN_DIAMETER}m",
    )
    inputs["column_diameter"] = str(column_diameter)

    cd = st.sidebar.number_input(
        "Water Drag Coefficient on Pier (Cd)",
        min_value=0.1,
        max_value=2.0,
        value=DEFAULT_CD,
        step=0.1,
        help=f"Default: {DEFAULT_CD} (semi-circular)",
    )
    inputs["cd"] = str(cd)

    # Using the same column diameter for pile by default
    pile_diameter = st.sidebar.number_input(
        "Pile Diameter (m)",
        min_value=0.0,
        max_value=10.0,
        value=DEFAULT_PILE_DIAMETER,  # Default same as column
        step=0.1,
        help="Diameter of the pile (defaults to column diameter)",
    )
    inputs["pile_diameter"] = str(pile_diameter)

    cd_pile = st.sidebar.number_input(
        "Water Drag Coefficient on Pile (Cd)",
        min_value=0.0,
        max_value=2.0,
        value=DEFAULT_CD_PILE,  # Default same as column
        step=0.1,
        help="Drag coefficient for pile (defaults to column Cd)",
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

    # Setup pile diameter - use column diameter if no pile diameter specified
    actual_pile_diameter = (
        Decimal(str(inputs["pile_diameter"]))
        if float(inputs["pile_diameter"]) > 0
        else Decimal(str(inputs["column_diameter"]))
    )

    forces = calculate_forces(
        Decimal(str(inputs["column_diameter"])),
        decimal_preview_depth,
        decimal_preview_velocity,
        actual_debris_depth,  # Already a Decimal
        Decimal(str(inputs["cd"])),
        Decimal(str(inputs["log_mass"])),
        Decimal(str(inputs["stopping_distance"])),
        Decimal(str(inputs["load_factor"])),
        actual_pile_diameter,
        Decimal(str(inputs["cd_pile"])),
        preview_scour_depth,
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
    st.write("**F1 (Water Flow) + F2 (Debris)**")
    st.write("**F1 (Water Flow) + F3 (Log Impact)**")

    # Draw and display the diagram
    st.subheader("Force Diagram")
    fig = draw_column_diagram(
        water_depth=decimal_preview_depth,  # Use Decimal value directly
        column_diameter=float(inputs["column_diameter"]),
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
        params_df = pd.DataFrame(
            {
                "Parameter": [
                    "Selected Event",
                    "Column Diameter (m)",
                    "Min Debris Mat Depth (m)",
                    "Max Debris Mat Depth (m)",
                    "Debris Span (m)",
                    "Water Drag Coefficient (Cd)",
                    "Log Mass (kg)",
                    "Stopping Distance (m)",
                    "Load Factor",
                    "Pile Diameter (m)",
                    "Pile Drag Coefficient (Cd)",
                    "Scour Depth (m)",
                ],
                "Value": [
                    inputs["selected_event"],
                    str(Decimal(str(inputs["column_diameter"]))),
                    str(Decimal(str(inputs["min_debris_depth"]))),
                    str(Decimal(str(inputs["max_debris_depth"]))),
                    "20.0",  # Debris span is hard-coded
                    str(Decimal(str(inputs["cd"]))),
                    str(Decimal(str(inputs["log_mass"]))),
                    str(Decimal(str(inputs["stopping_distance"]))),
                    str(Decimal(str(inputs["load_factor"]))),
                    str(Decimal(str(inputs["pile_diameter"]))),
                    str(Decimal(str(inputs["cd_pile"]))),
                    str(Decimal(str(inputs["scour_depth"]))),
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
