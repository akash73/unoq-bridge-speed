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

void loop() {
}