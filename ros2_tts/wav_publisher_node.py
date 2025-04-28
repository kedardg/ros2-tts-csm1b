#!/usr/bin/env python3
"""
ROS2 node: read a .wav file, convert to uint8 list and publish on a topic
"""
import wave
import pathlib

import rclpy
from rclpy.node import Node
from std_msgs.msg import UInt8MultiArray

class WavToUint8Node(Node):
    def __init__(self):
        super().__init__('wav_to_uint8_node')

        # Parameters
        self.declare_parameter('wav_file', '/ros2_ws/test_output/test_audio.wav')
        self.declare_parameter('topic', 'wav_bytes')
        self.declare_parameter('publish_rate', 0.2)  # Hz

        wav_path_str = self.get_parameter('wav_file').get_parameter_value().string_value
        topic = self.get_parameter('topic').get_parameter_value().string_value
        rate_hz = self.get_parameter('publish_rate').get_parameter_value().double_value

        self.wav_path = pathlib.Path(wav_path_str)
        if not self.wav_path.is_file():
            self.get_logger().error(f"WAV file not found: {wav_path_str}")
            rclpy.shutdown()
            return

        # Read .wav file fully
        wf = wave.open(str(self.wav_path), 'rb')
        total_frames = wf.getnframes()
        raw_bytes = wf.readframes(total_frames)
        wf.close()

        # Convert to uint8 list
        self.data_uint8 = list(raw_bytes)
        self.get_logger().info(f"Loaded {len(self.data_uint8)} bytes from {self.wav_path.name}")

        # Publisher
        self.publisher_ = self.create_publisher(
            UInt8MultiArray,
            topic,
            10
        )

        # Timer to publish at fixed rate
        timer_period = 1.0 / rate_hz if rate_hz > 0 else 1.0
        self.timer = self.create_timer(timer_period, self.publish_callback)

    def publish_callback(self):
        msg = UInt8MultiArray(data=self.data_uint8)
        self.publisher_.publish(msg)
        self.get_logger().info(f"Published UInt8Array of length {len(self.data_uint8)}")

def main(args=None):
    rclpy.init(args=args)
    node = WavToUint8Node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main() 