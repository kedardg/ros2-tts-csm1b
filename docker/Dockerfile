FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
# Disable lazy compilation in CSM
ENV NO_TORCH_COMPILE=1

# SYSTEM - Include all dependencies mentioned in the README
RUN apt-get update --yes --quiet && DEBIAN_FRONTEND=noninteractive apt-get install --yes --quiet --no-install-recommends \
    software-properties-common \
    build-essential apt-utils \
    wget curl vim git ca-certificates kmod \
    bc ffmpeg libsm6 libxext6 \
    # Required by README for Debian-based systems
    libgl1 libglib2.0-0 \
    # For better performance with TCMalloc
    libtcmalloc-minimal4 \
    # Audio processing dependencies
    libsndfile1 \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    libasound-dev \
    # Additional dependencies for ROS2
    gnupg \
    lsb-release \
    # Build dependencies
    python3-dev \
    python3-pip \
    python3-venv \
    python3-wheel \
    build-essential \
    gcc \
    g++ \
 && rm -rf /var/lib/apt/lists/*

# PYTHON 3.10
RUN add-apt-repository --yes ppa:deadsnakes/ppa && apt-get update --yes --quiet
RUN DEBIAN_FRONTEND=noninteractive apt-get install --yes --quiet --no-install-recommends \
    python3.10 \
    python3.10-dev \
    python3.10-distutils \
    python3.10-lib2to3 \
    python3.10-gdbm \
    python3.10-tk \
    python3.10-venv \
    pip \
 && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 999 \
    && update-alternatives --config python3 && ln -s /usr/bin/python3 /usr/bin/python

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build tools in virtual environment
RUN pip install --no-cache-dir --upgrade pip setuptools wheel build

# Setup ROS2 repositories
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Install ROS2 packages
RUN apt-get update && apt-get install -y \
    ros-humble-ros-base \
    ros-humble-rclpy \
    python3-colcon-common-extensions \
    python3-rosdep \
    && rm -rf /var/lib/apt/lists/*

# Set up CUDA environment variables
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,video

# Create workspace directory and copy the package
RUN mkdir -p /ros2_ws/src/ros2_tts
COPY . /ros2_ws/src/ros2_tts/

# Create resource directory and file
RUN mkdir -p /ros2_ws/src/ros2_tts/resource && \
    touch /ros2_ws/src/ros2_tts/resource/ros2_tts

# Initialize rosdep and install dependencies
WORKDIR /ros2_ws
RUN rosdep init || true && rosdep update
RUN rosdep install --from-paths src --ignore-src -r -y

# Install Python dependencies from setup.py
WORKDIR /ros2_ws/src/ros2_tts
RUN pip install --no-cache-dir -e .

# Build the ROS2 package
WORKDIR /ros2_ws
RUN . /opt/ros/humble/setup.sh && \
    colcon build --packages-select ros2_tts --symlink-install

# Create test output directory
RUN mkdir -p /ros2_ws/test_output && chmod 777 /ros2_ws/test_output

# Set up the entrypoint
COPY ./docker/docker-entrypoint.sh /
RUN chmod +x /docker-entrypoint.sh

# Set working directory back to workspace root
WORKDIR /ros2_ws

# Set the entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"] 