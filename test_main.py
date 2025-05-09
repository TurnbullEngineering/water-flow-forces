"""Unit tests for the Water Flow Forces Calculator."""

import pytest
from decimal import Decimal
from src.calculations import calculate_forces


def test_calculate_forces_normal_case():
    """Test calculate_forces with typical input values."""
    # Arrange
    column_diameter = Decimal("2.5")  # meters
    water_depth = Decimal("8.0")  # meters
    water_velocity = Decimal("3.0")  # m/s
    debris_mat_depth = Decimal("2.0")  # meters
    cd = Decimal("0.7")  # drag coefficient
    log_mass = Decimal("10000")  # kg
    stopping_distance = Decimal("0.025")  # meters
    load_factor = Decimal("1.3")

    # Act
    result = calculate_forces(
        column_diameter,
        water_depth,
        water_velocity,
        debris_mat_depth,
        cd,
        log_mass,
        stopping_distance,
        load_factor,
    )

    assert {"F1", "F2", "F3", "L1", "L2", "L3"} <= result.keys(), (
        "Result should contain keys: F1, F2, F3, L1, L2, L3"
    )
    # Test that forces are positive
    assert result["F1"] > 0
    assert result["F2"] > 0
    assert result["F3"] > 0
    # Test that heights are within water depth
    assert Decimal("0") <= result["L1"] <= water_depth
    assert Decimal("0") <= result["L2"] <= water_depth
    assert Decimal("0") <= result["L3"] <= water_depth


def test_calculate_forces_zero_velocity():
    """Test calculate_forces with zero velocity (should result in zero forces)."""
    # Arrange
    column_diameter = Decimal("2.5")
    water_depth = Decimal("8.0")
    water_velocity = Decimal("0.0")  # zero velocity
    debris_mat_depth = Decimal("2.0")
    cd = Decimal("0.7")
    log_mass = Decimal("10000")
    stopping_distance = Decimal("0.025")
    load_factor = Decimal("1.3")

    # Act
    result = calculate_forces(
        column_diameter,
        water_depth,
        water_velocity,
        debris_mat_depth,
        cd,
        log_mass,
        stopping_distance,
        load_factor,
    )

    # Assert
    assert result["F1"] == 0
    assert result["F2"] == 0
    assert result["F3"] == 0
    # Heights should still be valid
    assert result["L1"] == water_depth / 2
    assert result["L2"] == water_depth - (debris_mat_depth / 2)
    assert result["L3"] == water_depth


def test_calculate_forces_debris_depth_exceeding_water():
    """Test when debris mat depth exceeds water depth."""
    # Arrange
    column_diameter = Decimal("2.5")
    water_depth = Decimal("2.0")  # shallow water
    water_velocity = Decimal("3.0")
    debris_mat_depth = Decimal("4.0")  # exceeds water depth
    cd = Decimal("0.7")
    log_mass = Decimal("10000")
    stopping_distance = Decimal("0.025")
    load_factor = Decimal("1.3")

    # Act
    result = calculate_forces(
        column_diameter,
        water_depth,
        water_velocity,
        debris_mat_depth,
        cd,
        log_mass,
        stopping_distance,
        load_factor,
    )

    # Assert
    # Test that L2 is at half the debris depth
    assert result["L2"] == debris_mat_depth / 2, (
        "L2 should be at half the debris mat depth when it exceeds water depth."
    )

    # Calculate forces with same parameters but water depth is half of original
    result_with_half_water_depth = calculate_forces(
        column_diameter,
        water_depth / Decimal("2"),
        water_velocity,
        debris_mat_depth,
        cd,
        log_mass,
        stopping_distance,
        load_factor,
    )

    # F2 should be the same in both cases since it's limited by water depth
    assert result["F2"] == result_with_half_water_depth["F2"], (
        "F2 should not change with water depth if debris mat depth exceeds water depth."
    )


def test_calculate_forces_validates_inputs():
    """Test that the function validates input types."""
    # Arrange
    valid_inputs = {
        "column_diameter": Decimal("2.5"),
        "water_depth": Decimal("8.0"),
        "water_velocity": Decimal("3.0"),
        "debris_mat_depth": Decimal("2.0"),
        "cd": Decimal("0.7"),
        "log_mass": Decimal("10000"),
        "stopping_distance": Decimal("0.025"),
        "load_factor": Decimal("1.3"),
    }

    # Test each parameter with wrong type
    for param in valid_inputs:
        invalid_inputs = valid_inputs.copy()
        invalid_inputs[param] = 1.23  # type: ignore  # Testing invalid type handling

        # Act/Assert
        with pytest.raises((TypeError, AttributeError)):
            calculate_forces(**invalid_inputs)
