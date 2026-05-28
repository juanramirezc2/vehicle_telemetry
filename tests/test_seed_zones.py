from datetime import datetime

from backend.app.seed_zones import ZONES, build_seed_zones


def test_build_seed_zones_generates_expected_ids() -> None:
    zones = build_seed_zones(updated_at=datetime(2026, 5, 28, 12, 0, 0))

    assert len(zones) == 20
    assert [zone["zone_id"] for zone in zones] == ZONES


def test_build_seed_zones_populates_required_fields() -> None:
    updated_at = datetime(2026, 5, 28, 12, 0, 0)
    zones = build_seed_zones(updated_at=updated_at)

    for zone in zones:
        assert zone["entry_count"] == 0
        assert zone["updated_at"] == updated_at
        assert set(zone) == {
            "zone_id",
            "entry_count",
            "updated_at",
        }
