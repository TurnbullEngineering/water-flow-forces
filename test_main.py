"""Unit tests for the Water Flow Forces Calculator."""

import pytest
import pandas as pd
from decimal import Decimal
from src.calculations import calculate_forces
from src.constants import LegType
from src.data_processing import process_dataframe
from src.app import infer_column_width_from_filename
from src.models import PierConfig, BoredPileConfig


@pytest.mark.parametrize(
    "filename,expected_width",
    [
        ("FF_Export_1500.xlsx", 1.5),
        ("FF_Export_1650.xlsx", 1.65),
        ("FF_Export_3000.xlsx", 3.0),
        ("flood_inputs.xlsx", None),
    ],
)
def test_infer_column_width_from_filename(filename, expected_width):
    """Test extracting per-file column width from FF export filenames."""
    assert infer_column_width_from_filename(filename) == expected_width


def _default_processing_inputs() -> dict:
    return {
        "selected_event": "1% AEP",
        "leg_type": str(LegType.PIER.value),
        "column_diameter": "2.5",
        "cd": "0.7",
        "pile_diameter": "2.5",
        "cd_pile": "0.7",
        "min_debris_depth": "1.2",
        "max_debris_depth": "3.0",
        "log_mass": "2000",
        "stopping_distance": "0.075",
        "load_factor": "1.3",
        "water_surface_velocity_factor": "1.4",
    }


def test_process_dataframe_supports_flat_input_columns():
    """Test processing the original flat input column format."""
    df = pd.DataFrame(
        {
            "Structure Number": ["T001"],
            "1% AEP Event Peak Flood Depth": [1.482],
            "1% AEP Event Peak Velocity": [1.944],
            "1% AEP Event Scour": [0.5],
        }
    )

    result = process_dataframe(df, _default_processing_inputs())

    assert len(result) == 1
    assert result.loc[0, "F1"] > 0
    assert result.loc[0, "Fd2"] > 0


def test_process_dataframe_supports_grouped_ff_export_columns():
    """Test processing FF exports with repeated event headings and metric row."""
    df = pd.DataFrame(
        {
            "Structure Number": [None, None, "T001"],
            "1% AEP Event": ["Peak Flood Depth", None, 1.482],
            "1% AEP Event.1": ["Peak Flood Level", None, 180.876],
            "1% AEP Event.2": ["Peak Velocity", None, 1.944],
            "1% AEP Event.3": ["Scour", None, 0.5],
        }
    )

    result = process_dataframe(df, _default_processing_inputs())

    assert len(result) == 1
    assert result.loc[0, "Structure Number"] == "T001"
    assert result.loc[0, "1% AEP Event Peak Flood Depth"] == 1.482
    assert result.loc[0, "1% AEP Event Peak Velocity"] == 1.944
    assert result.loc[0, "1% AEP Event Scour"] == 0.5
    assert result.loc[0, "F1"] > 0
    assert result.loc[0, "Fd2"] > 0


def test_calculate_forces_pier_type():
    """Test calculate_forces with typical input values for pier type."""
    # Arrange
    leg_type = LegType.PIER
    leg_config: PierConfig = {"diameter": Decimal("2.5")}  # meters
    water_depth = Decimal("8.0")  # meters
    average_water_velocity = Decimal("3.0")  # m/s
    debris_mat_depth = Decimal("2.0")  # meters
    cd = Decimal("0.7")  # drag coefficient
    log_mass = Decimal("10000")  # kg
    stopping_distance = Decimal("0.025")  # meters
    load_factor = Decimal("1.3")

    # Act
    result = calculate_forces(
        leg_type=leg_type,
        leg_config=leg_config,
        water_depth=water_depth,
        average_water_velocity=average_water_velocity,
        debris_mat_depth=debris_mat_depth,
        cd_pier=cd,
        log_mass=log_mass,
        stopping_distance=stopping_distance,
        load_factor=load_factor,
        water_surface_velocity_factor=Decimal("1.4"),
    )

    assert {
        "F1",
        "F2",
        "F3",
        "L1",
        "L2",
        "L3",
    } <= result.keys(), "Result should contain keys: F1, F2, F3, L1, L2, L3"
    # Test that forces are positive
    assert result["F1"] > 0
    assert result["F1a"] + result["F1b"] == result["F1"]
    assert result["F2"] > 0
    assert result["F3"] > 0
    # Test that heights are within water depth
    assert Decimal("0") <= result["L1"] <= water_depth
    assert result["L1a"] == Decimal("3.0")
    assert result["L1b"] == Decimal("7.0")
    assert result["F1a"] / result["F1"] == Decimal("0.75")
    assert result["F1b"] / result["F1"] == Decimal("0.25")
    assert Decimal("0") <= result["L2"] <= water_depth
    assert Decimal("0") <= result["L3"] <= water_depth


def test_calculate_forces_bored_pile_type():
    """Test calculate_forces with typical input values for bored pile type."""
    # Arrange
    leg_type = LegType.BORED_PILE
    leg_config: BoredPileConfig = {"area": Decimal("20.0")}  # m²
    water_depth = Decimal("8.0")  # meters
    average_water_velocity = Decimal("3.0")  # m/s
    debris_mat_depth = Decimal("2.0")  # meters
    cd = Decimal("1.2")  # drag coefficient for circular pile
    log_mass = Decimal("10000")  # kg
    stopping_distance = Decimal("0.025")  # meters
    load_factor = Decimal("1.3")
    pile_diameter = Decimal("2.5")  # must be specified for bored pile

    # Act
    result = calculate_forces(
        leg_type=leg_type,
        leg_config=leg_config,
        water_depth=water_depth,
        average_water_velocity=average_water_velocity,
        debris_mat_depth=debris_mat_depth,
        cd_pier=cd,
        log_mass=log_mass,
        stopping_distance=stopping_distance,
        load_factor=load_factor,
        water_surface_velocity_factor=Decimal("1.4"),
        pile_diameter=pile_diameter,
    )

    assert {"F1", "F2", "F3", "L1", "L2", "L3"} <= result.keys()
    # Test that forces are positive
    assert result["F1"] > 0
    assert result["F1a"] + result["F1b"] == result["F1"]
    assert result["F2"] > 0
    assert result["F3"] > 0
    # Test that heights are within water depth
    assert Decimal("0") <= result["L1"] <= water_depth
    assert abs(result["F1a"] / result["F1"] - Decimal("0.5625")) < Decimal("1e-20")
    assert result["L1a"] == Decimal("4.0")
    assert result["L1b"] > Decimal("6.0")
    assert Decimal("0") <= result["L2"] <= water_depth
    assert Decimal("0") <= result["L3"] <= water_depth


def test_calculate_forces_zero_velocity():
    """Test calculate_forces with zero velocity (should result in zero forces)."""
    # Arrange
    leg_type = LegType.PIER
    leg_config: PierConfig = {"diameter": Decimal("2.5")}
    water_depth = Decimal("8.0")
    average_water_velocity = Decimal("0.0")  # zero velocity
    debris_mat_depth = Decimal("2.0")
    cd = Decimal("0.7")
    log_mass = Decimal("10000")
    stopping_distance = Decimal("0.025")
    load_factor = Decimal("1.3")

    # Act
    result = calculate_forces(
        leg_type=leg_type,
        leg_config=leg_config,
        water_depth=water_depth,
        average_water_velocity=average_water_velocity,
        debris_mat_depth=debris_mat_depth,
        cd_pier=cd,
        log_mass=log_mass,
        stopping_distance=stopping_distance,
        load_factor=load_factor,
        water_surface_velocity_factor=Decimal("1.4"),
    )

    # Assert
    assert result["F1"] == 0
    assert result["F1a"] == 0
    assert result["F1b"] == 0
    assert result["F2"] == 0
    assert result["F3"] == 0
    # Heights should still be valid
    assert result["L1"] == water_depth / 2
    assert result["L2"] == water_depth - (debris_mat_depth / 2)
    assert result["L3"] == water_depth


def test_calculate_forces_debris_depth_exceeding_water():
    """Test when debris mat depth exceeds water depth."""
    # Arrange
    leg_type = LegType.PIER
    leg_config: PierConfig = {"diameter": Decimal("2.5")}
    water_depth = Decimal("2.0")  # shallow water
    average_water_velocity = Decimal("3.0")
    debris_mat_depth = Decimal("4.0")  # exceeds water depth
    cd = Decimal("0.7")
    log_mass = Decimal("10000")
    stopping_distance = Decimal("0.025")
    load_factor = Decimal("1.3")

    # Act
    result = calculate_forces(
        leg_type=leg_type,
        leg_config=leg_config,
        water_depth=water_depth,
        average_water_velocity=average_water_velocity,
        debris_mat_depth=debris_mat_depth,
        cd_pier=cd,
        log_mass=log_mass,
        stopping_distance=stopping_distance,
        load_factor=load_factor,
        water_surface_velocity_factor=Decimal("1.4"),
    )

    # Assert
    # Test that L2 is at half the debris depth
    assert (
        result["L2"] == debris_mat_depth / 2
    ), "L2 should be at half the debris mat depth when it exceeds water depth."

    # Calculate forces with same parameters but water depth is half of original
    result_with_half_water_depth = calculate_forces(
        leg_type=leg_type,
        leg_config=leg_config,
        water_depth=water_depth / Decimal("2"),
        average_water_velocity=average_water_velocity,
        debris_mat_depth=debris_mat_depth,
        cd_pier=cd,
        log_mass=log_mass,
        stopping_distance=stopping_distance,
        load_factor=load_factor,
        water_surface_velocity_factor=Decimal("1.4"),
    )

    # F2 should be the same in both cases since it's limited by water depth
    assert (
        result["F2"] == result_with_half_water_depth["F2"]
    ), "F2 should not change with water depth if debris mat depth exceeds water depth."


def test_calculate_forces_validates_inputs():
    """Test that the function validates input types."""
    # Arrange
    valid_inputs = {
        "leg_type": LegType.PIER,
        "leg_config": {"diameter": Decimal("2.5")},
        "water_depth": Decimal("8.0"),
        "average_water_velocity": Decimal("3.0"),
        "debris_mat_depth": Decimal("2.0"),
        "cd_pier": Decimal("0.7"),
        "log_mass": Decimal("10000"),
        "stopping_distance": Decimal("0.025"),
        "load_factor": Decimal("1.3"),
        "water_surface_velocity_factor": Decimal("1.4"),
    }

    # Test each parameter with wrong type (except leg_type since it's an enum)
    skip_params = {"leg_type"}
    for param in valid_inputs:
        if param in skip_params:
            continue
        invalid_inputs = valid_inputs.copy()
        invalid_inputs[param] = 1.23  # type: ignore  # Testing invalid type handling

        # Act/Assert
        with pytest.raises((TypeError, AttributeError)):
            calculate_forces(**invalid_inputs)


def test_bored_pile_requires_pile_diameter():
    """Test that bored pile type requires pile_diameter to be specified."""
    # Arrange
    leg_type = LegType.BORED_PILE
    leg_config: BoredPileConfig = {"area": Decimal("20.0")}
    water_depth = Decimal("8.0")
    average_water_velocity = Decimal("3.0")
    debris_mat_depth = Decimal("2.0")
    cd = Decimal("1.2")
    log_mass = Decimal("10000")
    stopping_distance = Decimal("0.025")
    load_factor = Decimal("1.3")

    # Act/Assert
    with pytest.raises(ValueError):
        calculate_forces(
            leg_type=leg_type,
            leg_config=leg_config,
            water_depth=water_depth,
            average_water_velocity=average_water_velocity,
            debris_mat_depth=debris_mat_depth,
            cd_pier=cd,
            log_mass=log_mass,
            stopping_distance=stopping_distance,
            load_factor=load_factor,
            water_surface_velocity_factor=Decimal("1.4"),
            # pile_diameter not provided
        )
