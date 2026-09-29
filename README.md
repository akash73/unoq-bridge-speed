# How fast is the MCU ↔ MPU Bridge on the UNO Q? Measuring `Bridge.call` vs `Bridge.notify`

The Arduino UNO Q pairs a Linux MPU (running your Python app) with an Arduino/Zephyr
MCU (running your sketch), connected over the **Router Bridge**. Every time your
Python code needs something from the microcontroller — or the microcontroller needs
to push data up — that round trip crosses the Bridge. If you're deciding whether to
poll a sensor with `Bridge.call` or stream samples with `Bridge.notify`, it helps to
know the actual cost of each, in milliseconds, on real hardware.


## The two Bridge primitives

- **`Bridge.call(name, value)`** (Python) / **`Bridge.provide(name, fn)`** (sketch) —
  synchronous. Python blocks until the sketch's handler runs and returns a value.
  This is a true round trip: MPU → MCU → MPU.
- **`Bridge.notify(name, value)`** (Python) / **`Bridge.provide(name, fn)`** (sketch) —
  fire-and-forget. Python sends and moves on immediately; the sketch's handler
  returns nothing. There is no reply, so there is no round trip to measure — only
  the cost of sending.

Because `notify` has no reply, it isn't meaningful to force it into a request/response
shape just to get a comparable "round-trip" number — doing so would measure an
artificial wait, not `notify`'s real cost. Instead, each app measures the primitive
the way it's actually used.

## App 1 — `bridge roundtrip` (measuring `Bridge.call`)

**`sketch/sketch.ino`** exposes a handler that echoes back whatever value it receives:

```cpp
#include <Arduino_RouterBridge.h>

uint32_t ping(uint32_t value) {
    return value;
}

void setup() {
    Serial.begin(115200);
    if (!Bridge.begin()) {
        Serial.println("Bridge initialization failed");
        return;
    }
    Bridge.provide("benchmark_ping", ping);
    Serial.println("Bridge benchmark ready");
}

void loop() {}
```

**`python/main.py`** times 10,000 individual `Bridge.call` round trips (after a
100-call warm-up, to avoid skewing the numbers with one-time costs like cold caches
and buffer allocation), and reports the distribution:

```python
from arduino.app_utils import App, Bridge
import time, statistics, csv

ITERATIONS = 10000
WARMUP = 100

def run_benchmark():
    samples_ms = []
    for i in range(WARMUP):
        Bridge.call("benchmark_ping", i)

    for i in range(ITERATIONS):
        start = time.perf_counter_ns()
        result = Bridge.call("benchmark_ping", i)
        end = time.perf_counter_ns()
        if result != i:
            continue
        samples_ms.append((end - start) / 1_000_000.0)

    # min / median / mean / p95 / p99 / max printed here,
    # then written to bridge_latency.csv

App.run(user_loop=run_benchmark)
```

Each call blocks until the sketch's `ping()` has executed and its return value has
made it back to Python — that's the full round trip.

## App 2 — `bridge notify benchmark` (measuring `Bridge.notify`)

**`sketch/sketch.ino`** just counts what it receives, once per second, and never
sends anything back:

```cpp
#include <Arduino_RouterBridge.h>

volatile uint32_t receivedCount = 0;
unsigned long windowStart = 0;

void onPingNotify(uint32_t value) {
    receivedCount++;
}

void setup() {
    Serial.begin(115200);
    if (!Bridge.begin()) {
        Serial.println("Bridge initialization failed");
        return;
    }
    Bridge.provide("benchmark_ping_notify", onPingNotify);
    Serial.println("Bridge notify benchmark ready");
    windowStart = millis();
}

void loop() {
    if (millis() - windowStart >= 1000) {
        Serial.print("Received/sec: ");
        Serial.println(receivedCount);
        receivedCount = 0;
        windowStart = millis();
    }
}
```

**`python/main.py`** times how long it takes to fire 10,000 notifies back-to-back,
with nothing waiting for a reply — this is the real cost of `notify`, the send side
only:

```python
from arduino.app_utils import App, Bridge
import time

ITERATIONS = 10000
WARMUP = 100

def run_benchmark():
    for i in range(WARMUP):
        Bridge.notify("benchmark_ping_notify", i)

    start = time.perf_counter_ns()
    for i in range(ITERATIONS):
        Bridge.notify("benchmark_ping_notify", i)
    end = time.perf_counter_ns()

    total_ms = (end - start) / 1_000_000.0
    per_op_ms = total_ms / ITERATIONS
    # printed: total_ms, per_op_ms

App.run(user_loop=run_benchmark)
```

Because Python never waits on the sketch here, the two sides run independently —
the sketch's own received-per-second counter (in the Serial Monitor) is a separate,
corroborating measurement.

## Results

Measured on an UNO Q, 10,000 iterations per app (100-call warm-up excluded):

| Metric | Bridge.call (round trip) | Bridge.notify (send only) |
|---|---|---|
| Min | 5.191 ms | — |
| Median | 6.354 ms | — |
| **Mean / avg per op** | **6.423 ms** | **2.362 ms** |
| P95 | 6.717 ms | — |
| P99 | 8.245 ms | — |
| Max | 17.435 ms | — |

`Bridge.notify` has no min/median/p95/max row because it's timed as one 10,000-call
batch (23.6 s total ÷ 10,000), not as individual round trips — there's nothing to
distribute per call without waiting on a reply that doesn't exist.

An interactive chart with the same numbers (headline avg-per-op comparison, plus the
`Bridge.call` latency spread) is in
[`bridge-call-vs-notify-chart.html`](bridge-call-vs-notify-chart.html) — open it in a
browser, or take a screenshot for your Project Hub write-up.

## Takeaways

- **`Bridge.call` costs ~2.7× more per operation than `Bridge.notify`**, because it
  waits for the sketch to run its handler and send a value back — that round trip is
  where the extra ~4 ms goes.
- **Use `Bridge.call`** when you need a value back or a confirmation that the MCU
  acted (reading a sensor, requesting a computed result, anything request/response
  shaped).
- **Use `Bridge.notify`** for high-rate, one-way streams where you don't need — or
  can't afford to wait for — a reply (pushing frequent sensor samples, telemetry,
  fire-and-forget commands like "set this LED").
- Both numbers include one hop each way over the Router Bridge; they're a property
  of the Bridge itself, not of what the handler does (both handlers here do
  essentially nothing), so they're a reasonable estimate of the *floor* latency your
  own Bridge calls will sit on top of.
