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

## Docker Support

You can run the ROS2 TTS node using Docker, which supports both GPU and CPU configurations.

### Prerequisites for Docker

- Docker Engine 19.03 or later
- Docker Compose V2
- NVIDIA Container Toolkit (for GPU support)
- NVIDIA drivers (for GPU support)

### Running with Docker

The Docker configuration supports both GPU and CPU modes. By default, it runs in GPU mode.

1. Build and run with GPU support (default):
```bash
docker compose up
```

2. Run in CPU-only mode:
```bash
USE_CUDA=0 docker compose up
```

You can also control which GPUs are visible to the container using the `NVIDIA_VISIBLE_DEVICES` environment variable:
```bash
NVIDIA_VISIBLE_DEVICES=0,1 docker compose up  # Use specific GPUs
NVIDIA_VISIBLE_DEVICES=none docker compose up  # Force CPU mode
```

### Docker Environment Variables

- `USE_CUDA`: Set to 1 for GPU support (default) or 0 for CPU-only mode
- `NVIDIA_VISIBLE_DEVICES`: Control which GPUs are available to the container
  - `all`: Use all GPUs (default)
  - `none`: Force CPU mode
  - `0,1,2`: Specify GPU indices to use

## Configuration

The node uses a `settings.yaml` file for configuration. Create this file in your preferred config directory with the following structure:

```yaml
model:
  device: "cuda"  # Options: "cuda", "mps", "cpu" (user-specified device takes priority)
  repo_id: "sesame/csm_1b"
  use_speaker_prompt: false

paths:
  output_dir: "/path/to/output"
  prompt_dir: "/path/to/prompts"  # Optional

audio:
  sample_rate: 24000
  max_audio_length_ms: 10000

speaker_prompt:  # Optional, only if use_speaker_prompt is true
  text: "Example prompt text"
  audio_path: "path/to/prompt.wav"
  speaker_id: 0

watermark:  # Optional watermarking configuration
  enabled: true  # Set to false to disable watermarking
  key: [212, 211, 146, 56, 201]  # Optional, will use default key if not specified
```

### Device Selection

The node respects the device specified in your settings.yaml. If the specified device is not available, it will fall back to an available device in this order:
1. User-specified device (if available)
2. MPS (Apple Silicon)
3. CUDA
4. CPU

You can check your available devices with:
```python
python3 -c "import torch; print('MPS available:', torch.backends.mps.is_available()); print('CUDA available:', torch.cuda.is_available())"
```

The node will log the actual device being used when it starts.

### Watermarking Configuration

The TTS node includes audio watermarking to identify AI-generated content:

1. **Enable/Disable Watermarking**:
   ```yaml
   watermark:
     enabled: true  # Set to false to disable watermarking
   ```

2. **Custom Watermark Key**:
   ```yaml
   watermark:
     enabled: true
     key: [1, 2, 3, 4, 5]  # Your custom 5-integer key
   ```

3. **Default Key**: If no key is specified, uses CSM's default key
4. **Verification**: Use the provided CLI tool to verify watermarks:
   ```bash
   python3 -m ros2_tts.csm.watermarking --audio_path path/to/audio.wav
   ```

Note: The default watermark key is public. For production use, configure your own private key.

## Usage

### Running the Node

Start the TTS node:
```bash
ros2 run ros2_tts tts_node
```

You can control the logging verbosity using:
```bash
ros2 run ros2_tts tts_node --ros-args --log-level LEVEL
```
Available levels (from most to least verbose):
- debug: Detailed debugging information
- info: General information (default)
- warn: Warning messages
- error: Error messages
- fatal: Critical errors that cause the node to terminate

### Basic Usage

1. Publish text to convert to speech:
```bash
ros2 topic pub /text_to_speech std_msgs/String "data: 'Hello, this is a test.'"
```

2. Listen to the generated audio:
```bash
ros2 topic echo /audio_output
```

### Topics

- **Subscribed Topics:**
  - `/text_to_speech` (std_msgs/String)
    - Input text to be converted to speech

- **Published Topics:**
  - `/audio_output` (std_msgs/String)
    - Binary audio data in WAV format, encoded as a hex string
    - Includes watermark if enabled in settings

## Integration Examples

### Python Integration

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class TTSClient(Node):
    def __init__(self):
        super().__init__('tts_client')
        self.publisher = self.create_publisher(String, 'text_to_speech', 10)
        
    def speak(self, text):
        msg = String()
        msg.data = text
        self.publisher.publish(msg)

def main():
    rclpy.init()
    client = TTSClient()
    client.speak("Hello, world!")
    rclpy.spin_once(client)
    client.destroy_node()
    rclpy.shutdown()
```

### Launch File Integration

Create a launch file (`launch/tts_launch.py`):

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ros2_tts',
            executable='tts_node',
            name='tts_node',
            parameters=[{
                'settings_path': 'path/to/settings.yaml'
            }]
        )
    ])
```

## Troubleshooting

1. **CUDA Issues**
   - Ensure CUDA is properly installed
   - Check if PyTorch can see your GPU: `python -c "import torch; print(torch.cuda.is_available())"`

2. **Audio Output Issues**
   - Verify audio device permissions
   - Check if the output directory is writable
   - Verify watermarking is not affecting audio quality (adjust message_sdr if needed)

3. **Model Loading Issues**
   - Ensure you have access to the CSM model
   - Check your internet connection for model downloading
   - Verify silentcipher installation for watermarking

4. **Watermarking Issues**
   - Check if silentcipher is properly installed
   - Verify watermark settings in settings.yaml
   - Use the verification tool to check watermarks
   - Try adjusting message_sdr for better audio quality

## License

This package is licensed under the Apache License 2.0. See the LICENSE file for details.

## Acknowledgments

This package uses:
- CSM (Conversational Speech Model) from Sesame. For more information, visit [Sesame's CSM repository](https://github.com/SesameAILabs/csm)
- SilentCipher for audio watermarking. For more information, visit [Sony's SilentCipher repository](https://github.com/sony/silentcipher) 