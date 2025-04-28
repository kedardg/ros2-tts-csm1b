#!/bin/bash
set -e

# First activate virtual environment
source /opt/venv/bin/activate

# Then source ROS2 environment
source /opt/ros/humble/setup.bash

# Finally source our workspace setup if it exists
if [ -f "/ros2_ws/install/setup.bash" ]; then
    source /ros2_ws/install/setup.bash
fi

# Make sure PYTHONPATH includes our workspace's Python packages
if [ -d "/ros2_ws/install/lib/python3.10/site-packages" ]; then
    export PYTHONPATH="/ros2_ws/install/lib/python3.10/site-packages:${PYTHONPATH}"
fi

# Make sure our virtual environment's Python packages are in PYTHONPATH
export PYTHONPATH="/opt/venv/lib/python3.10/site-packages:${PYTHONPATH}"

# Debug information
echo "Current PYTHONPATH: ${PYTHONPATH}"
echo "Available ROS2 packages:"
ros2 pkg list
echo "Looking for ros2_tts package:"
ros2 pkg prefix ros2_tts || echo "ros2_tts package not found"
echo "Contents of /ros2_ws/install:"
ls -R /ros2_ws/install

# Execute the command passed to docker run
exec "$@" 