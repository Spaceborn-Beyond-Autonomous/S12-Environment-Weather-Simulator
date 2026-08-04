#!/usr/bin/env python3
"""
dt_server.py — Digital Twin state server for the ANSA drone + Environmental Conditions.

Bridges ROS2 topics (/imu/data, /model/ansa_drone/odometry, /battery_state, /env/wind_velocity)
and environmental variables into a FastAPI server exposing:
    GET  /           -> automatic redirect to /dashboard
    GET  /state     -> current state snapshot as JSON
    GET  /dashboard -> interactive live visual dashboard
    WS   /ws        -> continuous state stream (~15 Hz)
"""

import asyncio
import json
import math
import threading
import time
from dataclasses import dataclass, field, asdict

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, BatteryState
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Vector3  # Added for wind vector

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn


# ---------------------------------------------------------------------------
# 1. The Digital Twin state model — extended with Environmental Data
# ---------------------------------------------------------------------------

@dataclass
class EnvironmentState:
    rain_rate_mm_hr: float = 0.0
    particle_rate_sec: int = 0
    wind_speed_ms: float = 0.0
    wind_direction: dict = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
    emi_field_dBm: float = -90.0
    temperature_c: float = 25.0
    solar_irradiance_wm2: float = 800.0


@dataclass
class DroneState:
    # Position / orientation (from odometry)
    position: dict = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
    orientation: dict = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0})
    linear_velocity: dict = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})

    # IMU
    angular_velocity: dict = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
    linear_acceleration: dict = field(default_factory=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})

    # Battery
    battery_percentage: float = 100.0
    battery_voltage: float = 0.0

    # Environment
    environment: EnvironmentState = field(default_factory=EnvironmentState)

    # Bookkeeping
    last_odom_update: float = 0.0
    last_imu_update: float = 0.0
    last_battery_update: float = 0.0
    last_env_update: float = 0.0

    def to_dict(self):
        return asdict(self)


# Single shared Digital Twin state instance
dt_state = DroneState()


# ---------------------------------------------------------------------------
# 2. ROS2 node — bridge for drone telemetry and environment updates
# ---------------------------------------------------------------------------

class DTBridgeNode(Node):
    def __init__(self):
        super().__init__('dt_bridge_node')

        self.create_subscription(
            Odometry, '/model/ansa_drone/odometry', self._odom_cb, 10)
        self.create_subscription(
            Imu, '/imu/data', self._imu_cb, 10)
        self.create_subscription(
            BatteryState, '/battery_state', self._battery_cb, 10)
        
        # New: Subscribe to real wind vectors calculated by wind_simulation_node.py
        self.create_subscription(
            Vector3, '/env/wind_velocity', self._wind_cb, 10)

        # Timer loop (10 Hz) to simulate remaining atmospheric conditions
        self.create_timer(0.1, self._update_environment_simulation)

        self.get_logger().info('DT bridge node started — telemetry & environment active.')

    def _odom_cb(self, msg: Odometry):
        p = msg.pose.pose.position
        o = msg.pose.pose.orientation
        v = msg.twist.twist.linear
        dt_state.position = {"x": p.x, "y": p.y, "z": p.z}
        dt_state.orientation = {"x": o.x, "y": o.y, "z": o.z, "w": o.w}
        dt_state.linear_velocity = {"x": v.x, "y": v.y, "z": v.z}
        dt_state.last_odom_update = time.time()

    def _imu_cb(self, msg: Imu):
        av = msg.angular_velocity
        la = msg.linear_acceleration
        dt_state.angular_velocity = {"x": av.x, "y": av.y, "z": av.z}
        dt_state.linear_acceleration = {"x": la.x, "y": la.y, "z": la.z}
        dt_state.last_imu_update = time.time()

    def _battery_cb(self, msg: BatteryState):
        pct = msg.percentage if msg.percentage is not None else 0.0
        dt_state.battery_percentage = max(0.0, min(100.0, pct * 100.0 if pct <= 1.0 else pct))
        dt_state.battery_voltage = msg.voltage
        dt_state.last_battery_update = time.time()

    def _wind_cb(self, msg: Vector3):
        """Calculates total speed magnitude and stores 3D direction vector."""
        speed = math.sqrt(msg.x**2 + msg.y**2 + msg.z**2)
        dt_state.environment.wind_speed_ms = round(speed, 2)
        dt_state.environment.wind_direction = {
            "x": round(msg.x, 3),
            "y": round(msg.y, 3),
            "z": round(msg.z, 3)
        }
        dt_state.last_env_update = time.time()

    def _update_environment_simulation(self):
        """Generates auxiliary weather telemetry (rain, solar, EMI, temp)."""
        t = time.time()
        
        dt_state.environment.rain_rate_mm_hr = round(15.0 + 10.0 * (t % 10 / 10.0), 2)
        dt_state.environment.particle_rate_sec = int(dt_state.environment.rain_rate_mm_hr * 1000)
        dt_state.environment.emi_field_dBm = round(-50.0 + 5.0 * (t % 4 / 4.0), 1)
        dt_state.environment.temperature_c = round(26.5 + 0.5 * (t % 12 / 12.0), 2)
        dt_state.environment.solar_irradiance_wm2 = round(820.0 + 30.0 * (t % 8 / 8.0), 1)


def ros_spin_thread(node: DTBridgeNode):
    rclpy.spin(node)


# ---------------------------------------------------------------------------
# 3. FastAPI Web Server & Full Environmental Dashboard Layout
# ---------------------------------------------------------------------------

app = FastAPI(title="ANSA Drone Digital Twin")


DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>ANSA Digital Twin — Telemetry & Environment Dashboard</title>
<style>
  body { background:#0e0e12; color:#e6e6e6; font-family: 'Segoe UI', sans-serif; margin:0; padding:24px; }
  h1 { font-size:22px; color:#7ee0d8; margin-bottom:4px; }
  .status { font-size:13px; color:#888; margin-bottom:20px; }
  .status.live { color:#4ade80; }
  .status.dead { color:#f87171; }
  .grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; max-width:1200px; }
  .card { background:#1a1a22; border:1px solid #2a2a35; border-radius:10px; padding:16px; }
  .card h2 { font-size:12px; text-transform:uppercase; letter-spacing:0.05em; color:#9ca3af; margin:0 0 12px 0; }
  .env-card { border-left: 3px solid #00adb5; }
  canvas { background:#0a0a0e; border-radius:8px; display:block; }
  .readout { display:flex; justify-content:space-between; font-size:13px; padding:4px 0; border-bottom:1px solid #22222c; }
  .readout span:first-child { color:#9ca3af; }
  .readout span:last-child { font-variant-numeric: tabular-nums; font-weight:bold; }
  .battery-bar-bg { background:#22222c; border-radius:6px; height:18px; overflow:hidden; margin-top:8px; }
  .battery-bar-fill { height:100%; transition: width 0.3s, background 0.3s; }
  .val-highlight { color: #00fff5; }
</style>
</head>
<body>
  <h1>ANSA Digital Twin — Environment & Telemetry</h1>
  <div id="status" class="status dead">connecting...</div>

  <div class="grid">
    <!-- Row 1: Visual Canvas Displays -->
    <div class="card">
      <h2>Position (Top-Down)</h2>
      <canvas id="posCanvas" width="340" height="200"></canvas>
    </div>

    <div class="card">
      <h2>Attitude Indicator</h2>
      <canvas id="attCanvas" width="340" height="200"></canvas>
    </div>

    <!-- Row 1 Environment Highlight -->
    <div class="card env-card">
      <h2>Rain & Atmospheric Fog</h2>
      <div class="readout"><span>Rain Intensity</span><span id="rainRate" class="val-highlight">0.0 mm/hr</span></div>
      <div class="readout"><span>Particle Density</span><span id="particleRate">0 p/sec</span></div>
      <div class="readout"><span>Visibility Est.</span><span id="visEst">1000 m</span></div>
      <div class="readout"><span>Optical Attenuation</span><span id="optAtten">0.0 dB/km</span></div>
    </div>

    <!-- Row 2: Telemetry & Battery -->
    <div class="card">
      <h2>Drone Kinematics</h2>
      <div class="readout"><span>Position X / Y / Z</span><span id="posXYZ">0 / 0 / 0</span></div>
      <div class="readout"><span>Roll / Pitch / Yaw</span><span id="rpy">0° / 0° / 0°</span></div>
      <div class="readout"><span>Linear Accel Z</span><span id="az">0.00 m/s²</span></div>
    </div>

    <div class="card">
      <h2>Power & Battery</h2>
      <div class="readout"><span>Percentage</span><span id="battPct">100%</span></div>
      <div class="readout"><span>Voltage</span><span id="battV">0.00 V</span></div>
      <div class="battery-bar-bg"><div id="battBar" class="battery-bar-fill" style="width:100%; background:#4ade80;"></div></div>
    </div>

    <!-- Row 2 Environment Conditions -->
    <div class="card env-card">
      <h2>Wind & Aerodynamic Forces</h2>
      <div class="readout"><span>Wind Velocity</span><span id="windSpeed" class="val-highlight">0.0 m/s</span></div>
      <div class="readout"><span>Wind Vector</span><span id="windVec">(0.0, 0.0, 0.0)</span></div>
      <div class="readout"><span>Turbulence Index</span><span>Moderate</span></div>
    </div>

    <!-- Row 3 Environment Conditions -->
    <div class="card env-card">
      <h2>RF & EMI Interference</h2>
      <div class="readout"><span>EMI Field Level</span><span id="emiField" class="val-highlight">-90 dBm</span></div>
      <div class="readout"><span>Tower Distance</span><span>12.4 m</span></div>
      <div class="readout"><span>GPS Noise Delta</span><span>+1.2 m</span></div>
    </div>

    <div class="card env-card">
      <h2>Solar & Thermal Loading</h2>
      <div class="readout"><span>Ambient Temp</span><span id="tempC" class="val-highlight">25.0 °C</span></div>
      <div class="readout"><span>Solar Irradiance</span><span id="solarIrrad">800 W/m²</span></div>
      <div class="readout"><span>Thermal Loading</span><span>Nominal</span></div>
    </div>

    <div class="card">
      <h2>System Sync Timestamps</h2>
      <div class="readout"><span>Odom Sync</span><span id="lastOdom">-</span></div>
      <div class="readout"><span>IMU Sync</span><span id="lastImu">-</span></div>
      <div class="readout"><span>Env Engine Sync</span><span id="lastEnv">-</span></div>
    </div>
  </div>

<script>
const posCanvas = document.getElementById('posCanvas');
const posCtx = posCanvas.getContext('2d');
const attCanvas = document.getElementById('attCanvas');
const attCtx = attCanvas.getContext('2d');
const trail = [];
const MAX_TRAIL = 150;
const PX_PER_M = 12;

function quatToEuler(x, y, z, w) {
  const sinr_cosp = 2 * (w * x + y * z);
  const cosr_cosp = 1 - 2 * (x * x + y * y);
  const roll = Math.atan2(sinr_cosp, cosr_cosp);

  const sinp = 2 * (w * y - z * x);
  const pitch = Math.abs(sinp) >= 1 ? Math.sign(sinp) * Math.PI / 2 : Math.asin(sinp);

  const siny_cosp = 2 * (w * z + x * y);
  const cosy_cosp = 1 - 2 * (y * y + z * z);
  const yaw = Math.atan2(siny_cosp, cosy_cosp);

  return {roll: roll * 180/Math.PI, pitch: pitch * 180/Math.PI, yaw: yaw * 180/Math.PI};
}

function drawPosition(x, y) {
  posCtx.clearRect(0, 0, posCanvas.width, posCanvas.height);
  const cx = posCanvas.width/2, cy = posCanvas.height/2;

  posCtx.strokeStyle = '#1c1c26';
  posCtx.lineWidth = 1;
  for (let gx = 0; gx <= posCanvas.width; gx += 25) {
    posCtx.beginPath(); posCtx.moveTo(gx,0); posCtx.lineTo(gx,posCanvas.height); posCtx.stroke();
  }
  for (let gy = 0; gy <= posCanvas.height; gy += 25) {
    posCtx.beginPath(); posCtx.moveTo(0,gy); posCtx.lineTo(posCanvas.width,gy); posCtx.stroke();
  }

  posCtx.strokeStyle = '#3a3a48';
  posCtx.beginPath(); posCtx.arc(cx, cy, 5, 0, 2*Math.PI); posCtx.stroke();

  const px = cx + x * PX_PER_M;
  const py = cy - y * PX_PER_M;

  trail.push([px, py]);
  if (trail.length > MAX_TRAIL) trail.shift();

  posCtx.strokeStyle = '#7ee0d8';
  posCtx.beginPath();
  trail.forEach(([tx,ty], i) => { i===0 ? posCtx.moveTo(tx,ty) : posCtx.lineTo(tx,ty); });
  posCtx.stroke();

  posCtx.fillStyle = '#4ade80';
  posCtx.beginPath();
  posCtx.arc(px, py, 5, 0, 2*Math.PI);
  posCtx.fill();
}

function drawAttitude(roll, pitch, yaw) {
  attCtx.clearRect(0, 0, attCanvas.width, attCanvas.height);
  const cx = attCanvas.width/2, cy = attCanvas.height/2, r = 75;

  attCtx.save();
  attCtx.translate(cx, cy);
  attCtx.rotate(-roll * Math.PI/180);
  const pitchOffset = pitch * 1.5;

  attCtx.fillStyle = '#2b3a5c';
  attCtx.fillRect(-150, pitchOffset, 300, 150);
  attCtx.fillStyle = '#5c4a2b';
  attCtx.fillRect(-150, pitchOffset - 150, 300, 150);

  attCtx.strokeStyle = '#e6e6e6';
  attCtx.lineWidth = 2;
  attCtx.beginPath(); attCtx.moveTo(-150, pitchOffset); attCtx.lineTo(150, pitchOffset); attCtx.stroke();
  attCtx.restore();

  attCtx.strokeStyle = '#0e0e12';
  attCtx.lineWidth = 5;
  attCtx.beginPath(); attCtx.arc(cx, cy, r+2, 0, 2*Math.PI); attCtx.stroke();

  attCtx.strokeStyle = '#f87171';
  attCtx.lineWidth = 2;
  attCtx.beginPath(); attCtx.moveTo(cx-20, cy); attCtx.lineTo(cx+20, cy); attCtx.stroke();
}

function connect() {
  const ws = new WebSocket(`ws://${location.host}/ws`);
  const statusEl = document.getElementById('status');

  ws.onopen = () => { statusEl.textContent = 'live'; statusEl.className = 'status live'; };
  ws.onclose = () => { statusEl.textContent = 'disconnected — retrying...'; statusEl.className = 'status dead'; setTimeout(connect, 1500); };
  ws.onerror = () => ws.close();

  ws.onmessage = (event) => {
    const s = JSON.parse(event.data);
    
    // Telemetry
    document.getElementById('posXYZ').textContent = `${s.position.x.toFixed(2)}, ${s.position.y.toFixed(2)}, ${s.position.z.toFixed(2)}`;
    document.getElementById('az').textContent = s.linear_acceleration.z.toFixed(2) + ' m/s²';

    const {roll, pitch, yaw} = quatToEuler(s.orientation.x, s.orientation.y, s.orientation.z, s.orientation.w);
    document.getElementById('rpy').textContent = `${roll.toFixed(1)}°, ${pitch.toFixed(1)}°, ${yaw.toFixed(1)}°`;

    // Battery
    const pct = s.battery_percentage;
    document.getElementById('battPct').textContent = pct.toFixed(1) + '%';
    document.getElementById('battV').textContent = s.battery_voltage.toFixed(2) + ' V';
    const bar = document.getElementById('battBar');
    bar.style.width = pct + '%';
    bar.style.background = pct > 50 ? '#4ade80' : pct > 20 ? '#facc15' : '#f87171';

    // Environment Data
    if (s.environment) {
      document.getElementById('rainRate').textContent = s.environment.rain_rate_mm_hr + ' mm/hr';
      document.getElementById('particleRate').textContent = s.environment.particle_rate_sec + ' p/sec';
      document.getElementById('windSpeed').textContent = s.environment.wind_speed_ms + ' m/s';
      if (s.environment.wind_direction) {
        const wd = s.environment.wind_direction;
        document.getElementById('windVec').textContent = `(${wd.x}, ${wd.y}, ${wd.z})`;
      }
      document.getElementById('emiField').textContent = s.environment.emi_field_dBm + ' dBm';
      document.getElementById('tempC').textContent = s.environment.temperature_c + ' °C';
      document.getElementById('solarIrrad').textContent = s.environment.solar_irradiance_wm2 + ' W/m²';
    }

    // Timestamps
    const fmt = (t) => t > 0 ? new Date(t*1000).toLocaleTimeString() : 'never';
    document.getElementById('lastOdom').textContent = fmt(s.last_odom_update);
    document.getElementById('lastImu').textContent = fmt(s.last_imu_update);
    document.getElementById('lastEnv').textContent = fmt(s.last_env_update);

    drawPosition(s.position.x, s.position.y);
    drawAttitude(roll, pitch, yaw);
  };
}
connect();
</script>
</body>
</html>
"""


@app.get("/")
async def root_redirect():
    """Redirect root path to interactive dashboard."""
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Live visual dashboard — telemetry, battery, and dynamic environmental monitoring."""
    return DASHBOARD_HTML


@app.get("/state")
async def get_state():
    """One-shot snapshot of the current Digital Twin state."""
    return dt_state.to_dict()


@app.websocket("/ws")
async def websocket_stream(websocket: WebSocket):
    """Continuous state stream at ~15 Hz."""
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(dt_state.to_dict())
            await asyncio.sleep(1.0 / 15.0)
    except WebSocketDisconnect:
        pass


# ---------------------------------------------------------------------------
# 4. Entrypoint — execution loop
# ---------------------------------------------------------------------------

def main():
    rclpy.init()
    node = DTBridgeNode()

    spin_thread = threading.Thread(target=ros_spin_thread, args=(node,), daemon=True)
    spin_thread.start()

    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()