# lidar3d_stack

3D LiDAR Sensor Simulation Stack for Drone and Rover platforms.

**SPACEBORN / ANSA — Robotics & Simulation Department**  
**Classification:** INTERNAL — NOT FOR EXTERNAL DISTRIBUTION

---

## Software Versions

| Software | Version |
|---|---|
| Ubuntu | 22.04 LTS |
| ROS2 | Humble |
| Gazebo | Harmonic |
| Python | 3.10 |

---

## Dependencies

```bash
# ROS2 packages
sudo apt install -y \
  ros-humble-robot-state-publisher \
  ros-humble-ros-gz-sim \
  ros-humble-ros-gz-bridge \
  ros-humble-rviz2 \
  ros-humble-xacro

# Gazebo Harmonic
sudo apt install -y gz-harmonic

# ROS2 + Gazebo Harmonic bridge
sudo apt install -y ros-humble-ros-gzharmonic
```

---

## Workspace Setup

### Step 1 — Create Workspace

```bash
mkdir -p ~/spaceborn_ws/src
cd ~/spaceborn_ws/src
```

### Step 2 — Clone Repository

```bash
git clone https://github.com/spaceborn-ansa/lidar3d_stack.git
```

### Step 3 — Build Workspace

```bash
cd ~/spaceborn_ws
colcon build --symlink-install
```

### Step 4 — Source Workspace

```bash
source install/setup.bash

# Optional — add to .bashrc for permanent sourcing
echo "source ~/spaceborn_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### Step 5 — Verify Package is Found

```bash
ros2 pkg list | grep lidar3d_stack
```

---

## Launch

```bash
# Rover + OS1-64 64-beam (default)
ros2 launch lidar3d_stack lidar_launch.py

# Rover + VLP-16 16-beam
ros2 launch lidar3d_stack lidar_launch.py lidar_profile:=vlp16

# Drone + OS1-64 64-beam
ros2 launch lidar3d_stack lidar_launch.py robot_type:=drone

# Drone + VLP-16 16-beam
ros2 launch lidar3d_stack lidar_launch.py robot_type:=drone lidar_profile:=vlp16
```

### Launch Arguments

| Argument | Default | Options |
|---|---|---|
| `robot_type` | `rover` | `rover`, `drone` |
| `lidar_profile` | `os1_64` | `os1_64`, `vlp16` |
| `world_name` | `lidar_world` | any `.sdf` in worlds/ |

---

## Verify LiDAR Data

### Check Topic is Publishing

```bash
# Confirm topic exists
ros2 topic list | grep scan_3d

# Confirm publishing rate — must show 10 Hz
ros2 topic hz /scan_3d
```

### Inspect PointCloud2 Message

```bash
# Print one full message to terminal
ros2 topic echo /scan_3d --once
```

### Check PointCloud2 Fields and Structure

```bash
# Shows fields: x, y, z, intensity, ring, timestamp
ros2 topic echo /scan_3d --field fields --once
```

### Check from Gazebo Side

```bash
# Confirm sensor is publishing inside Gazebo
gz topic -l | grep scan

# Check data rate on Gazebo side
gz topic -hz /scan_3d
```

### Check TF Tree

```bash
ros2 run tf2_tools view_frames
# Opens a PDF showing full TF tree
# Expected: world → base_link → lidar_link
```

---

## Visualise PointCloud2 in RViz2

RViz2 launches automatically with the stack. Follow these steps to display the point cloud:

**Step 1** — Set Fixed Frame in top left panel:
```
Global Options → Fixed Frame → lidar_link
```

**Step 2** — Add PointCloud2 display:
```
Click Add (bottom left)
→ By Topic
→ /scan_3d
→ PointCloud2
→ OK
```

**Step 3** — Configure display settings in left panel:

| Setting | Value |
|---|---|
| Topic | `/scan_3d` |
| Style | `Flat Squares` |
| Size (m) | `0.05` |
| Color Transformer | `AxisColor` |
| Axis | `Z` |
| Decay Time | `0` |

**Step 4** — Save RViz config for future use:
```
File → Save Config As → rviz/lidar3d.rviz
```

---

## LiDAR Profiles

### OS1-64 (64-beam)

| Parameter | Value |
|---|---|
| Vertical beams | 64 |
| Horizontal FOV | 360° |
| Vertical FOV | 45° |
| Max range | 120m |
| Update rate | 10 Hz |
| Noise stddev | 0.03m |

### VLP-16 (16-beam)

| Parameter | Value |
|---|---|
| Vertical beams | 16 |
| Horizontal FOV | 360° |
| Vertical FOV | 30° |
| Max range | 120m |
| Update rate | 10 Hz |
| Noise stddev | 0.03m |

Both profiles publish on `/scan_3d` as `sensor_msgs/msg/PointCloud2` at `lidar_link` frame.

---

## Sign-Off Criteria

- Virtual OS1-64 streaming `/scan_3d` at 10 Hz, 64 beams confirmed in RViz2
- TF tree correct: `base_link → lidar_link` on both drone and rover models  
- Both 16-beam and 64-beam sensor profiles configurable and validated
