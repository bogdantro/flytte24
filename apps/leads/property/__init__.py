# apps/leads/property/ — Norwegian address verification + building-information lookup.
#
# Two stages, kept behind clean seams so a provider can be swapped without the
# wizard (frontend or view) noticing:
#
#   1. kartverket.py  — verify an address against Kartverket / Geonorge (free, keyless)
#   2. providers/     — pluggable building-data provider (mock | norkart | ...)
#       service.py    — PropertyLookupService ties the two together and returns
#                       ONE normalized structure (normalizer.py) regardless of provider
#
# See docs/superpowers/specs/2026-09-02-property-lookup-design.md.
