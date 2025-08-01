"""Test individual force calculations against engineer-provided values."""

from decimal import Decimal
import pytest
from src.calculations import calculate_forces
from src.constants import LegType
from src.models import PierConfig, BoredPileConfig


@pytest.mark.parametrize(
    "column_diameter,water_depth,average_water_velocity,load_factor,expected_f1",
    [
        # Format: (diameter_m, depth_m, velocity_m_s, load_factor, expected_F1_kN)
        (2.5, 1.482, 1.944, 1.0, 4.901),
        (2.5, 0.485, 0.373, 1.0, 0.059),
    ],
)
def test_water_force_pier(
    column_diameter, water_depth, average_water_velocity, load_factor, expected_f1
):
    """Test F1 calculation for pier type with provided test cases."""
    # Convert inputs to Decimal
    column_diameter = Decimal(str(column_diameter))
    water_depth = Decimal(str(water_depth))
    average_water_velocity = Decimal(str(average_water_velocity))
    load_factor = Decimal(str(load_factor))
    expected_f1 = Decimal(str(expected_f1))

    leg_config: PierConfig = {"diameter": column_diameter}

    result = calculate_forces(
        leg_type=LegType.PIER,
        leg_config=leg_config,
        water_depth=water_depth,
        average_water_velocity=average_water_velocity,
        debris_mat_depth=Decimal("0.0"),
        cd_pier=Decimal("0.7"),
        log_mass=Decimal("1.0"),
        stopping_distance=Decimal("1.0"),
        load_factor=load_factor,
        water_surface_velocity_factor=Decimal("1.0"),
    )

    assert abs(result["F1"] - expected_f1) < Decimal(
        "0.1"
    ), f"F1 = {result['F1']}, expected {expected_f1}"


@pytest.mark.parametrize(
    "wetted_area,average_water_velocity,load_factor,expected_f1",
    [
        # Format: (area_m2, velocity_m_s, load_factor, expected_F1_kN)
        (20.0, 3.0, 1.3, 132.370389438),
    ],
)
def test_water_force_on_pier_bored_pile(
    wetted_area, average_water_velocity, load_factor, expected_f1
):
    """Test F1 calculation for bored pile type with provided test cases."""
    # Convert inputs to Decimal
    wetted_area = Decimal(str(wetted_area))
    average_water_velocity = Decimal(str(average_water_velocity))
    load_factor = Decimal(str(load_factor))
    expected_f1 = Decimal(str(expected_f1))

    leg_config: BoredPileConfig = {"area": wetted_area}

    result = calculate_forces(
        leg_type=LegType.BORED_PILE,
        leg_config=leg_config,
        water_depth=Decimal("1.0"),
        average_water_velocity=average_water_velocity,
        debris_mat_depth=Decimal("0.0"),
        cd_pier=Decimal("0.8"),
        log_mass=Decimal("0.0"),
        stopping_distance=Decimal("1.0"),
        load_factor=load_factor,
        water_surface_velocity_factor=Decimal("1.0"),
        pile_diameter=Decimal("2.5"),  # Diameter irrelevant for bored F1
        cd_pile=Decimal("0.7"),
    )

    assert abs(result["F1"] - expected_f1) < Decimal(
        "0.1"
    ), f"F1 = {result['F1']}, expected {expected_f1}"


@pytest.mark.parametrize(
    "pile_diameter,scour_depth,average_water_velocity,load_factor,expected_fd2",
    [
        # Format: (diameter_m, scour_m, velocity_m_s, load_factor, expected_Fd2_kN)
        (2.5, 1.482, 1.944, 1, 4.901),
        (2.5, 0.485, 0.373, 1, 0.059),
    ],
)
def test_scoured_pile_force(
    pile_diameter, scour_depth, average_water_velocity, load_factor, expected_fd2
):
    """Test Fd2 calculation for scoured pile with provided test cases."""
    # Convert inputs to Decimal
    pile_diameter = Decimal(str(pile_diameter))
    scour_depth = Decimal(str(scour_depth))
    average_water_velocity = Decimal(str(average_water_velocity))
    load_factor = Decimal(str(load_factor))
    expected_fd2 = Decimal(str(expected_fd2))

    leg_config: PierConfig = {"diameter": pile_diameter}

    result = calculate_forces(
        leg_type=LegType.PIER,  # Type doesn't matter for Fd2
        leg_config=leg_config,
        water_depth=Decimal("1.0"),
        average_water_velocity=average_water_velocity,
        debris_mat_depth=Decimal("0.0"),
        cd_pier=Decimal("0.7"),
        log_mass=Decimal("0.0"),
        stopping_distance=Decimal("1.0"),
        load_factor=load_factor,
        water_surface_velocity_factor=Decimal("1.0"),
        pile_diameter=pile_diameter,
        cd_pile=Decimal("0.7"),
        scour_depth=scour_depth,
    )

    assert abs(result["Fd2"] - expected_fd2) < Decimal(
        "0.1"
    ), f"Fd2 = {result['Fd2']}, expected {expected_fd2}"


@pytest.mark.parametrize(
    "water_depth,average_water_velocity,debris_depth,load_factor,expected_f2",
    [
        # Format: (depth_m, velocity_m_s, debris_m, load_factor, expected_F2_kN)
        (1.482, 1.944, 1.482, 1, 190.423),  # No safety factor
    ],
)
def test_debris_force(
    water_depth, average_water_velocity, debris_depth, load_factor, expected_f2
):
    """Test F2 calculation (debris force) with provided test cases."""
    # Convert inputs to Decimal
    water_depth = Decimal(str(water_depth))
    average_water_velocity = Decimal(str(average_water_velocity))
    debris_depth = Decimal(str(debris_depth))
    load_factor = Decimal(str(load_factor))
    expected_f2 = Decimal(str(expected_f2))

    leg_config: PierConfig = {"diameter": Decimal("2.5")}  # Diameter irrelevant for F2

    result = calculate_forces(
        leg_type=LegType.PIER,  # Type doesn't matter for F2
        leg_config=leg_config,
        water_depth=water_depth,
        average_water_velocity=average_water_velocity,
        debris_mat_depth=debris_depth,
        cd_pier=Decimal("0.7"),  # Not used for F2
        log_mass=Decimal("0.0"),
        stopping_distance=Decimal("1.0"),
        load_factor=load_factor,
        water_surface_velocity_factor=Decimal("1.0"),  # Isolate the debris force
    )

    assert abs(result["F2"] - expected_f2) < Decimal(
        "0.1"
    ), f"F2 = {result['F2']}, expected {expected_f2}"


@pytest.mark.parametrize(
    "water_depth,average_water_velocity,log_mass,stopping_distance,load_factor,expected_f3",
    [
        # Format: (depth_m, velocity_m_s, mass_kg, stop_m, load_factor, expected_F3_kN)
        (1.193, 0.863, 10000, 0.025, 1.0, 148.954),
    ],
)
def test_log_impact_force(
    water_depth,
    average_water_velocity,
    log_mass,
    stopping_distance,
    load_factor,
    expected_f3,
):
    """Test F3 calculation (log impact force) with provided test cases."""
    # Convert inputs to Decimal
    water_depth = Decimal(str(water_depth))
    average_water_velocity = Decimal(str(average_water_velocity))
    log_mass = Decimal(str(log_mass))
    stopping_distance = Decimal(str(stopping_distance))
    load_factor = Decimal(str(load_factor))
    expected_f3 = Decimal(str(expected_f3))

    leg_config: PierConfig = {"diameter": Decimal("2.5")}  # Diameter irrelevant for F3

    result = calculate_forces(
        leg_type=LegType.PIER,  # Type doesn't matter for F3
        leg_config=leg_config,
        water_depth=water_depth,
        average_water_velocity=average_water_velocity,
        debris_mat_depth=Decimal("0.0"),
        cd_pier=Decimal("0.7"),  # Not used for F3
        log_mass=log_mass,
        stopping_distance=stopping_distance,
        load_factor=load_factor,
        water_surface_velocity_factor=Decimal("1.0"),  # Isolate the log impact force
    )

    assert abs(result["F3"] - expected_f3) < Decimal(
        "0.1"
    ), f"F3 = {result['F3']}, expected {expected_f3}"
