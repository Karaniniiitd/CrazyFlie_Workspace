# CrazyFlie Workspace

**Author:** Karan Kumar Anand  
**Platform:** Ubuntu 22.04 | ROS 2 Humble | Python 3.10  
**Hardware:** Crazyflie 2.1 Nano Quadcopter · Crazyradio 2.0 USB Dongle

---

## Overview

This repository documents the complete setup, configuration, and ROS 2 integration of the **Crazyflie 2.1** nano quadcopter on Ubuntu Linux. It covers the entire pipeline — from initial hardware configuration and firmware flashing to manual flight verification and autonomous ROS 2 control.

The workspace is structured around [Crazyswarm2](https://github.com/IMRCLab/crazyswarm2), a ROS 2 package that provides a high-level interface for controlling Crazyflie drones. This is a foundational step toward the broader goal of building a **fully autonomous, coordinated Crazyflie swarm**.

---

## Motivation

> *"The goal is not to fly one drone — it is to orchestrate many."*

Modern autonomous systems increasingly demand **multi-agent coordination** — from search-and-rescue missions to precision agriculture and warehouse logistics. The **Crazyflie 2.1**, with its open-source firmware and lightweight ROS 2 integration via Crazyswarm2, offers an ideal research platform to explore and prototype real-world swarm intelligence.

This project is driven by the following vision:

### Core Goal — Autonomous Crazyflie Swarm

Build a multi-drone system where a fleet of Crazyflie quadcopters can:

- **Coordinate autonomously** without centralized human control
- **Distribute tasks** across agents using decentralized planning algorithms
- **Avoid inter-drone collisions** through real-time trajectory negotiation
- **Adapt dynamically** to changing environments and mission parameters

### Research Motivation

| Aspect | Motivation |
|--------|------------|
| **Swarm Intelligence** | Study emergent collective behaviour from simple per-drone rules |
| **Decentralized Control** | Eliminate single points of failure — no master controller |
| **Efficient Coordination** | Minimize redundant flight paths and maximize mission coverage |
| **Scalability** | Design algorithms that work for 2 drones and scale to 20+ |
| **Real Hardware Validation** | Move beyond simulation — test coordination strategies on physical drones |

### Roadmap

- [x] **Phase 1** — Hardware bring-up: Crazyradio 2.0, firmware, udev, connectivity
- [x] **Phase 2** — Manual flight validation via Xbox controller and CFClient
- [x] **Phase 3** — ROS 2 integration: Crazyswarm2 launch, services, takeoff/land
- [ ] **Phase 4** — Multi-drone spawning and fleet configuration
- [ ] **Phase 5** — Decentralized task allocation and collision-free trajectory planning
- [ ] **Phase 6** — Full autonomous swarm mission execution

---

## Repository Structure

```
cf_ws/
├── src/
│   ├── crazyswarm2/        # ROS 2 Crazyflie driver (cloned from IMRCLab)
│   └── my_crazyflie/       # Custom ROS 2 package for Crazyflie control
├── Documentation/
│   ├── CrazyFile Crazy radio connection Documentation.pdf
│   ├── CrazyFlie with Game controller Documentation.pdf
│   └── Ros2 Configuration with CrazyFlie.pdf
└── README.md
```

---

## Documentation

Detailed setup guides are available in the [`Documentation/`](./Documentation/) folder:

| Document | Description |
|----------|-------------|
| [Crazyradio Connection Documentation](./Documentation/CrazyFile%20Crazy%20radio%20connection%20Documentation.pdf) | Complete setup, bug diagnosis, and resolution for Crazyradio 2.0 on Ubuntu |
| [Game Controller Documentation](./Documentation/CrazyFlie%20with%20Game%20controller%20Documentation.pdf) | Manual flight setup using Xbox One S controller and CFClient |
| [ROS 2 Configuration](./Documentation/Ros2%20Configuration%20with%20CrazyFlie.pdf) | Workspace setup, hardware connection, and ROS 2 service verification |

---

## System Requirements

| Component | Specification |
|-----------|--------------|
| Operating System | Ubuntu 22.04 LTS |
| ROS 2 Version | ROS 2 Humble Hawksbill |
| Python | Python 3.10 |
| cfclient | 2026.4 |
| cflib | 0.1.32 |
| Drone | Crazyflie 2.1 |
| Radio | Crazyradio 2.0 |

---

## Setup Guide

### 1. Prerequisites

Ensure ROS 2 Humble is installed. Then create the workspace:

```bash
mkdir -p ~/cf_ws/src
cd ~/cf_ws/src
git clone https://github.com/IMRCLab/crazyswarm2.git
```

### 2. Install Dependencies

```bash
cd ~/cf_ws
rosdep install --from-paths src --ignore-src -r -y
```

### 3. Build the Workspace

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source ~/cf_ws/install/setup.bash
```

---

## Crazyradio 2.0 Setup

### Firmware Flashing

If the Crazyradio mounts as a USB storage device (`Crazyradio2`), it is in UF2 bootloader mode and requires firmware flashing:

```bash
# Download official firmware
wget https://github.com/bitcraze/crazyradio2-firmware/releases/download/5.5/crazyradio2-5.5.uf2

# Flash firmware (Crazyradio must be mounted)
cp crazyradio2-5.5.uf2 /media/$USER/Crazyradio2/
```

After copying, the device reboots automatically. Verify with:

```bash
lsusb
# Expected: 1915:7777 Nordic Semiconductor ASA Bitcraze Crazyradio (PA) dongle
```

### USB Permissions (udev Rules)

Create the udev rules file to allow non-root access:

```bash
sudo nano /etc/udev/rules.d/99-bitcraze.rules
```

Add the following lines:

```
SUBSYSTEM=="usb", ATTRS{idVendor}=="1915", ATTRS{idProduct}=="7777", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="35f0", ATTRS{idProduct}=="bad2", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="5740", MODE="0666"
```

Reload rules:

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Verify Driver

```bash
python3 - <<EOF
import cflib.crtp
cflib.crtp.init_drivers()
print(cflib.crtp.get_interfaces_status())
EOF
```

Expected output:
```
{'radio': 'Crazyradio version 2.04', ...}
```

---

## Manual Flight Setup (Xbox Controller)

### Install Python Packages

```bash
python3 -m venv venv
source venv/bin/activate
pip install cfclient cflib pygame
```

### Launch CFClient

```bash
cfclient
```

### Xbox Controller Mapping

| Joystick Input | Drone Control |
|----------------|---------------|
| Left Stick Up/Down | Thrust |
| Left Stick Left/Right | Yaw |
| Right Stick Up/Down | Pitch |
| Right Stick Left/Right | Roll |

> **Note:** Use the **PlayStation Mode 3** input profile in CFClient for the most stable axis calibration with Xbox controllers. Default Xbox profiles may exhibit a ~30° Roll offset at rest.

### Verify Joystick

```bash
jstest /dev/input/js0
```

---

## ROS 2 Launch & Control

### Launch the Crazyflie Server

```bash
source ~/cf_ws/install/setup.bash
ros2 launch crazyflie launch.py
```

This starts:
- Crazyflie Server
- Motion Capture Node
- Teleoperation Node
- Joystick Node

### Verify Active Services

```bash
ros2 service list | grep cf231
```

Expected services:
- `/cf231/takeoff`
- `/cf231/land`
- `/cf231/emergency`
- `/cf231/goto`

### Takeoff Command

```bash
ros2 service call /cf231/takeoff crazyflie_interfaces/srv/Takeoff \
  "{group_mask: 0, height: 0.2, duration: {sec: 2, nanosec: 0}}"
```

> **Note on Kalman Filter Warning:** The message `ESTKALMAN: State out of bounds, resetting` is expected when no external localization (Flow Deck, Motion Capture, or Lighthouse) is configured. This can be safely ignored for basic connection tests.

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Crazyradio mounts as USB drive | Device in UF2 bootloader mode | Flash official firmware (`.uf2` file) |
| `Cannot find Crazyradio` | Missing udev rules / permissions | Create `/etc/udev/rules.d/99-bitcraze.rules` |
| `Scan returns []` | Crazyflie not powered on | Power on the drone before scanning |
| Xbox Roll offset at rest | Default profile miscalibrated | Switch to PlayStation Mode 3 profile |
| `ESTKALMAN` warning | No localization system configured | Safely ignorable for basic tests |

---

## Key Lessons

1. If Crazyradio mounts as a USB storage device named `Crazyradio2`, it is in bootloader mode — flash the firmware.
2. Linux USB detection does not guarantee application firmware is running — always verify via `lsusb` (expected PID: `7777`).
3. Always source the ROS 2 workspace (`source install/setup.bash`) before running any ROS 2 commands.
4. Verify ROS 2 services are active before writing any control code.
5. Keep the launch terminal running during all drone operations.

---

## License

This project is for academic and research purposes.
