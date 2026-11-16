"""Framework control catalogues: ISO/IEC 27001:2022 Annex A and SOC 2 (2017 TSC).

Only the control *identifiers* are catalogued here -- enough to validate that a
control in the register maps to a real framework reference, which is what an
auditor or a board risk committee will check first.
"""
from __future__ import annotations

import re

# ISO/IEC 27001:2022 Annex A reorganised the controls into four themes.
# A.5  Organizational controls   A.5.1  - A.5.37  (37)
# A.6  People controls           A.6.1  - A.6.8   (8)
# A.7  Physical controls         A.7.1  - A.7.14  (14)
# A.8  Technological controls    A.8.1  - A.8.34  (34)   => 93 controls total
_ISO_THEME_SIZES = {5: 37, 6: 8, 7: 14, 8: 34}

ISO_27001_2022: set[str] = {
    f"A.{theme}.{n}"
    for theme, size in _ISO_THEME_SIZES.items()
    for n in range(1, size + 1)
}

# SOC 2 Trust Services Criteria (2017, incl. 2022 points of focus).
# Common Criteria CC1-CC9 plus the four optional categories.
_SOC2_SERIES = {
    "CC1": 5, "CC2": 3, "CC3": 4, "CC4": 2, "CC5": 3,
    "CC6": 8, "CC7": 5, "CC8": 1, "CC9": 2,   # security / common criteria
    "A1": 3,            # Availability
    "C1": 2,            # Confidentiality
    "PI1": 5,           # Processing Integrity
    "P1": 1, "P2": 1, "P3": 2, "P4": 3, "P5": 2, "P6": 7, "P7": 1, "P8": 1,  # Privacy
}

SOC2_TSC: set[str] = {
    f"{series}.{n}"
    for series, size in _SOC2_SERIES.items()
    for n in range(1, size + 1)
}

_ISO_RE = re.compile(r"^A\.[5-8]\.\d{1,2}$")
_SOC2_RE = re.compile(r"^(CC[1-9]|A1|C1|PI1|P[1-8])\.\d{1,2}$")


def resolve(control_id: str) -> str:
    """Return the framework name a control id belongs to, or raise ValueError.

    A valid id is both well-formed *and* present in the published catalogue, so
    a plausible-looking but non-existent id (e.g. ``A.5.99``) is rejected.
    """
    cid = control_id.strip()
    if _ISO_RE.match(cid) and cid in ISO_27001_2022:
        return "ISO/IEC 27001:2022"
    if _SOC2_RE.match(cid) and cid in SOC2_TSC:
        return "SOC 2 (2017 TSC)"
    raise ValueError(f"unknown framework control id: {control_id!r}")


def is_valid(control_id: str) -> bool:
    try:
        resolve(control_id)
        return True
    except ValueError:
        return False
