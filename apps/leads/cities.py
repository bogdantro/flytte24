"""
The 5 cities the wizard's map can be pre-centered on via ?by=<slug>.
Verbatim from kobly-full-site-spec.pdf §13.1 / the reference lib/cities.ts.
Reused later by the city marketing pages (a later phase).
"""

CITIES = {
    "oslo": {"name": "Oslo", "lat": 59.9139, "lon": 10.7522, "zoom": 11},
    "bergen": {"name": "Bergen", "lat": 60.3913, "lon": 5.3221, "zoom": 11},
    "trondheim": {"name": "Trondheim", "lat": 63.4305, "lon": 10.3951, "zoom": 11},
    "stavanger": {"name": "Stavanger", "lat": 58.9700, "lon": 5.7331, "zoom": 11},
    "tromso": {"name": "Tromsø", "lat": 69.6492, "lon": 18.9553, "zoom": 11},
}
