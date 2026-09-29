from arduino.app_utils import App, Bridge
import time
import statistics
import csv

ITERATIONS = 10000
WARMUP = 100

benchmark_done = False

def run_benchmark():
    global benchmark_done
    if benchmark_done:
        time.sleep(1)
        return
    benchmark_done = True

    samples_ms = []

    print("Warming up...")

    for i in range(WARMUP):
        Bridge.call("benchmark_ping", i)

    print("Running benchmark...")

    for i in range(ITERATIONS):

        start = time.perf_counter_ns()

        result = Bridge.call("benchmark_ping", i)

        end = time.perf_counter_ns()

        if result != i:
            print(f"ERROR: sent {i}, received {result}")
            continue

        rtt_ms = (end - start) / 1_000_000.0
        samples_ms.append(rtt_ms)

    print()
    print("UNO Q MCU <-> MPU Bridge benchmark")
    print("----------------------------------")
    print(f"Samples : {len(samples_ms)}")
    print(f"Min     : {min(samples_ms):.3f} ms")
    print(f"Median  : {statistics.median(samples_ms):.3f} ms")
    print(f"Mean    : {statistics.mean(samples_ms):.3f} ms")

    sorted_samples = sorted(samples_ms)

    def percentile(data, p):
        index = int((len(data) - 1) * p)
        return data[index]

    print(f"P95     : {percentile(sorted_samples, 0.95):.3f} ms")
    print(f"P99     : {percentile(sorted_samples, 0.99):.3f} ms")
    print(f"Max     : {max(samples_ms):.3f} ms")

    with open("bridge_latency.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["iteration", "rtt_ms"])

        for i, value in enumerate(samples_ms):
            writer.writerow([i, value])

    print()
    print("Results written to bridge_latency.csv")

App.run(user_loop=run_benchmark)

