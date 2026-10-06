/*
 * =========================================================================
 * Project: Solar Energy Optimizer - Edge AI Auto-Generated Firmware
 * Generated Automatically by: train_ml_pipeline.ipynb
 * Author: Islam Ahmed Nabil Asar
 * =========================================================================
 */

#ifndef SCALER_PARAMS_H
#define SCALER_PARAMS_H

#define NUM_TELEMETRY_FEATURES 4

enum OperationalState {
  STATE_OPTIMAL = 0,
  STATE_SUB_OPTIMAL = 1,
  STATE_CRITICAL_ALERT = 2
};

// 1. Normalization Parameters
static const float SCALER_MEANS[NUM_TELEMETRY_FEATURES] = {
    54.5021f, 50.0904f, 11.7379f, 14.0668f
};

static const float SCALER_SCALES[NUM_TELEMETRY_FEATURES] = {
    23.3604f, 16.2678f, 1.5617f, 8.4345f
};

inline void normalize_features(const float raw[NUM_TELEMETRY_FEATURES], float scaled[NUM_TELEMETRY_FEATURES]) {
    for (int i = 0; i < NUM_TELEMETRY_FEATURES; i++) {
        scaled[i] = (raw[i] - SCALER_MEANS[i]) / SCALER_SCALES[i];
    }
}

// 2. Auto-Generated Edge AI Decision Engine (Generic Model Transpilation)
inline OperationalState predict_edge_state(const float raw[NUM_TELEMETRY_FEATURES], const float scaled[NUM_TELEMETRY_FEATURES]) {
    if (scaled[2] <= -0.7895f) {
        if (scaled[0] <= 1.5558f) {
            if (scaled[1] <= -1.5374f) {
                return (OperationalState)2;
            } else {
                if (scaled[3] <= -1.2594f) {
                    return (OperationalState)2;
                } else {
                    return (OperationalState)2;
                }
            }
        } else {
            return (OperationalState)2;
        }
    } else {
        if (scaled[1] <= 0.8550f) {
            if (scaled[1] <= -0.1214f) {
                if (scaled[0] <= -0.6311f) {
                    return (OperationalState)1;
                } else {
                    return (OperationalState)0;
                }
            } else {
                if (scaled[3] <= 0.3989f) {
                    return (OperationalState)1;
                } else {
                    return (OperationalState)1;
                }
            }
        } else {
            return (OperationalState)2;
        }
    }
}

#endif // SCALER_PARAMS_H
