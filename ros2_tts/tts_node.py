#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, UInt8MultiArray
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import numpy as np
from ros2_tts.csm.text_to_speech import TextToSpeechGenerator
import io
import wave
import struct
import os
from ament_index_python.packages import get_package_share_directory

class TTSNode(Node):
    def __init__(self):
        super().__init__('tts_node')
        
        # Create QoS profile for better audio streaming
        qos_profile = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # Get the settings file path
        try:
            package_share_dir = get_package_share_directory('ros2_tts')
            settings_path = os.path.join(package_share_dir, 'config', 'settings.yaml')
            if not os.path.exists(settings_path):
                settings_path = 'settings.yaml'  # Fallback to local directory
            self.get_logger().info(f'Using settings file: {settings_path}')
        except Exception as e:
            self.get_logger().warning(f'Could not find package share directory: {str(e)}')
            settings_path = 'settings.yaml'  # Fallback to local directory
        
        # Initialize TTS Generator
        self.get_logger().info('Initializing TTS Generator...')
        self.tts_generator = TextToSpeechGenerator(settings_path)
        
        # Create subscribers and publishers
        self.text_subscription = self.create_subscription(
            String,
            'text_to_speech',
            self.text_callback,
            qos_profile
        )
        
        self.audio_publisher = self.create_publisher(
            UInt8MultiArray,
            'audio_output',
            qos_profile
        )
        
        # Store audio parameters
        self.sample_rate = self.tts_generator.generator.sample_rate
        self.channels = 1  # mono
        self.sample_width = 2  # 16-bit
        
        self.get_logger().info(f'TTS Node initialized with sample_rate={self.sample_rate}, channels={self.channels}')

    def normalize_audio(self, audio_np: np.ndarray) -> np.ndarray:
        """Normalize audio to prevent clipping."""
        try:
            # Ensure audio is in float32 format
            audio_np = audio_np.astype(np.float32)
            
            # Normalize if audio exceeds [-1, 1] range
            max_val = np.abs(audio_np).max()
            if max_val > 1.0:
                audio_np = audio_np / max_val
                self.get_logger().debug(f'Audio normalized by factor {max_val}')
            
            return audio_np
            
        except Exception as e:
            self.get_logger().warning(f'Audio normalization failed: {str(e)}')
            return audio_np

    def text_callback(self, msg):
        """Handle incoming text messages."""
        try:
            self.get_logger().info(f'Received text: "{msg.data}"')
            
            if not msg.data.strip():
                self.get_logger().warning('Received empty text, skipping synthesis')
                return
            
            # Generate speech directly as audio tensor (includes watermarking)
            audio_tensor = self.tts_generator.generator.generate(
                text=msg.data,
                speaker=0,  # default speaker
                context=[],
                max_audio_length_ms=self.tts_generator.settings['audio']['max_audio_length_ms']
            )
            
            if audio_tensor is None or audio_tensor.size == 0:
                self.get_logger().error('Generated audio tensor is empty')
                return
            
            # Convert audio tensor to numpy array and normalize
            audio_np = audio_tensor.cpu().numpy()
            audio_np = self.normalize_audio(audio_np)
            
            # Create WAV data in memory with header
            try:
                with io.BytesIO() as wav_buffer:
                    with wave.open(wav_buffer, 'wb') as wav_file:
                        wav_file.setnchannels(self.channels)
                        wav_file.setsampwidth(self.sample_width)
                        wav_file.setframerate(self.sample_rate)
                        
                        # Convert float32 to int16 with clipping protection
                        audio_int16 = np.clip(audio_np * 32767, -32768, 32767).astype(np.int16)
                        wav_file.writeframes(audio_int16.tobytes())
                    
                    # Get the complete WAV data including header
                    wav_data = wav_buffer.getvalue()
                
                if len(wav_data) == 0:
                    self.get_logger().error('Generated WAV data is empty')
                    return
                
                # Create and publish UInt8MultiArray message with complete WAV data
                audio_msg = UInt8MultiArray()
                audio_msg.data = list(wav_data)  # Convert bytes to list of uint8
                self.audio_publisher.publish(audio_msg)
                self.get_logger().info(f'Published WAV data with header: {len(wav_data)} bytes')
                
            except (IOError, wave.Error) as e:
                self.get_logger().error(f'Error creating WAV data: {str(e)}')
            
        except Exception as e:
            self.get_logger().error(f'Error processing text: {str(e)}')

def main(args=None):
    rclpy.init(args=args)
    
    tts_node = TTSNode()
    
    try:
        rclpy.spin(tts_node)
    except KeyboardInterrupt:
        pass
    finally:
        tts_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main() 