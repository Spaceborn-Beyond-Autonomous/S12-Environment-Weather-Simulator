#!/usr/bin/env python3
"""
dt_server.py — Digital Twin state server for the ANSA drone.

Bridges ROS2 topics (/imu/data, /model/ansa_drone/odometry, /battery_state)
into a FastAPI server exposing:
    GET  /state   -> current state snapshot as JSON
    WS   /ws      -> continuous state stream (~15 Hz)

Architecture note: this file is the ONLY place that touches rclpy directly.
The DT class (DroneState below) holds the mirrored state in memory and is
updated purely from ROS2 callbacks — nothing downstream of this file should
ever import rclpy or talk to ROS2/Gazebo directly. That separation is what
makes this a digital twin rather than just a passthrough viewer: the DT
state is free-standing and could, in principle, be fed by a different
source (e.g. a real drone) without changing anything below this layer.

Usage:
    source /opt/ros/jazzy/setup.bash
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    python3 dt_server.py

Then:
    curl http://localhost:8000/state
    (or open a WebSocket client to ws://localhost:8000/ws)
"""

import asyncio
import json
import threading
import time
from dataclasses import dataclass, field, asdict

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, BatteryState
from nav_msgs.msg import Odometry

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn


# ---------------------------------------------------------------------------
# 1. The Digital Twin state model — plain data, no ROS2/Gazebo awareness
# ---------------------------------------------------------------------------

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

    # Bookkeeping — helps the dashboard show data freshness / sync fidelity
    last_odom_update: float = 0.0
    last_imu_update: float = 0.0
    last_battery_update: float = 0.0

    def to_dict(self):
        return asdict(self)


# Single shared instance. Protected implicitly by the GIL for simple
# attribute writes; good enough for this read-mostly, single-writer-per-field
# use case. If contention becomes an issue later, add a threading.Lock.
dt_state = DroneState()


# ---------------------------------------------------------------------------
# 2. ROS2 node — the ONLY thing that touches rclpy
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

        self.get_logger().info('DT bridge node started — subscribed to odometry, imu, battery')

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
        # Clamp percentage defensively — known upstream bug lets this go
        # negative in Gazebo; the DT should never surface a nonsense value.
        pct = msg.percentage if msg.percentage is not None else 0.0
        dt_state.battery_percentage = max(0.0, min(100.0, pct * 100.0 if pct <= 1.0 else pct))
        dt_state.battery_voltage = msg.voltage
        dt_state.last_battery_update = time.time()


def ros_spin_thread(node: DTBridgeNode):
    """Runs rclpy spin on a background thread so FastAPI/uvicorn can own the main thread."""
    rclpy.spin(node)


# ---------------------------------------------------------------------------
# 3. FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(title="ANSA Drone Digital Twin")


DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>ANSA Drone Digital Twin</title>
<style>
  body { background:#0e0e12; color:#e6e6e6; font-family: 'Segoe UI', sans-serif; margin:0; padding:24px; }
  h1 { font-size:20px; color:#7ee0d8; margin-bottom:4px; }
  .status { font-size:13px; color:#888; margin-bottom:20px; }
  .status.live { color:#4ade80; }
  .status.dead { color:#f87171; }
  .grid { display:grid; grid-template-columns: 1fr 1fr; gap:20px; max-width:1000px; }
  .card { background:#1a1a22; border:1px solid #2a2a35; border-radius:10px; padding:16px; }
  .card h2 { font-size:13px; text-transform:uppercase; letter-spacing:0.05em; color:#9ca3af; margin:0 0 12px 0; }
  canvas { background:#0a0a0e; border-radius:8px; display:block; }
  .readout { display:flex; justify-content:space-between; font-size:13px; padding:4px 0; border-bottom:1px solid #22222c; }
  .readout span:first-child { color:#9ca3af; }
  .readout span:last-child { font-variant-numeric: tabular-nums; }
  .battery-bar-bg { background:#22222c; border-radius:6px; height:22px; overflow:hidden; margin-top:8px; }
  .battery-bar-fill { height:100%; transition: width 0.3s, background 0.3s; }
</style>
</head>
<body>
  <h1>ANSA Drone Digital Twin</h1>
  <div id="status" class="status dead">connecting...</div>

  <div class="grid">
    <div class="card">
      <h2>Position (top-down)</h2>
      <canvas id="posCanvas" width="440" height="300"></canvas>
    </div>

    <div class="card">
      <h2>Attitude</h2>
      <canvas id="attCanvas" width="440" height="300"></canvas>
    </div>

    <div class="card">
      <h2>Telemetry</h2>
      <div class="readout"><span>Position X</span><span id="px">0.00</span></div>
      <div class="readout"><span>Position Y</span><span id="py">0.00</span></div>
      <div class="readout"><span>Position Z (alt)</span><span id="pz">0.00</span></div>
      <div class="readout"><span>Roll</span><span id="roll">0.00°</span></div>
      <div class="readout"><span>Pitch</span><span id="pitch">0.00°</span></div>
      <div class="readout"><span>Yaw</span><span id="yaw">0.00°</span></div>
      <div class="readout"><span>Linear accel Z</span><span id="az">0.00</span></div>
    </div>

    <div class="card">
      <h2>Battery</h2>
      <div class="readout"><span>Percentage</span><span id="battPct">100%</span></div>
      <div class="readout"><span>Voltage</span><span id="battV">0.00 V</span></div>
      <div class="battery-bar-bg"><div id="battBar" class="battery-bar-fill" style="width:100%; background:#4ade80;"></div></div>
      <div class="readout" style="margin-top:12px;"><span>Last odom update</span><span id="lastOdom">-</span></div>
      <div class="readout"><span>Last IMU update</span><span id="lastImu">-</span></div>
      <div class="readout"><span>Last battery update</span><span id="lastBatt">-</span></div>
    </div>
  </div>

<script>
const posCanvas = document.getElementById('posCanvas');
const posCtx = posCanvas.getContext('2d');
const attCanvas = document.getElementById('attCanvas');
const attCtx = attCanvas.getContext('2d');
const trail = [];
const MAX_TRAIL = 200;
const PX_PER_M = 15;

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

  // grid
  posCtx.strokeStyle = '#1c1c26';
  posCtx.lineWidth = 1;
  for (let gx = 0; gx <= posCanvas.width; gx += 30) {
    posCtx.beginPath(); posCtx.moveTo(gx,0); posCtx.lineTo(gx,posCanvas.height); posCtx.stroke();
  }
  for (let gy = 0; gy <= posCanvas.height; gy += 30) {
    posCtx.beginPath(); posCtx.moveTo(0,gy); posCtx.lineTo(posCanvas.width,gy); posCtx.stroke();
  }

  // origin marker
  posCtx.strokeStyle = '#3a3a48';
  posCtx.beginPath(); posCtx.arc(cx, cy, 6, 0, 2*Math.PI); posCtx.stroke();

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
  posCtx.arc(px, py, 6, 0, 2*Math.PI);
  posCtx.fill();
}

function drawAttitude(roll, pitch, yaw) {
  attCtx.clearRect(0, 0, attCanvas.width, attCanvas.height);
  const cx = attCanvas.width/2, cy = attCanvas.height/2, r = 110;

  attCtx.save();
  attCtx.translate(cx, cy);
  attCtx.rotate(-roll * Math.PI/180);
  const pitchOffset = pitch * 2;

  attCtx.fillStyle = '#2b3a5c';
  attCtx.fillRect(-200, pitchOffset, 400, 200);
  attCtx.fillStyle = '#5c4a2b';
  attCtx.fillRect(-200, pitchOffset - 200, 400, 200);

  attCtx.strokeStyle = '#e6e6e6';
  attCtx.lineWidth = 2;
  attCtx.beginPath(); attCtx.moveTo(-200, pitchOffset); attCtx.lineTo(200, pitchOffset); attCtx.stroke();
  attCtx.restore();

  attCtx.strokeStyle = '#0e0e12';
  attCtx.lineWidth = 6;
  attCtx.beginPath(); attCtx.arc(cx, cy, r+3, 0, 2*Math.PI); attCtx.stroke();
  attCtx.save();
  attCtx.beginPath(); attCtx.arc(cx, cy, r, 0, 2*Math.PI); attCtx.clip();
  attCtx.restore();

  attCtx.strokeStyle = '#f87171';
  attCtx.lineWidth = 3;
  attCtx.beginPath(); attCtx.moveTo(cx-30, cy); attCtx.lineTo(cx+30, cy); attCtx.stroke();

  attCtx.fillStyle = '#9ca3af';
  attCtx.font = '12px sans-serif';
  attCtx.fillText('yaw ' + yaw.toFixed(1) + '°', cx-30, cy+r+25);
}

function connect() {
  const ws = new WebSocket(`ws://${location.host}/ws`);
  const statusEl = document.getElementById('status');

  ws.onopen = () => { statusEl.textContent = 'live'; statusEl.className = 'status live'; };
  ws.onclose = () => { statusEl.textContent = 'disconnected — retrying...'; statusEl.className = 'status dead'; setTimeout(connect, 1500); };
  ws.onerror = () => ws.close();

  ws.onmessage = (event) => {
    const s = JSON.parse(event.data);
    document.getElementById('px').textContent = s.position.x.toFixed(3);
    document.getElementById('py').textContent = s.position.y.toFixed(3);
    document.getElementById('pz').textContent = s.position.z.toFixed(3);
    document.getElementById('az').textContent = s.linear_acceleration.z.toFixed(3);

    const {roll, pitch, yaw} = quatToEuler(s.orientation.x, s.orientation.y, s.orientation.z, s.orientation.w);
    document.getElementById('roll').textContent = roll.toFixed(2) + '°';
    document.getElementById('pitch').textContent = pitch.toFixed(2) + '°';
    document.getElementById('yaw').textContent = yaw.toFixed(2) + '°';

    const pct = s.battery_percentage;
    document.getElementById('battPct').textContent = pct.toFixed(1) + '%';
    document.getElementById('battV').textContent = s.battery_voltage.toFixed(2) + ' V';
    const bar = document.getElementById('battBar');
    bar.style.width = pct + '%';
    bar.style.background = pct > 50 ? '#4ade80' : pct > 20 ? '#facc15' : '#f87171';

    const fmt = (t) => t > 0 ? new Date(t*1000).toLocaleTimeString() : 'never';
    document.getElementById('lastOdom').textContent = fmt(s.last_odom_update);
    document.getElementById('lastImu').textContent = fmt(s.last_imu_update);
    document.getElementById('lastBatt').textContent = fmt(s.last_battery_update);

    drawPosition(s.position.x, s.position.y);
    drawAttitude(roll, pitch, yaw);
  };
}
connect();
</script>
</body>
</html>
"""


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Live-updating visual dashboard — position trail, attitude indicator, battery gauge."""
    return DASHBOARD_HTML


@app.get("/state")
async def get_state():
    """One-shot snapshot of the current DT state."""
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
# 4. Entrypoint — start rclpy in background, then run uvicorn in foreground
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