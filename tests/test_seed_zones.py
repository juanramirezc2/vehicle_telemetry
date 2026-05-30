import random
from datetime import datetime

from backend.app.seed_zones import ZONES, build_seed_zones


def test_build_seed_zones_generates_expected_ids() -> None:
    zones = build_seed_zones(now=datetime(2026, 5, 28, 12, 0, 0), rng=random.Random(1))

    assert len(zones) == len(ZONES)
    assert [zone["zone_id"] for zone in zones] == ZONES


def test_build_seed_zones_populates_required_fields() -> None:
    now = datetime(2026, 5, 28, 12, 0, 0)
    zones = build_seed_zones(now=now, rng=random.Random(7))

    for zone in zones:
        assert 0 <= zone["entry_count"] <= 500
        assert zone["updated_at"] <= now
        assert set(zone) == {
            "zone_id",
            "entry_count",
            "updated_at",
        }


def test_build_seed_zones_produces_varied_counts() -> None:
    zones = build_seed_zones(rng=random.Random(42))
    counts = [zone["entry_count"] for zone in zones]

    assert len(set(counts)) > 1
