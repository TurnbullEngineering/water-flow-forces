"""Data processing functions for handling Excel files in the Water Flow Forces Calculator."""

from decimal import Decimal
import pandas as pd
import numpy as np
from .calculations import calculate_forces, calculate_actual_debris_depth


def process_dataframe(df: pd.DataFrame, inputs: dict) -> pd.DataFrame:
    """
    Process the input dataframe and calculate forces using Decimal for precision.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing flood event data
    inputs : dict
        Dictionary of input parameters including:
        - selected_event: str, e.g. "1% AEP" or "PMF"
        - column_diameter: str
        - cd: str
        - pile_diameter: str
        - cd_pile: str
        - min_debris_depth: str
        - max_debris_depth: str
        - log_mass: str
        - stopping_distance: str
        - load_factor: str

    Returns
    -------
    pd.DataFrame
        The input dataframe with additional columns for calculated forces

    Raises
    ------
    ValueError
        If required columns are missing from the dataframe
    """
    df.columns = df.columns.str.replace("\n", " ").str.strip()

    # Use selected event for column names
    event = inputs["selected_event"]  # e.g. "1% AEP" or "PMF"
    VELOCITY_COL = f"{event} Event Peak Velocity"
    DEPTH_COL = f"{event} Event Peak Flood Depth"
    SCOUR_COL = f"{event} Event Scour"

    missing_cols = []
    if VELOCITY_COL not in df.columns:
        missing_cols.append(VELOCITY_COL)
    if DEPTH_COL not in df.columns:
        missing_cols.append(DEPTH_COL)
    if SCOUR_COL not in df.columns:
        missing_cols.append(SCOUR_COL)

    df[VELOCITY_COL] = pd.to_numeric(df[VELOCITY_COL], errors="coerce")
    df[DEPTH_COL] = pd.to_numeric(df[DEPTH_COL], errors="coerce")
    df[SCOUR_COL] = pd.to_numeric(df[SCOUR_COL], errors="coerce")

    if missing_cols:
        raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

    results = []

    def is_invalid_value(val):
        """Check if a value is invalid (NaN or None)."""
        if pd.isna(val) or val == np.nan:
            return True
        return False

    for idx, row in df.iterrows():
        water_depth = row[DEPTH_COL]
        water_velocity = row[VELOCITY_COL]
        scour_depth = row[SCOUR_COL]

        # If any value is invalid, output N/A for all results
        if (
            is_invalid_value(water_depth)
            or is_invalid_value(water_velocity)
            or is_invalid_value(scour_depth)
        ):
            results.append(
                {
                    "F1": "N/A",
                    "L1": "N/A",
                    "F2": "N/A",
                    "L2": "N/A",
                    "F3": "N/A",
                    "L3": "N/A",
                    "Fd2": "N/A",
                    "Ld2": "N/A",
                }
            )
            continue

        # Convert all inputs to Decimal for consistent precision
        decimal_water_depth = Decimal(str(water_depth))
        decimal_water_velocity = Decimal(str(water_velocity))
        decimal_scour_depth = Decimal(str(scour_depth))

        actual_debris_depth = calculate_actual_debris_depth(
            decimal_water_depth,
            Decimal(str(inputs["min_debris_depth"])),
            Decimal(str(inputs["max_debris_depth"])),
        )

        # Use actual scour depth from Excel data, but column_diameter for pile if no pile_diameter specified
        actual_pile_diameter = (
            Decimal(str(inputs["pile_diameter"]))
            if float(inputs["pile_diameter"]) > 0
            else Decimal(str(inputs["column_diameter"]))
        )

        forces = calculate_forces(
            Decimal(str(inputs["column_diameter"])),
            decimal_water_depth,
            decimal_water_velocity,
            actual_debris_depth,  # Already a Decimal
            Decimal(str(inputs["cd"])),
            Decimal(str(inputs["log_mass"])),
            Decimal(str(inputs["stopping_distance"])),
            Decimal(str(inputs["load_factor"])),
            actual_pile_diameter,
            Decimal(str(inputs["cd_pile"])),
            decimal_scour_depth,  # Use scour depth from Excel data
        )

        results.append(
            {
                "F1": float(forces["F1"]),
                "L1": float(forces["L1"]),
                "F2": float(forces["F2"]),
                "L2": float(forces["L2"]),
                "F3": float(forces["F3"]),
                "L3": float(forces["L3"]),
                "Fd2": float(forces["Fd2"]),
                "Ld2": float(forces["Ld2"]),
            }
        )

    # Process results and combine with original dataframe
    results_df = pd.DataFrame(results)
    combined_df = pd.concat([df, results_df], axis=1)
    combined_df.replace(
        to_replace=[np.inf, -np.inf, np.nan],
        value="N/A",
        inplace=True,
    )

    # Ensure all object columns are strings for consistent handling
    object_columns = combined_df.select_dtypes(include=["object"]).columns
    for col in object_columns:
        combined_df[col] = combined_df[col].astype(str)

    return combined_df
