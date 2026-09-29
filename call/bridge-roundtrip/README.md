# 😀 bridge roundtrip

Measures the round-trip latency of `Bridge.call` between the MPU (Python) and the MCU (sketch) on the Arduino UNO Q.

## How it works

- The sketch (`sketch/sketch.ino`) registers a handler `benchmark_ping` via `Bridge.provide()` that simply echoes back the `uint32_t` value it receives.
- The Python app (`python/main.py`) calls `Bridge.call("benchmark_ping", i)` in a loop, timing each call with `time.perf_counter_ns()` and verifying the echoed value matches what was sent.
- A `user_loop` (`run_benchmark`) runs once via `App.run(user_loop=...)`: it does 100 warm-up calls (discarded), then 10,000 timed calls, and guards against re-running with a `benchmark_done` flag (subsequent loop iterations just sleep).

## Output

On completion, the app prints round-trip time statistics (min, median, mean, P95, P99, max) to the console, and writes every sample to `bridge_latency.csv` (columns: `iteration`, `rtt_ms`) in the app's working directory for further analysis.

## Running it

Start the app from App Lab. It runs the benchmark once (~10k roundtrips) and then idles. Check the app logs for the printed summary, and check out the app again to inspect `bridge_latency.csv` for the raw per-call data.

## Notes

- No bricks are required (`app.yaml` declares `bricks: []`); the sketch only depends on `Arduino_RouterBridge.h`.
- `ITERATIONS` and `WARMUP` in `python/main.py` can be tuned to change sample size.
