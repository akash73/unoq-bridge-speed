# 📨 bridge notify benchmark

Measures Bridge.notify without turning it into a fake request/response. Since
`notify` is fire-and-forget (no return value, no built-in reply), it isn't
measured as a round trip. Instead:

- **Python side**: times how long it takes to fire `ITERATIONS` notifies
  (`benchmark_ping_notify`) back-to-back, with nothing waiting for a reply.
  This is the real cost of using `notify` - just the send side, with no
  artificial waiting mixed in.
- **Sketch side**: independently counts how many notifies it receives and
  prints that count once per second to the Serial Monitor. It never sends
  anything back to Python, so the two sides are never waiting on each other.

Before the timed run, `WARMUP` notifies are sent and discarded. This avoids
cold-start bias: the first few calls are typically slower than steady-state
ones due to one-time costs like Python module/JIT caches settling, serial port
buffer allocation, CPU frequency scaling ramping up from idle, and the
MCU-side handler being touched for the first time. Without a warmup, those
slow first calls would skew the measured average away from `notify`'s real
steady-state cost.