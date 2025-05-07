import pytest
from decimal import Decimal
from main import calculate_forces


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

    # Assert
    assert isinstance(result, dict)
    assert all(isinstance(v, Decimal) for v in result.values())
    assert set(result.keys()) == {"F1", "L1", "F2", "L2", "F3", "L3"}
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
    assert result["L2"] == debris_mat_depth / 2


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
