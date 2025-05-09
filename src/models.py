"""Type definitions for the Water Flow Forces Calculator."""

from typing import TypedDict
from decimal import Decimal


class ForceResults(TypedDict):
    """Type hints for force calculation results.

    Attributes
    ----------
    F1 : Decimal
        Water Flow Force on pier (kN)
    L1 : Decimal
        Height of F1 application (m)
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

    F1: Decimal  # Water Flow Force on pier (kN)
    L1: Decimal  # Height of F1 application (m)
    F2: Decimal  # Debris Force (kN)
    L2: Decimal  # Height of F2 application (m)
    F3: Decimal  # Log Impact Force (kN)
    L3: Decimal  # Height of F3 application (m)
    Fd2: Decimal  # Water Flow Force on pile (kN)
    Ld2: Decimal  # Height of Fd2 application, must be negative (m)
