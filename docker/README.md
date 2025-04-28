# Docker Deployment for ROS2 TTS Node

This directory contains Docker configuration files to easily deploy the ROS2 Text-to-Speech node.

## Prerequisites

* Docker
* Docker Compose
* Git
* HuggingFace account and API token (for accessing the CSM model)

## Quick Start

1. Clone the repository:
```bash
git clone <repository_url>
cd ros2_tts
```

2. Set up your HuggingFace token:
```bash
export HUGGINGFACE_TOKEN="your_token_here"
```

3. Configure watermarking (optional):
Edit `settings.yaml` to customize watermarking:
```yaml
watermark:
  enabled: true  # set to false to disable watermarking
  key: [212, 211, 146, 56, 201]  # Default CSM watermark key, change for production use
```

4. Build and start the Docker container:
```bash
cd docker
docker-compose build
docker-compose up
```

## Docker Architecture

The Docker setup includes:

### Build-time Setup (during `docker-compose build`)
* Installation of system dependencies
* Installation of Python dependencies (including silentcipher for watermarking)
* ROS2 package building
* Creation of necessary directories

### Runtime (during `docker-compose up`)
* ROS2 environments are sourced
* TTS node is started with watermarking enabled
* Test node runs automated tests

## Testing

The container runs both the TTS node and a test node by default. The test node will:
* Send sample text messages
* Receive generated audio (with watermark if enabled)
* Save WAV files to the test_output directory
* Log success/failure for each test
* Verify watermarks in generated audio (if enabled)

Test output files will be available in the `test_output` directory.

## Development Workflow

1. Make changes to your code locally
2. Rebuild the Docker image:
```bash
docker-compose build
```

3. Start the container:
```bash
docker-compose up
```

For interactive development:
```bash
# Start container with bash
docker-compose run --rm ros2_tts bash

# In the container:
source /opt/ros/humble/setup.bash
source /ros2_ws/install/setup.bash
ros2 run ros2_tts tts_node  # or any other command
```

## Watermarking Configuration

The TTS node includes audio watermarking to identify AI-generated content:

* **Enable/Disable**: Set `watermark.enabled` in settings.yaml
* **Custom Key**: Change `watermark.key` in settings.yaml (recommended for production)
* **Default Key**: If no key is specified, uses CSM's default key
* **Verification**: Use `check_audio_from_file` in watermarking.py to verify watermarks

Note: The default watermark key is public. For production use, configure your own private key.

## Troubleshooting

### Audio Issues
If you have audio problems:
* Ensure the host audio device is properly mounted
* Check the audio device permissions
* Verify the ALSA configuration
* Check if watermarking is affecting audio quality (adjust message_sdr if needed)

### Model Loading Issues
* Verify your HuggingFace token is correctly set
* Check internet connectivity for model downloading
* Ensure sufficient disk space for model storage
* Verify silentcipher installation for watermarking

### Build Issues
If you encounter build errors:
* Clear Docker build cache: `docker-compose build --no-cache`
* Update system packages: `apt-get update` in Dockerfile
* Check Python package versions in requirements 

# ROS2 Text-to-Speech Node

A ROS2 package that provides text-to-speech capabilities using the CSM (Conversational Speech Model) from Sesame. This node allows you to convert text messages into natural-sounding speech audio.

## Features

- Text-to-speech conversion using state-of-the-art CSM model
- Configurable speaker identity and voice characteristics
- Streaming audio output
- Support for speaker prompting/voice cloning
- Easy integration with other ROS2 nodes
- Flexible device support (CUDA/MPS/CPU)
- Audio watermarking for AI-generated content identification
- Configurable watermark keys for content traceability
- Network-accessible ROS2 topics for distributed systems

## Verified Hardware Configuration

This package has been tested and verified on the following hardware:
- GPU: NVIDIA RTX 3080 (Laptop) with 16GB VRAM
- CUDA Version: Compatible with CUDA 12.7
- Driver Version: 566.14
- Memory Usage: ~9GB VRAM during operation
- Memory Requirements: Minimum 16GB system RAM recommended

Note: While the package can run on less powerful hardware or CPU-only configurations, performance and latency may vary.

## Topics

### Input Topic: /text_to_speech
- Message Type: std_msgs/String
- Format: Plain text to be converted to speech
- Example:
  ```bash
  ros2 topic pub /text_to_speech std_msgs/String "data: 'Hello, world!'"
  ```

### Output Topic: /audio_output
- Message Type: std_msgs/msg/UInt8MultiArray
- Format: WAV file data as raw bytes
- Structure:
  1. RIFF header (4 bytes)
  2. WAV format marker (4 bytes)
  3. "fmt " chunk (4 bytes)
  4. Audio format data (sample rate, bit depth)
  5. "data" chunk followed by audio samples
- Sample Rate: 24000 Hz (default)
- Bit Depth: 16-bit
- Channels: Mono
- Includes watermark if enabled in settings

## Prerequisites

- ROS2 Humble or later
- Python 3.10 or later
- CUDA-compatible GPU (optional, will fall back to CPU if not available)
- ffmpeg (for some audio operations)
- silentcipher (for audio watermarking)

## Installation

1. Clone this repository into your ROS2 workspace's src directory:
```bash
cd ~/ros2_ws/src
git clone <repository_url>
```

2. Install the required dependencies:
```bash
# Install ROS2 dependencies
rosdep install --from-paths src --ignore-src -r -y

# Install Python dependencies
cd ros2_tts
pip install -r requirements.txt
```

3. Build the package:
```bash
cd ~/ros2_ws
colcon build --packages-select ros2_tts
```

4. Source the workspace:
```bash
source ~/ros2_ws/install/setup.bash
```

## Network Configuration and External Access

The TTS node can be accessed from external containers or machines on the network. Here's how to configure and use it:

### Docker Network Configuration

The docker-compose.yml includes network settings for external access:
```yaml
services:
  ros2_tts:
    network_mode: "host"  # Allows direct access to host network
    environment:
      - ROS_DOMAIN_ID=0  # Change to isolate ROS2 networks
      - RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

### Accessing from Another Container

To subscribe from another container:
```yaml
services:
  your_service:
    network_mode: "host"
    environment:
      - ROS_DOMAIN_ID=0  # Must match TTS node's domain ID
      - RMW_IMPLEMENTATION=rmw_fastrtps_cpp
```

### Accessing from Another Machine

1. Ensure both machines are on the same network
2. Set identical ROS_DOMAIN_ID on both machines
3. Allow UDP traffic on ports 7400-7500 (default DDS ports)
4. Configure SROS2 for secure communication (recommended for production)

## Docker Support

You can run the ROS2 TTS node using Docker, which supports both GPU and CPU configurations. 

## Example Code

Here are various examples of how to interact with the TTS node:

### Basic Subscriber with Audio Playback
```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_msgs.msg import UInt8MultiArray
import sounddevice as sd
import numpy as np
import wave
import io

class TTSAudioPlayer(Node):
    def __init__(self):
        super().__init__('tts_audio_player')
        self.subscription = self.create_subscription(
            UInt8MultiArray,
            'audio_output',
            self.audio_callback,
            10)
        
    def audio_callback(self, msg):
        # Convert uint8 array directly to bytes
        audio_data = bytes(msg.data)
        
        # Read WAV data using wave
        with io.BytesIO(audio_data) as wav_buffer:
            with wave.open(wav_buffer, 'rb') as wav_file:
                # Get audio parameters
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                # Read audio data
                audio_data = wav_file.readframes(wav_file.getnframes())
                
        # Convert to numpy array for playback
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        
        # Play audio
        sd.play(audio_array, framerate)
        sd.wait()  # Wait until audio finishes playing

def main():
    rclpy.init()
    player = TTSAudioPlayer()
    rclpy.spin(player)
    player.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### Save Audio to File
```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8MultiArray
import os
from datetime import datetime

class TTSAudioSaver(Node):
    def __init__(self):
        super().__init__('tts_audio_saver')
        self.subscription = self.create_subscription(
            UInt8MultiArray,
            'audio_output',
            self.audio_callback,
            10)
        self.output_dir = 'tts_output'
        os.makedirs(self.output_dir, exist_ok=True)
        
    def audio_callback(self, msg):
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(self.output_dir, f'tts_{timestamp}.wav')
        
        # Write bytes directly from UInt8MultiArray
        with open(filename, 'wb') as f:
            f.write(bytes(msg.data))
        
        self.get_logger().info(f'Saved audio to: {filename}')
```

### Interactive TTS Client
```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8MultiArray
import threading
import queue
import wave
import io

class InteractiveTTSClient(Node):
    def __init__(self):
        super().__init__('interactive_tts_client')
        self.publisher = self.create_publisher(String, 'text_to_speech', 10)
        self.subscription = self.create_subscription(
            UInt8MultiArray,
            'audio_output',
            self.audio_callback,
            10)
        self.input_queue = queue.Queue()
        
        # Start input thread
        self.input_thread = threading.Thread(target=self.input_loop)
        self.input_thread.daemon = True
        self.input_thread.start()
        
        # Create timer for processing input
        self.timer = self.create_timer(0.1, self.timer_callback)
        
    def input_loop(self):
        print("Enter text to convert to speech (Ctrl+C to exit):")
        while True:
            try:
                text = input("> ")
                self.input_queue.put(text)
            except (KeyboardInterrupt, EOFError):
                break
    
    def timer_callback(self):
        try:
            # Check for new input
            text = self.input_queue.get_nowait()
            if text:
                msg = String()
                msg.data = text
                self.publisher.publish(msg)
                self.get_logger().info(f'Published: "{text}"')
        except queue.Empty:
            pass
            
    def audio_callback(self, msg):
        # Get WAV info from the received data
        audio_data = bytes(msg.data)
        with io.BytesIO(audio_data) as wav_buffer:
            with wave.open(wav_buffer, 'rb') as wav_file:
                duration = wav_file.getnframes() / wav_file.getframerate()
                
        self.get_logger().info(f'Received audio data: {len(msg.data)} bytes, duration: {duration:.2f}s')
```

### Network Client (External Machine)
```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8MultiArray
import os

class NetworkTTSClient(Node):
    def __init__(self):
        super().__init__('network_tts_client')
        # Configure ROS_DOMAIN_ID to match the TTS node
        os.environ['ROS_DOMAIN_ID'] = '0'  # Must match TTS node
        
        self.publisher = self.create_publisher(String, 'text_to_speech', 10)
        self.subscription = self.create_subscription(
            UInt8MultiArray,
            'audio_output',
            self.audio_callback,
            10)
    
    def send_text(self, text):
        msg = String()
        msg.data = text
        self.publisher.publish(msg)
        self.get_logger().info(f'Published: "{text}"')
    
    def audio_callback(self, msg):
        # Process raw WAV data from UInt8MultiArray
        audio_data = bytes(msg.data)
        with io.BytesIO(audio_data) as wav_buffer:
            with wave.open(wav_buffer, 'rb') as wav_file:
                duration = wav_file.getnframes() / wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                
        self.get_logger().info(
            f'Received audio: {len(msg.data)} bytes, '
            f'{duration:.2f}s, {channels} ch, '
            f'{sample_width*8}bit, {framerate}Hz'
        )
```

Each example demonstrates different aspects of working with the TTS node:
- Real-time audio playback
- Saving audio files
- Interactive text input
- Batch processing with audio feedback
- Network communication

Requirements for examples:
```bash
pip install sounddevice numpy  # For audio playback example
``` 