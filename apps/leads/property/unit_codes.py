# apps/leads/property/unit_codes.py
#
# Parsing a Norwegian bruksenhetsnummer (unit code) such as "H0201".
#
# Format, per Matrikkelforskriften § 60 (and the Matrikkelen "bruksenhet"
# documentation): a single letter, then two digits for the floor within that
# level, then two digits for the running number of the unit on that floor.
#
#   letter  meaning
#   ------  -----------------------------------------------------------------
#   H       hoveddel / bolig over bakken (main residential floors above ground)
#   L       loft (attic)
#   U       underetasje (partly-below-ground floor)
#   K       kjeller (basement)
#
#   "H0201"  ->  level H, floor 2, unit 1 on that floor
#   "U0101"  ->  level U (underetasje), floor 1, unit 1
#
# IMPORTANT: this is a *fallback* only. Prefer an explicit floor value from the
# building-data provider whenever it gives one; call this just to fill a gap.
# All parsing logic for unit codes lives in this one function — do not scatter
# equivalent slicing/regex around the views or JavaScript.

import re

_UNIT_CODE_RE = re.compile(r"^(?P<letter>[A-Za-z])(?P<floor>\d{2})(?P<running>\d{2})$")

_LEVEL_LABELS = {
    "H": "etasje",        # rendered as "2. etasje"
    "L": "loft",
    "U": "underetasje",
    "K": "kjeller",
}


def parse_bruksenhet_code(code):
    """Parse a bruksenhetsnummer like "H0201" into its parts.

    Returns a dict:
        {
            "raw": "H0201",
            "level_type": "H",            # H | L | U | K (upper-cased)
            "level_label": "etasje",      # Norwegian label for the level
            "floor": 2,                   # int, floor within the level
            "running_no": 1,              # int, unit's number on that floor
            "floor_label": "2. etasje",   # display string, or e.g. "Underetasje"
        }

    Returns None for anything that isn't a well-formed code (empty, wrong
    length, non-digits, unknown letter) — the caller then simply has no
    fallback floor, which is fine.
    """
    if not code or not isinstance(code, str):
        return None
    match = _UNIT_CODE_RE.match(code.strip())
    if not match:
        return None

    letter = match.group("letter").upper()
    if letter not in _LEVEL_LABELS:
        return None

    floor = int(match.group("floor"))
    running_no = int(match.group("running"))
    level_label = _LEVEL_LABELS[letter]

    if letter == "H":
        floor_label = f"{floor}. etasje"
    elif floor <= 1:
        floor_label = level_label.capitalize()
    else:
        floor_label = f"{level_label.capitalize()} {floor}"

    return {
        "raw": code.strip(),
        "level_type": letter,
        "level_label": level_label,
        "floor": floor,
        "running_no": running_no,
        "floor_label": floor_label,
    }


def floor_from_unit_code(code):
    """Just the human-readable floor label for a unit code ("H0201" -> "2. etasje"),
    or None. Convenience wrapper for the normalizer's fallback path."""
    parsed = parse_bruksenhet_code(code)
    return parsed["floor_label"] if parsed else None
