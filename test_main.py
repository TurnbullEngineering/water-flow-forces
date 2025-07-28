"""Unit tests for the Water Flow Forces Calculator."""

import pytest
from decimal import Decimal
from src.calculations import calculate_forces
from src.constants import LegType
from src.models import PierConfig, BoredPileConfig


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
    assert result["F2"] > 0
    assert result["F3"] > 0
    # Test that heights are within water depth
    assert Decimal("0") <= result["L1"] <= water_depth
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
    assert result["F2"] > 0
    assert result["F3"] > 0
    # Test that heights are within water depth
    assert Decimal("0") <= result["L1"] <= water_depth
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
