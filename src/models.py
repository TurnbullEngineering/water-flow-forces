"""Type definitions for the Water Flow Forces Calculator."""

from typing import TypedDict, Union
from decimal import Decimal


class ForceResults(TypedDict):
    """Type hints for force calculation results.

    Attributes
    ----------
    F1 : Decimal
        Total water-flow force, equal to F1a + F1b (kN)
    L1 : Decimal
        Height of total F1 application (m)
    F1a : Decimal
        Water-flow force on the clear lower portion below the debris mat (kN)
    L1a : Decimal
        Height of F1a application (m)
    F1b : Decimal
        Water-flow force on the debris-covered upper portion (kN)
    L1b : Decimal
        Height of F1b application (m)
    F2 : Decimal
        Debris Force (kN)
    L2 : Decimal
        Height of F2 application (m)
    F3 : Decimal
        Log Impact Force (kN)
    L3 : Decimal
        Height of F3 application (m)
    Fd2 : Decimal
        Water Flow Force on pile (kN)
    Ld2 : Decimal
        Height of Fd2 application, must be negative (m)
    """

    F1: Decimal  # Total water-flow force, F1a + F1b (kN)
    L1: Decimal  # Height of total F1 application (m)
    F1a: Decimal  # Clear lower-portion water-flow force (kN)
    L1a: Decimal  # Height of F1a application (m)
    F1b: Decimal  # Debris-covered upper-portion water-flow force (kN)
    L1b: Decimal  # Height of F1b application (m)
    F2: Decimal  # Debris Force (kN)
    L2: Decimal  # Height of F2 application (m)
    F3: Decimal  # Log Impact Force (kN)
    L3: Decimal  # Height of F3 application (m)
    Fd2: Decimal  # Water Flow Force on pile (kN)
    Ld2: Decimal  # Height of Fd2 application, must be negative (m)


class PierConfig(TypedDict):
    """Configuration for pier type leg.

    Attributes
    ----------
    diameter : Decimal
        Diameter of the pier (m)
    """

    diameter: Decimal


class BoredPileConfig(TypedDict):
    """Configuration for bored pile type leg.

    Attributes
    ----------
    area : Decimal
        Area of the pile (m²)
    """

    area: Decimal


# Union type for leg configuration
LegConfig = Union[PierConfig, BoredPileConfig]
