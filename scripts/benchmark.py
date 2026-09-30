import time
import httpx

CONTROLLER_URL = "http://127.0.0.1:8000"

def run_benchmarks():
    print("==================================================")
    print("      PS-023 Live Performance Benchmark           ")
    print("==================================================")

    # 1. API Health Latency
    times = []
    for _ in range(10):
        t0 = time.perf_counter()
        r = httpx.get(f"{CONTROLLER_URL}/health")
        t1 = time.perf_counter()
        if r.status_code == 200:
            times.append((t1 - t0) * 1000)
    avg_latency = sum(times) / len(times) if times else 0
    print(f"[1] Controller API Health Latency:  {avg_latency:.2f} ms")

    # 2. Node List Latency
    t0 = time.perf_counter()
    r = httpx.get(f"{CONTROLLER_URL}/nodes")
    t1 = time.perf_counter()
    nodes = r.json() if r.status_code == 200 else []
    print(f"[2] Cluster Node Query Latency:    {(t1 - t0) * 1000:.2f} ms (Found {len(nodes)} nodes)")

    # 3. VM Creation + Scheduling Roundtrip
    t0 = time.perf_counter()
    payload = {
        "name": f"bench-vm-{int(time.time())}",
        "cpu": 1,
        "memory_mb": 1024,
        "disk_gb": 10,
        "image": "ubuntu-24.04"
    }
    r = httpx.post(f"{CONTROLLER_URL}/vms", json=payload)
    t1 = time.perf_counter()
    if r.status_code == 201:
        vm = r.json()
        print(f"[3] VM Provision & Schedule Time:  {(t1 - t0):.3f} sec (Assigned to {vm.get('node_id')})")
        
        # 4. VM Stop Latency
        vm_id = vm["id"]
        t0 = time.perf_counter()
        r = httpx.post(f"{CONTROLLER_URL}/vms/{vm_id}/stop")
        t1 = time.perf_counter()
        print(f"[4] VM Stop Operation Latency:     {(t1 - t0):.3f} sec")

        # 5. VM Delete Latency
        t0 = time.perf_counter()
        r = httpx.delete(f"{CONTROLLER_URL}/vms/{vm_id}")
        t1 = time.perf_counter()
        print(f"[5] VM Deletion Latency:           {(t1 - t0):.3f} sec")
    else:
        print(f"[3] VM Creation failed: {r.status_code} {r.text}")

    print("==================================================")

if __name__ == "__main__":
    run_benchmarks()
