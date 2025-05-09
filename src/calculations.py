"""Core calculation functions for the Water Flow Forces Calculator."""

from decimal import Decimal
from .models import ForceResults, PierConfig, BoredPileConfig, LegConfig
from .constants import DEBRIS_SPAN, LegType


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
    leg_type: LegType,
    leg_config: LegConfig,
    water_depth: Decimal,
    water_velocity: Decimal,
    debris_mat_depth: Decimal,
    cd_pier: Decimal,
    log_mass: Decimal,
    stopping_distance: Decimal,
    load_factor: Decimal,
    pile_diameter: Decimal = Decimal("0"),
    cd_pile: Decimal = Decimal("0"),
    scour_depth: Decimal = Decimal("0"),
) -> ForceResults:
    """
    Calculate forces using Decimal for consistent precision.

    Parameters
    ----------
    leg_type : LegType
        Type of leg (PIER or BORED_PILE)
    leg_config : LegConfig
        Configuration for the leg type (PierConfig or BoredPileConfig)
    water_depth : Decimal
        Depth of water (m)
    water_velocity : Decimal
        Velocity of water flow (m/s)
    debris_mat_depth : Decimal
        Depth of debris mat (m)
    cd_pier : Decimal
        Drag coefficient for pier
    log_mass : Decimal
        Mass of log for impact calculation (kg)
    stopping_distance : Decimal
        Distance over which log stops (m)
    load_factor : Decimal
        Safety factor applied to forces
    pile_diameter : Decimal, optional
        Diameter of pile (m), defaults to column_diameter if 0
    cd_pile : Decimal, optional
        Drag coefficient for pile
    scour_depth : Decimal, optional
        Depth of scour below ground (m)

    Returns
    -------
    ForceResults
        Dictionary containing calculated forces and their application heights

    Raises
    ------
    ValueError
        If scour_depth or pile_diameter is negative
    TypeError
        If leg_config doesn't match leg_type
    """
    # Calculate above-ground forces based on leg type
    if leg_type == LegType.PIER:
        # Pier type: use diameter and water depth for wetted area
        if not isinstance(leg_config, dict) or "diameter" not in leg_config:
            raise TypeError("Pier type requires PierConfig with diameter")
        column_diameter = leg_config["diameter"]
        Ad = water_depth * column_diameter
        F1 = Decimal("0.5") * cd_pier * (water_velocity**2) * Ad * load_factor
        L1 = water_depth / Decimal("2")  # Mid-height for pier type
    else:
        # Bored pile type: use explicit area and 2/3 water depth
        if not isinstance(leg_config, dict) or "area" not in leg_config:
            raise TypeError("Bored pile type requires BoredPileConfig with area")
        # area is just the area of a single face of the triangular leg of transmission tower
        # critical case is 45 degrees, and there are two faces
        # so the wetted area normal to the flow is area * sqrt(2)
        Ad = leg_config["area"] * Decimal("2").sqrt()
        F1 = Decimal("0.5") * cd_pier * (water_velocity**2) * Ad * load_factor
        L1 = (Decimal("2") * water_depth) / Decimal("3")  # 2/3 height for bored pile

    # Calculate debris forces (same for both types)
    debris_span = Decimal(str(DEBRIS_SPAN))  # m
    Adeb = debris_mat_depth * debris_span
    C_debris = Cd(water_velocity, water_depth)
    F2 = Decimal("0.5") * C_debris * (water_velocity**2) * Adeb * load_factor
    L2 = max(
        water_depth - (debris_mat_depth / Decimal("2")), debris_mat_depth / Decimal("2")
    )

    # Calculate log impact force
    acceleration = (water_velocity**2) / (Decimal("2") * stopping_distance)
    F3 = log_mass * acceleration * load_factor / Decimal("1000")  # Convert to kN
    L3 = water_depth

    if scour_depth < 0 or pile_diameter < 0:
        raise ValueError("Scour depth and pile diameter must be non-negative.")

    # Use column diameter if no pile diameter specified
    # Validate and get pile diameter
    if pile_diameter == 0:
        if leg_type == LegType.PIER:
            if isinstance(leg_config, dict) and "diameter" in leg_config:
                pile_diameter = leg_config["diameter"]  # type: ignore
            else:
                raise TypeError("Pier type requires PierConfig with diameter")
        else:  # BORED_PILE
            raise ValueError("Pile diameter must be specified for bored pile type")

    Ad2 = scour_depth * pile_diameter  # Forces only apply to scoured area
    # Fd2 - Water Flow Force on pile
    Fd2 = Decimal("0.5") * cd_pile * (water_velocity**2) * Ad2 * load_factor
    Ld2 = -scour_depth / Decimal("2")  # Force acts at midpoint of scoured area

    return {
        "F1": F1,  # Water Flow Force (kN)
        "L1": L1,  # Height of F1 application (m)
        "F2": F2,  # Debris Force (kN)
        "L2": L2,  # Height of F2 application (m)
        "F3": F3,  # Log Impact Force (kN)
        "L3": L3,  # Height of F3 application (m)
        "Fd2": Fd2,  # Water Flow Force on pile (kN)
        "Ld2": Ld2,  # Height of Fd2 application (m)
    }
