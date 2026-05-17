# Pool Monitoring

Store manual measurements to compare with automatic sensor readings and calibrate the automatic measurements.
The system serves as a bridge between precise manual reference measurements and automated sensor monitoring.

## Core Features

**Manual Data Entry:** Intuitive UI for entering reference values directly at the pool.

The measured values serve as a basis for later analysis (not part of this project):
- **Sensor Drift Analysis:** Comparison between hardware sensors and manual measurements.
- **Calibration Logic:** Calculation of a software offset to compensate for sensor inaccuracies.
- **Historical Data:** Local storage and visualization of recent measurement cycles.

## Deployment & Installation

The app is delivered as a PWA. Installation happens without an app store via the browser's "Add to Home Screen" feature. This reduces maintenance costs and bypasses restrictive store policies.

## Specification

- **Platforms:** Web App
- **Design:** Modern, bright design
- **Manual Input:**
    - **Time & Date:** (default: now)
    - **Name:** (default: "Pool")
    - **Temp:** °C (default: 20°C | +/- 0.2°C)
    - **Chlorine:** (default: 1.0 | +/- 0.1)
    - **pH Value:** (default: 7.0 | +/- 0.1)
- **Send measurements as JSON** to MQTT server.
- **MQTT Server & Password** stored locally on the phone or in cookies.

* **Technology Stack:** Vue.js 3, Tailwind CSS, MQTT bridge via REST (Python backend), Chart.js.
* **Framework:** Vue.js 3 (Composition API).
* **Styling:** Tailwind CSS (utility-first for responsive design).

## Technology

### MQTT

- Mosquitto in Docker container as MQTT broker (existing)
- Python backend REST ↔ MQTT (part of this project)

- JSON message:
```json
{
    "time": 1755724982,
    "name": "Pool H32",
    "status": "manual data",
    "sensorType": "manual",
    "temp": 28.4,
    "pH": 7.2,
    "cl": 0.7
}
```

### Server

- Virtual server with Docker environment (existing)
- Secure connection (Let's Encrypt)
- Authentication / login
