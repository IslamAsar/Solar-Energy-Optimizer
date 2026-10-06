"""
Project: Solar Energy Optimizer - Flask AI Deployment API
Module: AI for Engineering (Week 8 Task Deliverable)
Author: Islam Ahmed Nabil Asar

Endpoints:
    - GET  /              : Live AI Telemetry Dashboard.
    - POST /api/predict   : Receives sensor telemetry, runs ML inference, and returns diagnosis.
    - POST /api/telemetry : Ingests telemetry, logs to CSV, and returns real-time prediction.
    - GET  /api/latest    : Returns the latest recorded telemetry and AI state.
    - GET  /api/health    : Health-check endpoint verifying model loading status.
"""

import os
import time
import warnings
from collections import deque
from flask import Flask, jsonify, request
import joblib
import numpy as np

# Suppress all warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

# Paths to ML Artifacts from Week 8 Training Pipeline
MODEL_PATH = "solar_optimizer_model.pkl"
SCALER_PATH = "solar_scaler.pkl"
LOG_FILE = "sensor_log.csv"

# Global model holders
model = None
scaler = None

# In-memory buffer for the latest telemetry packets
TELEMETRY_BUFFER = deque(maxlen=50)


def init_log_file():
    """Initializes the CSV log file with unified schema if it does not exist."""
    expected_header = "timestamp,irradiance,temperature,voltage,status,source\n"
    if not os.path.exists(LOG_FILE) or os.stat(LOG_FILE).st_size == 0:
        try:
            with open(LOG_FILE, "w", newline="") as f:
                f.write(expected_header)
        except Exception as e:
            print(f"[AI Server Error] Failed to initialize {LOG_FILE}: {e}")


def load_artifacts():
    """Loads serialized Machine Learning model and StandardScaler from disk."""
    global model, scaler
    init_log_file()
    try:
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            model = joblib.load(MODEL_PATH)
            scaler = joblib.load(SCALER_PATH)
            print(f"[AI Server] Loaded ML model from '{MODEL_PATH}' successfully.")
        else:
            print("[AI Server Notice] Serialized model not found on disk. Using physics-based fallback.")
    except Exception as e:
        print(f"[AI Server Error] Loading artifacts failed: {e}")


def run_lean_inference(irradiance: float, temperature: float, voltage: float):
    """Executes Machine Learning prediction on scaled telemetry features."""
    power_index = (irradiance * voltage) / (temperature + 1.0)

    state_code = 0
    if model is not None and scaler is not None:
        try:
            raw_feats = np.array([[irradiance, temperature, voltage, power_index]])
            scaled_feats = scaler.transform(raw_feats)
            state_code = int(model.predict(scaled_feats)[0])
        except Exception:
            state_code = 0
    else:
        # Rule-based fallback matching solar operating dynamics
        if temperature > 65.0 or voltage < 10.5:
            state_code = 2
        elif irradiance < 40.0 or temperature > 50.0:
            state_code = 1
        else:
            state_code = 0

    state_map = {
        0: {
            "name": "OPTIMAL GENERATION",
            "tag": "OPTIMAL",
            "severity": "normal",
            "action": "Maintain active MPPT tracking.",
        },
        1: {
            "name": "SUB-OPTIMAL (SHADING/CLEANING)",
            "tag": "SUB_OPTIMAL",
            "severity": "warning",
            "action": "Schedule panel surface dust cleaning.",
        },
        2: {
            "name": "CRITICAL ALERT (OVERHEAT/LOW VOLT)",
            "tag": "CRITICAL_ALERT",
            "severity": "critical",
            "action": "Trigger emergency load disconnect and cooling.",
        },
    }

    diag = state_map.get(state_code, state_map[0])

    est_power = (irradiance / 100.0) * voltage * 6.5 * (1.0 - (temperature - 25.0) * 0.004)
    est_power = round(max(0.0, est_power), 2)

    return {
        "state_code": state_code,
        "state_name": diag["name"],
        "status_tag": diag["tag"],
        "severity": diag["severity"],
        "recommended_action": diag["action"],
        "estimated_power_watts": est_power,
    }


# =====================================================================
# API & UI ENDPOINTS
# =====================================================================

@app.route("/", methods=["GET"])
def index():
    """Live Web Dashboard for real-time monitoring."""
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Solar Optimizer - AI Dashboard</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; padding: 2rem; margin: 0; }
            .container { max-width: 720px; margin: 0 auto; background: #1e293b; padding: 2rem; border-radius: 12px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.5); }
            h1 { color: #38bdf8; font-size: 1.6rem; margin-top: 0; display: flex; align-items: center; gap: 8px; }
            .card { background: #334155; padding: 1.25rem; border-radius: 8px; margin-bottom: 1rem; }
            .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
            .metric { text-align: center; }
            .metric-label { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; }
            .metric-val { font-size: 1.7rem; font-weight: bold; color: #facc15; margin-top: 4px; }
            .status-badge { display: inline-block; padding: 0.4rem 0.8rem; border-radius: 6px; font-weight: 700; font-size: 0.9rem; }
            .normal { background: #14532d; color: #86efac; border: 1px solid #16a34a; }
            .warning { background: #713f12; color: #fde047; border: 1px solid #ca8a04; }
            .critical { background: #7f1d1d; color: #fca5a5; border: 1px solid #dc2626; }
            .info-row { display: flex; justify-content: space-between; margin: 0.5rem 0; border-bottom: 1px solid #475569; padding-bottom: 0.4rem; }
            .footer { font-size: 0.8rem; color: #64748b; text-align: center; margin-top: 1rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>☀️ Solar Optimizer AI Dashboard</h1>
            
            <div class="card grid">
                <div class="metric">
                    <div class="metric-label">Irradiance</div>
                    <div class="metric-val" id="irr">-- %</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Temperature</div>
                    <div class="metric-val" id="temp">-- °C</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Voltage</div>
                    <div class="metric-val" id="volt">-- V</div>
                </div>
            </div>

            <div class="card">
                <div class="info-row" style="border: none; align-items: center;">
                    <span style="font-weight: 600;">System Health State:</span>
                    <span id="badge" class="status-badge normal">WAITING TELEMETRY</span>
                </div>
                <div class="info-row">
                    <span>Estimated Output Power:</span>
                    <strong id="power" style="color: #38bdf8;">-- W</strong>
                </div>
                <div class="info-row">
                    <span>Recommended Action:</span>
                    <span id="action" style="color: #e2e8f0;">--</span>
                </div>
                <div class="info-row" style="border: none; margin-bottom: 0;">
                    <span>Last Received Packet:</span>
                    <span id="ts" style="color: #94a3b8;">--</span>
                </div>
            </div>

            <div class="footer">Solar Energy Optimizer • Connected to Flask API</div>
        </div>

        <script>
            async function fetchTelemetry() {
                try {
                    const res = await fetch('/api/latest');
                    const json = await res.json();
                    if (json.status === 'success' && json.data) {
                        const d = json.data;
                        document.getElementById('irr').innerText = d.irradiance.toFixed(1) + ' %';
                        document.getElementById('temp').innerText = d.temperature.toFixed(1) + ' °C';
                        document.getElementById('volt').innerText = d.voltage.toFixed(2) + ' V';
                        document.getElementById('ts').innerText = d.timestamp;

                        const diag = d.prediction;
                        document.getElementById('power').innerText = diag.estimated_power_watts + ' W';
                        document.getElementById('action').innerText = diag.recommended_action;

                        const badge = document.getElementById('badge');
                        badge.innerText = diag.state_name;
                        badge.className = 'status-badge ' + diag.severity;
                    }
                } catch (e) {
                    console.error("Telemetry fetch error:", e);
                }
            }
            setInterval(fetchTelemetry, 1000);
            fetchTelemetry();
        </script>
    </body>
    </html>
    """
    return html, 200


@app.route("/api/health", methods=["GET"])
def health_check():
    """Verifies API server status and whether ML models are loaded in memory."""
    return (
        jsonify({
            "status": "healthy",
            "ml_model_loaded": model is not None,
            "scaler_loaded": scaler is not None,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }),
        200,
    )


@app.route("/api/predict", methods=["POST"])
def predict():
    """Accepts sensor telemetry JSON and returns ML prediction."""
    data = request.get_json(silent=True)
    if (
        not data
        or "irradiance" not in data
        or "temperature" not in data
        or "voltage" not in data
    ):
        return (
            jsonify({
                "status": "error",
                "message": "Invalid payload. Required keys: 'irradiance', 'temperature', 'voltage'",
            }),
            400,
        )

    try:
        irr = float(data["irradiance"])
        temp = float(data["temperature"])
        volt = float(data["voltage"])

        prediction = run_lean_inference(irr, temp, volt)

        return (
            jsonify({
                "status": "success",
                "telemetry_inputs": {
                    "irradiance": irr,
                    "temperature": temp,
                    "voltage": volt,
                },
                "ai_diagnosis": prediction,
            }),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/telemetry", methods=["POST"])
def ingest_telemetry():
    """Ingests real-time telemetry from serial_bridge.py, logs to CSV with source='AI'."""
    data = request.get_json(silent=True)
    if (
        not data
        or "irradiance" not in data
        or "temperature" not in data
        or "voltage" not in data
    ):
        return jsonify({"status": "error", "message": "Invalid telemetry data"}), 400

    try:
        irr = float(data["irradiance"])
        temp = float(data["temperature"])
        volt = float(data["voltage"])
        ts = time.strftime("%H:%M:%S")

        prediction = run_lean_inference(irr, temp, volt)

        record = {
            "timestamp": ts,
            "irradiance": irr,
            "temperature": temp,
            "voltage": volt,
            "prediction": prediction,
        }
        TELEMETRY_BUFFER.append(record)

        # Append to CSV log with unified status and source='AI'
        status_tag = prediction.get("status_tag", "OPTIMAL")
        try:
            with open(LOG_FILE, "a", newline="") as f:
                f.write(f"{ts},{irr:.2f},{temp:.2f},{volt:.2f},{status_tag},AI\n")
        except Exception:
            pass

        return (
            jsonify({
                "status": "recorded",
                "timestamp": ts,
                "prediction": prediction,
            }),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/latest", methods=["GET"])
def get_latest():
    """Returns the most recent telemetry sample and AI diagnostic output."""
    if len(TELEMETRY_BUFFER) == 0:
        return (
            jsonify({
                "status": "empty",
                "message": "No telemetry packets received yet.",
            }),
            200,
        )
    return jsonify({"status": "success", "data": TELEMETRY_BUFFER[-1]}), 200


if __name__ == "__main__":
    load_artifacts()
    print("=========================================================")
    print(" Solar Energy Optimizer - Flask AI Deployment API")
    print(" Running on: http://0.0.0.0:5000 (Local & Network Accessible)")
    print(" Endpoints:  / | /api/health | /api/predict | /api/telemetry")
    print("=========================================================")
    app.run(host="0.0.0.0", port=5000, debug=False)