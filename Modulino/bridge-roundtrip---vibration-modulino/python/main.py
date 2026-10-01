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
    x_values = []
    duplicate_reads = 0

    print("Warming up...")

    for i in range(WARMUP):
        Bridge.call("benchmark_ping", i)

    print("Running benchmark...")

    last_x = None

    for i in range(ITERATIONS):

        start = time.perf_counter_ns()

        x_accel = Bridge.call("benchmark_ping", i)

        end = time.perf_counter_ns()

        rtt_ms = (end - start) / 1_000_000.0
        samples_ms.append(rtt_ms)
        x_values.append(x_accel)

        if last_x is not None and x_accel == last_x:
            duplicate_reads += 1
        last_x = x_accel

    mean_ms = statistics.mean(samples_ms)

    print()
    print("UNO Q MCU <-> MPU Modulino Movement acquisition benchmark")
    print("-----------------------------------------------------------")
    print(f"Samples          : {len(samples_ms)}")
    print(f"Min              : {min(samples_ms):.3f} ms")
    print(f"Median           : {statistics.median(samples_ms):.3f} ms")
    print(f"Mean             : {mean_ms:.3f} ms")

    sorted_samples = sorted(samples_ms)

    def percentile(data, p):
        index = int((len(data) - 1) * p)
        return data[index]

    print(f"P95              : {percentile(sorted_samples, 0.95):.3f} ms")
    print(f"P99              : {percentile(sorted_samples, 0.99):.3f} ms")
    print(f"Max              : {max(samples_ms):.3f} ms")
    print(f"Effective rate   : {1000.0 / mean_ms:.1f} samples/sec")
    print(f"Duplicate reads  : {duplicate_reads}/{len(samples_ms)} "
          f"({100.0 * duplicate_reads / len(samples_ms):.1f}%) - back-to-back reads "
          f"with the same X value, i.e. polled faster than the sensor produced a new sample")

    with open("bridge_latency.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["iteration", "rtt_ms", "x_accel_g"])

        for i, (value, x_accel) in enumerate(zip(samples_ms, x_values)):
            writer.writerow([i, value, x_accel])

    print()
    print("Results written to bridge_latency.csv")

App.run(user_loop=run_benchmark)

