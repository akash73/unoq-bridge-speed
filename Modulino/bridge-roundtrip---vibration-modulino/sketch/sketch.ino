#include <Arduino_Modulino.h>
#include <Arduino_RouterBridge.h>

ModulinoMovement movement;

// Reads the latest accelerometer sample from the Modulino Movement sensor
// and returns its X axis value (in g). movement.update() pulls the newest
// sample off the sensor's I2C registers; if called faster than the sensor's
// own output data rate, it returns the same value as the previous call.
float get_accel_x(uint32_t i) {
    movement.update();
    return movement.getX();
}

void setup() {
    Serial.begin(115200);

    if (!Bridge.begin()) {
        Serial.println("Bridge initialization failed");
        return;
    }

    Modulino.begin(Wire1);
    while (!movement.begin()) {
        delay(1000);
    }

    Bridge.provide("benchmark_ping", get_accel_x);

    Serial.println("Bridge benchmark ready (Modulino Movement)");
}

void loop() {
 
}