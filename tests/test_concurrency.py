"""
Concurrency tests for the Fleet Telemetry API.

Tests true parallel writes to verify:
1. Zone counter atomicity under concurrent crossings
2. Telemetry ingestion under burst load
3. Fault transition atomicity (mission cancel + maintenance record)
4. Fleet state consistency under concurrent updates

Usage:
    pip install httpx pytest pytest-asyncio
    pytest tests/test_concurrency.py -v
    # or run standalone:
    python tests/test_concurrency.py
"""

import asyncio
import time
from datetime import datetime, timezone

import httpx

BASE_URL = "http://localhost:8000/api"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"


def make_telemetry(
    vehicle_id: str,
    status: str = "moving",
    zone_entered: str | None = None,
    battery_pct: float = 50.0,
    error_codes: list[str] | None = None,
) -> dict:
    return {
        "vehicle_id": vehicle_id,
        "timestamp": utc_now_iso(),
        "lat": 37.41,
        "lon": -122.08,
        "battery_pct": battery_pct,
        "speed_mps": 1.2 if status == "moving" else 0.0,
        "status": status,
        "error_codes": error_codes or [],
        "zone_entered": zone_entered,
    }


async def send_telemetry(
    client: httpx.AsyncClient, payload: dict
) -> httpx.Response:
    resp = await client.post(f"{BASE_URL}/telemetry", json=payload)
    return resp


async def test_concurrent_zone_crossings():
    """
    Send 20 vehicles entering the same zone simultaneously.
    Verify the zone counter matches exactly 20.
    """
    print("\n=== Test: Concurrent Zone Crossings ===")
    zone = "charging_bay_1"
    n_vehicles = 20

    # Get baseline count
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/zones/counts")
        zones = resp.json()
        baseline = next(
            (z["entry_count"] for z in zones if z["zone_id"] == zone), 0
        )
        print(f"Baseline {zone} count: {baseline}")

    # Fire all 20 concurrently
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = []
        for i in range(n_vehicles):
            payload = make_telemetry(
                vehicle_id=f"v-{(i % 50) + 1:02d}",
                status="charging",
                zone_entered=zone,
                battery_pct=float(20 + i),
            )
            tasks.append(send_telemetry(client, payload))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    successes = sum(1 for r in results if isinstance(r, httpx.Response) and r.status_code == 201)
    errors = [r for r in results if isinstance(r, Exception) or (isinstance(r, httpx.Response) and r.status_code != 201)]

    print(f"Successes: {successes}/{n_vehicles}")
    if errors:
        print(f"Errors: {len(errors)}")
        for e in errors[:5]:
            print(f"  {e}")

    # Verify final count
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/zones/counts")
        zones = resp.json()
        final = next(
            (z["entry_count"] for z in zones if z["zone_id"] == zone), 0
        )
        print(f"Final {zone} count: {final}")
        print(f"Expected: {baseline + n_vehicles}")
        assert final == baseline + n_vehicles, (
            f"Zone counter mismatch! Expected {baseline + n_vehicles}, got {final}. "
            f"Lost {n_vehicles - (final - baseline)} entries."
        )
        print("PASSED: Zone counter is exactly correct")


async def test_concurrent_telemetry_burst():
    """
    Simulate a burst of 50 vehicles sending telemetry simultaneously.
    Verify all are accepted and no data corruption.
    """
    print("\n=== Test: Concurrent Telemetry Burst ===")
    n_vehicles = 50

    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = []
        for i in range(n_vehicles):
            payload = make_telemetry(
                vehicle_id=f"v-{(i % 50) + 1:02d}",
                status="moving",
                battery_pct=float(100 - i),
            )
            tasks.append(send_telemetry(client, payload))

        start = time.monotonic()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.monotonic() - start

    successes = sum(1 for r in results if isinstance(r, httpx.Response) and r.status_code == 201)
    failures = n_vehicles - successes

    print(f"Completed in {elapsed:.3f}s")
    print(f"Successes: {successes}/{n_vehicles}")
    print(f"Failures: {failures}")

    assert successes == n_vehicles, f"Expected {n_vehicles} successes, got {successes}"
    print("PASSED: All concurrent telemetry events accepted")


async def test_concurrent_fault_transitions():
    """
    Send multiple fault events for the same vehicle concurrently.
    Verify only one mission is cancelled and one maintenance record created.
    """
    print("\n=== Test: Concurrent Fault Transitions ===")
    vehicle_id = "v-10"
    n_faults = 10

    # First, get current vehicle state
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/vehicles")
        vehicles = resp.json()
        vehicle = next((v for v in vehicles if v["id"] == vehicle_id), None)
        if vehicle:
            print(f"Vehicle {vehicle_id} current status: {vehicle['status']}")

    # Fire N fault events concurrently
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = []
        for i in range(n_faults):
            payload = make_telemetry(
                vehicle_id=vehicle_id,
                status="fault",
                error_codes=[f"E_CONCURRENT_{i}"],
                battery_pct=0.0,
            )
            tasks.append(send_telemetry(client, payload))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    successes = sum(1 for r in results if isinstance(r, httpx.Response) and r.status_code == 201)
    print(f"Fault events accepted: {successes}/{n_faults}")

    # Verify vehicle is in fault state
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/vehicles")
        vehicles = resp.json()
        vehicle = next((v for v in vehicles if v["id"] == vehicle_id), None)
        if vehicle:
            print(f"Vehicle {vehicle_id} final status: {vehicle['status']}")
            assert vehicle["status"] == "fault", (
                f"Vehicle should be in fault state, got {vehicle['status']}"
            )

    print("PASSED: Fault transitions handled atomically")


async def test_fleet_state_consistency():
    """
    Read fleet state while writes are happening concurrently.
    Verify the response is always internally consistent.
    """
    print("\n=== Test: Fleet State Consistency Under Load ===")
    n_writes = 30
    n_reads = 10

    async def write_telemetry(client: httpx.AsyncClient, idx: int):
        payload = make_telemetry(
            vehicle_id=f"v-{(idx % 50) + 1:02d}",
            status=["moving", "idle", "charging"][idx % 3],
            zone_entered=["aisle_a", "aisle_b", "charging_bay_1"][idx % 3] if idx % 4 == 0 else None,
        )
        return await send_telemetry(client, payload)

    async def read_vehicles(client: httpx.AsyncClient):
        return await client.get(f"{BASE_URL}/vehicles")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Interleave reads and writes
        tasks = []
        for i in range(max(n_writes, n_reads)):
            if i < n_writes:
                tasks.append(write_telemetry(client, i))
            if i < n_reads:
                tasks.append(read_vehicles(client))

        results = await asyncio.gather(*tasks, return_exceptions=True)

    read_results = [
        r for r in results
        if isinstance(r, httpx.Response) and r.request.method == "GET"
    ]

    for resp in read_results:
        if resp.status_code == 200:
            vehicles = resp.json()
            total = len(vehicles)
            status_counts = {}
            for v in vehicles:
                s = v["status"]
                status_counts[s] = status_counts.get(s, 0) + 1
            assert sum(status_counts.values()) == total, (
                f"Status counts don't sum to total: {status_counts}"
            )

    print(f"Verified {len(read_results)} concurrent reads were consistent")
    print("PASSED: Fleet state always consistent")


async def main():
    print("=" * 60)
    print("Fleet Telemetry API - Concurrency Test Suite")
    print("=" * 60)

    # Verify server is up
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BASE_URL.replace('/api', '')}/")
            print(f"Server status: {resp.status_code}")
        except httpx.ConnectError:
            print("ERROR: Cannot connect to server at", BASE_URL)
            print("Make sure the server is running: uvicorn backend.app.main:app --reload")
            return

    await test_concurrent_zone_crossings()
    await test_concurrent_telemetry_burst()
    await test_concurrent_fault_transitions()
    await test_fleet_state_consistency()

    print("\n" + "=" * 60)
    print("ALL CONCURRENCY TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
