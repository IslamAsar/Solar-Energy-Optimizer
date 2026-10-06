/*
 * =========================================================================
 * Project: Solar Energy Optimizer - Arduino Serial Bridge
 * Target: Arduino Uno (ATmega328P) in Proteus Simulation / Hardware
 * Baud Rate: 9600 bps
 * Author: Islam Ahmed Nabil Asar
 * =========================================================================
 * Wiring / Pinout:
 *   - LDR (Solar Light Sensor)               -> Analog Pin A0 (0 - 100%)
 *   - LM35 (Temperature Sensor)              -> Analog Pin A1 (°C)
 *   - POT-HG (Battery Voltage Proxy)         -> Analog Pin A2 (0 - 15V)
 *   - Green LED (Optimal Generation)         -> Digital Pin 8
 *   - Yellow LED (Sub-Optimal Warning)       -> Digital Pin 9
 *   - Red LED (Critical Emergency Alert)     -> Digital Pin 10
 *   - Relay Output (Emergency Load Cutoff)   -> Digital Pin 11 
 * 
 * Proteus COMPIM Settings:
 *   - RXD (Pin 2) -> Arduino RX (Pin 0)
 *   - TXD (Pin 3) -> Arduino TX (Pin 1)
 *   - Physical Port: COM1 | Baud: 9600
 *   - Virtual Baud: 9600
 * =========================================================================
 */

#include "scaler_params.h"

// Analog Sensor Inputs in Proteus
const int PIN_LDR_LIGHT = A0;   // LDR (Solar Irradiance Proxy)
const int PIN_LM35_TEMP = A1;   // LM35 (Panel / Battery Temperature)
const int PIN_POT_VOLT  = A2;   // Potentiometer (Battery Voltage Proxy)

// Digital Actuator & Indicator Outputs
const int PIN_LED_OPTIMAL   = 8;   // Green LED (Normal Operation)
const int PIN_LED_WARNING   = 9;   // Yellow LED (Maintenance Warning)
const int PIN_LED_CRITICAL  = 10;  // Red LED (Critical Hazard Alert)
const int PIN_RELAY_CUTOFF  = 11;  // Relay / MOSFET (Load Cutoff)

/**
 * Autonomous Hardware Actuation based on Edge AI Prediction.
 */
void update_hardware_actuators(OperationalState state) {
  switch (state) {
    case STATE_OPTIMAL:
      digitalWrite(PIN_LED_OPTIMAL, HIGH);
      digitalWrite(PIN_LED_WARNING, LOW);
      digitalWrite(PIN_LED_CRITICAL, LOW);
      digitalWrite(PIN_RELAY_CUTOFF, HIGH); // Load connected
      break;

    case STATE_SUB_OPTIMAL:
      digitalWrite(PIN_LED_OPTIMAL, LOW);
      digitalWrite(PIN_LED_WARNING, HIGH);
      digitalWrite(PIN_LED_CRITICAL, LOW);
      digitalWrite(PIN_RELAY_CUTOFF, HIGH); // Load maintained, maintenance needed
      break;

    case STATE_CRITICAL_ALERT:
      digitalWrite(PIN_LED_OPTIMAL, LOW);
      digitalWrite(PIN_LED_WARNING, LOW);
      digitalWrite(PIN_LED_CRITICAL, HIGH);
      digitalWrite(PIN_RELAY_CUTOFF, LOW);  // Emergency disconnect triggered
      break;
  }
}

void setup() {
  // Initialize Serial interface matching Proteus COMPIM & Python Bridge (9600 baud)
  Serial.begin(9600);
  analogReference(DEFAULT);

  // Configure digital actuator pins
  pinMode(PIN_LED_OPTIMAL, OUTPUT);
  pinMode(PIN_LED_WARNING, OUTPUT);
  pinMode(PIN_LED_CRITICAL, OUTPUT);
  pinMode(PIN_RELAY_CUTOFF, OUTPUT);

  // Set initial safe operational state
  update_hardware_actuators(STATE_OPTIMAL);
  delay(100);
}

void loop() {
  // -----------------------------------------------------------------------
  // 1. Analog Telemetry Acquisition
  // -----------------------------------------------------------------------
  // Read solar irradiance (0.0 to 100.0 %)
  float irradiance = (analogRead(PIN_LDR_LIGHT) / 1023.0f) * 100.0f;

  // Read panel/battery temperature via LM35 (10 mV per degree Celsius)
  float temperature = (analogRead(PIN_LM35_TEMP) * (5.0f / 1023.0f)) * 100.0f;

  // Read battery voltage (0.0 to 15.0 V)
  float voltage = (analogRead(PIN_POT_VOLT) / 1023.0f) * 15.0f;

  // -----------------------------------------------------------------------
  // 2. Feature Engineering
  // -----------------------------------------------------------------------
  // Power Factor Interaction Index
  float powerIndex = (irradiance * voltage) / (temperature + 1.0f);

  // -----------------------------------------------------------------------
  // 3. Edge Normalization (Defined in scaler_params.h)
  // -----------------------------------------------------------------------
  float rawTelemetry[NUM_TELEMETRY_FEATURES] = {
    irradiance,
    temperature,
    voltage,
    powerIndex
  };
  float scaledTelemetry[NUM_TELEMETRY_FEATURES];

  // In-place normalization using compiled StandardScaler parameters
  normalize_features(rawTelemetry, scaledTelemetry);

  // -----------------------------------------------------------------------
  // 4. Edge AI Inference Execution (Defined in scaler_params.h)
  // -----------------------------------------------------------------------
  // Runs the compiled Decision Tree model in-place in RAM (< 1 ms latency)
  OperationalState edgePrediction = predict_edge_state(rawTelemetry, scaledTelemetry);

  // -----------------------------------------------------------------------
  // 5. Hardware Safety Actuation
  // -----------------------------------------------------------------------
  update_hardware_actuators(edgePrediction);

  // -----------------------------------------------------------------------
  // 6. Serial Telemetry Streaming
  // Format: irradiance,temperature,voltage,edge_status_code
  // -----------------------------------------------------------------------
  Serial.print(irradiance, 1);
  Serial.print(",");
  Serial.print(temperature, 1);
  Serial.print(",");
  Serial.print(voltage, 2);
  Serial.print(",");
  Serial.println((int)edgePrediction);
  
  // 250 ms delay (4 samples per second, smooth for 9600 baud and Proteus)
  delay(250);
}
