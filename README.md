# ESP32 WASD Teleop with micro-ROS(UDP)


![WhatsApp Image 2025-04-14 at 20 48 59](https://github.com/user-attachments/assets/06d42721-9948-4062-941d-e0b52f7be772)


This project demonstrates a simple teleoperation system using an ESP32 running micro-ROS and ROS 2 Humble on a host machine.

- Press WASD/Space on the host to send integer commands (1-4, 0) to the ESP32 via `/wasd_command`.
- The ESP32 receives the command and periodically publishes its current status integer back to the host via `/wasd_status`.
- A host node displays the textual meaning of the received status.

## Structure

- `esp32_firmware/string_teleop/`: Contains the ESP-IDF project for the ESP32 micro-ROS node.
- `ros2_host_pkgs/`: Contains the ROS 2 Humble packages for the host system.
  - `esp32_wasd_host`: Publishes keyboard commands.
  - `wasd_status_display`: Subscribes to ESP32 status and displays text.

## Requirements

- Host: Ubuntu 22.04, ROS 2 Humble, Docker
- ESP32: ESP32 board, ESP-IDF micro-ROS build environment (Docker recommended)
- WiFi Network

## Setup & Running

**ESP32 Firmware:**
1. Use the `microros/esp-idf-microros:humble` Docker image.
2. Mount this repository's root into the container (e.g., `-v $(pwd):/project`).
3. `cd /project/esp32_firmware/string_teleop`
4. `idf.py set-target esp32`
5. `idf.py menuconfig` (Configure WiFi SSID/Password, Agent IP)
6. `idf.py build`
7. `idf.py -p /dev/ttyUSB0 flash monitor`

**Host ROS 2 Packages:**
1. Create a ROS 2 workspace (e.g., `mkdir -p ~/wasd_ws/src`).
2. Copy the contents of `ros2_host_pkgs/*` from this repo into `~/wasd_ws/src/`.
3. `cd ~/wasd_ws`
4. `colcon build`
5. `source install/setup.bash`

**Running the System:**
1. Terminal 1 (Agent): `docker run -it --rm --net=host microros/micro-ros-agent:humble udp4 --port 8888`
2. Terminal 2 (Status Display): `source ~/wasd_ws/install/setup.bash && ros2 run esp32_status_display status_display`
3. Terminal 3 (Keyboard Input): `source ~/wasd_ws/install/setup.bash && ros2 run esp32_wasd_host wasd_teleop`
4. Press WASD/Space in Terminal 4.
