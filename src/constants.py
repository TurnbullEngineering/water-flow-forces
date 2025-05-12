"""Constants and configuration values for the Water Flow Forces Calculator."""

from typing import List, Dict
from enum import Enum, auto


class LegType(Enum):
    """Enumeration for different leg types."""

    PIER = auto()
    BORED_PILE = auto()


# Mapping of leg types to their display names
LEG_TYPE_NAMES: Dict[LegType, str] = {
    LegType.PIER: "Pier Type",
    LegType.BORED_PILE: "Bored Pile",
}

# Default Cd values for different leg types
CD_VALUES: Dict[LegType, float] = {
    LegType.PIER: 0.7,  # Default for pier type (uses 0.7 above ground)
    LegType.BORED_PILE: 0.8,  # Default for bored pile (uses 0.8 above ground)
}

# Default pile Cd values (below ground)
CD_PILE_VALUES: Dict[LegType, float] = {
    LegType.PIER: 0.7,  # Same as above ground for pier
    LegType.BORED_PILE: 0.7,  # Same as pier for below ground
}

# Available flood events for analysis
EVENTS: List[str] = ["10% AEP", "1% AEP", "0.5% AEP", "0.2% AEP", "0.05% AEP", "PMF"]

# Default parameter values
DEFAULT_COLUMN_DIAMETER = 2.5  # m
DEFAULT_CD = CD_VALUES[LegType.PIER]  # Semi-circular
DEFAULT_PILE_DIAMETER = 2.5  # m
DEFAULT_CD_PILE = 0.7
DEFAULT_WATER_DEPTH = 8.0  # m
DEFAULT_WATER_VELOCITY = 3.0  # m/s
DEFAULT_SCOUR_DEPTH = 1.0  # m
DEFAULT_MIN_DEBRIS_DEPTH = 1.2  # m
DEFAULT_MAX_DEBRIS_DEPTH = 3.0  # m
DEFAULT_LOG_MASS = 2000  # kg
DEFAULT_STOPPING_DISTANCE = 0.075  # m
DEFAULT_LOAD_FACTOR = 1.3

# Fixed parameters
DEBRIS_SPAN = 20.0  # m

# Calculator description and legal information
CALCULATOR_DESCRIPTION = """
The Water Flow Forces Calculator, developed by Turnbull Engineering Pty Ltd, estimates design forces on transmission tower footings in accordance with AS 5100.2 Section 16 - Forces Resulting from Water Flow.
"""

ENGINEERING_ASSUMPTIONS = """
The tool applies reasonable engineering assumptions, including (but not limited to) a default load factor of 1.3 for the PMF peak flood, reflecting considerations such as climate change, limited redundancy, and inspection/maintenance constraints.
"""

LEGAL_TERMS = """
By using this tool, you acknowledge that you are appropriately qualified to interpret its outputs. Turnbull Engineering Pty Ltd reserves the right to update, modify, or discontinue the software and documentation without notice.
"""

CONTACT_INFO = """
The embedded sheet outlines key assumptions and design input parameters used in the calculations. For bespoke scenarios or custom refinements, please contact Marco.Liang@Turnbullengineering.com.au.
"""

TECHNICAL_ASSUMPTIONS: List[str] = [
    "For pier type, wetted area is calculated as the product of water depth and column diameter.",
    "For bored pile, wetted area is provided directly. Wetted Area is taken as the area of a single face of the triangular leg of transmission tower.",
    "Debris width is assumed to be 20 m.",
    "For water depths less than the minimum debris depth, the minimum depth is adopted per AS 5100.2.",
    "Default load factor is 1.3, actual load factor used for calculations is a parameter.",
]
