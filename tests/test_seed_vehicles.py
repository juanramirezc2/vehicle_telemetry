from datetime import datetime

from backend.app.seed_vehicles import VEHICLE_COUNT, build_seed_vehicles


def test_build_seed_vehicles_generates_expected_ids() -> None:
    vehicles = build_seed_vehicles(updated_at=datetime(2026, 5, 28, 12, 0, 0))

    assert len(vehicles) == VEHICLE_COUNT
    assert [vehicle["id"] for vehicle in vehicles] == [
        f"v-{index}" for index in range(1, VEHICLE_COUNT + 1)
    ]


def test_build_seed_vehicles_populates_required_fields() -> None:
    updated_at = datetime(2026, 5, 28, 12, 0, 0)
    vehicles = build_seed_vehicles(updated_at=updated_at)

    for vehicle in vehicles:
        assert vehicle["status"] in {"idle", "moving", "charging", "fault"}
        assert 50 <= vehicle["battery"] <= 100
        assert vehicle["updated_at"] == updated_at
        assert set(vehicle) == {
            "id",
            "status",
            "battery",
            "current_zone",
            "updated_at",
        }
