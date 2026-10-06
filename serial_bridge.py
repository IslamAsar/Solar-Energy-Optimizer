"""
Serial to Flask API Bridge (Arduino Uno Integration)
Reads telemetry from COM2 and sends HTTP POST to Flask API (/api/telemetry).
"""

import time
import requests
import serial

PORT = "COM2"
BAUD = 9600
API_URL = "http://127.0.0.1:5000/api/telemetry"

print(f"Connecting to Arduino on {PORT} at {BAUD} baud...")
try:
    ser = serial.Serial(PORT, BAUD, timeout=1.0)
    time.sleep(1.0)
    print(f"Connected! Forwarding sensor data to {API_URL} ...\n")
except Exception as e:
    print(f"Error opening {PORT}: {e}")
    exit()

try:
    while True:
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line:
            continue

        parts = [float(p.strip()) for p in line.split(",")]
        if len(parts) >= 3:
            payload = {
                "irradiance": parts[0],
                "temperature": parts[1],
                "voltage": parts[2],
            }

            # Send to Flask API
            try:
                res = requests.post(API_URL, json=payload, timeout=0.8)
                if res.status_code == 200:
                    resp_json = res.json()
                    # Handle response from either /api/telemetry or /api/predict
                    diag = resp_json.get("prediction") or resp_json.get("ai_diagnosis")
                    if diag:
                        print(
                            f"[{time.strftime('%H:%M:%S')}] "
                            f"Irr: {parts[0]:5.1f}% | Temp: {parts[1]:4.1f}°C | Volt: {parts[2]:5.2f}V --> "
                            f"AI: {diag['state_name']} ({diag['estimated_power_watts']} W)"
                        )
            except Exception:
                print("[Notice] Flask API Server is not responding...")

except KeyboardInterrupt:
    ser.close()
    print("\nBridge stopped.")