from arduino.app_utils import App, Bridge
import time

ITERATIONS = 10000
WARMUP = 100

benchmark_done = False

def run_benchmark():
    global benchmark_done
    if benchmark_done:
        time.sleep(1)
        return
    benchmark_done = True

    print("Warming up...", flush=True)

    for i in range(WARMUP):
        Bridge.notify("benchmark_ping_notify", i)

    print("Running benchmark...", flush=True)

    start = time.perf_counter_ns()

    for i in range(ITERATIONS):
        Bridge.notify("benchmark_ping_notify", i)

    end = time.perf_counter_ns()

    total_ms = (end - start) / 1_000_000.0
    per_op_ms = total_ms / ITERATIONS

    print(flush=True)
    print("UNO Q MCU <-> MPU Bridge NOTIFY benchmark (send-only, no wait)", flush=True)
    print("----------------------------------------------------------------", flush=True)
    print(f"Samples    : {ITERATIONS}", flush=True)
    print(f"Total time : {total_ms:.3f} ms", flush=True)
    print(f"Avg per op : {per_op_ms:.4f} ms", flush=True)
    print(flush=True)
    print("Check the Serial Monitor for the sketch's received-messages-per-second count.", flush=True)

App.run(user_loop=run_benchmark)