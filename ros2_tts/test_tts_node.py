#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8MultiArray
import wave
import numpy as np
import pathlib
import time
from datetime import datetime

class TTSTestNode(Node):
    def __init__(self):
        super().__init__('tts_test_node')
        
        # Create publishers and subscribers
        self.text_publisher = self.create_publisher(
            String,
            'text_to_speech',
            10
        )
        
        self.audio_subscription = self.create_subscription(
            UInt8MultiArray,
            'audio_output',
            self.audio_callback,
            10
        )
        
        # Create output directory
        self.output_dir = pathlib.Path('test_output')
        self.output_dir.mkdir(exist_ok=True)
        
        self.received_audio = False
        self.get_logger().info('TTS Test Node initialized')
        
        # Start test after a short delay
        self.create_timer(2.0, self.run_test)
    
    def audio_callback(self, msg):
        """Handle received audio data"""
        try:
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"test_audio_{timestamp}.wav"
            
            # Write received WAV data directly (includes header)
            with open(str(output_path), 'wb') as f:
                f.write(bytes(msg.data))
            
            # Verify and log WAV properties
            with wave.open(str(output_path), 'rb') as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                self.get_logger().info(
                    f'Saved WAV file: {channels} channels, '
                    f'{sample_width} bytes/sample, {framerate} Hz, '
                    f'{n_frames} frames'
                )
            
            self.received_audio = True
            
        except Exception as e:
            self.get_logger().error(f'Error saving audio: {str(e)}')
    
    def run_test(self):
        """Run a series of tests"""
        test_texts = [
            "Hello, this is a test message.",
            "Testing audio synthesis with a longer sentence to verify continuous speech.",
            "Testing, 1 2 3!",
            "The quick brown fox jumps over the lazy dog."
        ]
        
        for i, text in enumerate(test_texts):
            self.get_logger().info(f'Running test {i+1}/{len(test_texts)}')
            
            # Reset flag
            self.received_audio = False
            
            # Publish test text
            msg = String()
            msg.data = text
            self.text_publisher.publish(msg)
            self.get_logger().info(f'Published text: "{text}"')
            
            # Wait for audio response with timeout
            timeout = 10.0  # seconds
            start_time = time.time()
            
            while not self.received_audio and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if not self.received_audio:
                self.get_logger().error(f'Test {i+1} failed: No audio received within {timeout} seconds')
            else:
                self.get_logger().info(f'Test {i+1} completed successfully')
            
            # Wait between tests
            time.sleep(2.0)
        
        self.get_logger().info('All tests completed')
        rclpy.shutdown()

def main(args=None):
    rclpy.init(args=args)
    
    test_node = TTSTestNode()
    
    try:
        rclpy.spin(test_node)
    except KeyboardInterrupt:
        pass
    finally:
        test_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main() 