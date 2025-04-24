import streamlit as st
import pandas as pd
from decimal import Decimal, getcontext
from io import BytesIO

# Set precision for decimal calculations
getcontext().prec = 28


def calculate_forces(
    column_diameter,
    water_depth,
    water_velocity,
    debris_mat_depth,  # Changed parameter name for clarity
    cd,
    log_mass,
    stopping_distance,
    load_factor=Decimal("1.0"),
):
    # Convert all inputs to Decimal for precise calculations
    column_diameter = Decimal(str(column_diameter))
    water_depth = Decimal(str(water_depth))
    water_velocity = Decimal(str(water_velocity))
    debris_mat_depth = Decimal(str(debris_mat_depth))
    cd = Decimal(str(cd))
    log_mass = Decimal(str(log_mass))
    stopping_distance = Decimal(str(stopping_distance))

    # Calculate wetted area (Ad) for F1
    Ad = water_depth * column_diameter

    # Calculate debris mat area (Adeb) for F2
    debris_span = Decimal("20.0")  # m
    Adeb = debris_mat_depth * debris_span  # Using debris_mat_depth

    # Calculate forces and their locations
    # F1 - Water Flow Force
    F1 = Decimal("0.5") * cd * (water_velocity**2) * Ad
    L1 = water_depth / Decimal("2")

    # F2 - Debris Force
    F2 = Decimal("0.5") * cd * (water_velocity**2) * Adeb
    L2 = water_depth - (debris_mat_depth / Decimal("2"))  # Using debris_mat_depth

    # F3 - Log Impact Force
    # F = ma, where a = v²/2s
    acceleration = (water_velocity**2) / (Decimal("2") * stopping_distance)
    F3 = log_mass * acceleration
    L3 = water_depth

    # Apply load factor and convert F3 from N to kN
    F1 = F1 * load_factor
    F2 = F2 * load_factor
    F3 = (F3 / Decimal("1000")) * load_factor  # Convert to kN and apply load factor

    return F1, L1, F2, L2, F3, L3


def process_dataframe(df: pd.DataFrame, inputs):
    # Clean column names - replace returns with spaces and trim
    df.columns = df.columns.str.replace("\n", " ").str.strip()

    # Required columns
    VELOCITY_COL = "PMF Event Peak Velocity"
    DEPTH_COL = "PMF Event Peak Flood Depth"

    # Validate required columns exist
    missing_cols = []
    if VELOCITY_COL not in df.columns:
        missing_cols.append(VELOCITY_COL)
    if DEPTH_COL not in df.columns:
        missing_cols.append(DEPTH_COL)

    if missing_cols:
        raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

    # Initialize result columns
    results = []

    # Process each row
    for idx, row in df.iterrows():
        water_depth = row[DEPTH_COL]
        water_velocity = row[VELOCITY_COL]

        # Calculate forces using the debris mat depth from inputs
        F1, L1, F2, L2, F3, L3 = calculate_forces(
            inputs["column_diameter"],
            water_depth,
            water_velocity,
            inputs["debris_mat_depth"],  # Using input parameter
            inputs["cd"],
            inputs["log_mass"],
            inputs["stopping_distance"],
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

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Combine DataFrames
    combined_df = pd.concat([df, results_df], axis=1)

    # Convert all object columns to string type
    object_columns = combined_df.select_dtypes(include=["object"]).columns
    for col in object_columns:
        combined_df[col] = combined_df[col].astype(str)

    # Ensure all numeric columns are float type for consistency
    numeric_cols = ["F1", "L1", "F2", "L2", "F3", "L3"]
    for col in numeric_cols:
        combined_df[col] = combined_df[col].astype(float)

    return combined_df


def main():
    st.title("Water Flow Forces Calculator")

    # Input parameters
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

    inputs["debris_mat_depth"] = st.sidebar.number_input(
        "Debris Mat Depth (m)",
        min_value=0.1,
        max_value=10.0,
        value=3.0,
        step=0.1,
        help="Depth of debris mat for force calculation",
    )

    inputs["cd"] = st.sidebar.number_input(
        "Drag Coefficient (Cd)",
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
        max_value=10.0,
        value=1.0,
        step=0.1,
        help="Factor to be applied to all forces",
    )

    # Preview calculation
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

    # Excel Processing Section
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
                    # Process the data
                    result_df = process_dataframe(df, inputs)

                    # Show preview
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

                    # Download button
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        result_df.to_excel(writer, index=False)
                    output.seek(0)

                    st.download_button(
                        label="Download Results as Excel",
                        data=output,
                        file_name="water_flow_forces_results.xlsx",
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
