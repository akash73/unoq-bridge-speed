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
